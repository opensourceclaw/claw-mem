# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Proactive compression: auto-trigger at 70% capacity to prevent context overflow.

Lightweight checker that runs after each store() call. Does NOT depend on CMS
enable_cms — it uses a simple len(working_memory) / max_working_memory ratio.

Architecture:
  store() succeeds
    -> ProactiveCompressionChecker.check_and_compress()
      -> utilization >= 0.7?
        -> YES: identify critical items, compress the rest, sink to semantic.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ── Patterns for critical content detection ──────────────────────

_CRITICAL_TAGS = {"important", "critical", "关键", "重要", "todo", "待办"}

_TODO_PATTERNS = [
    "- [ ]", "- [x]", "TODO", "todo", "待办", "要做",
    "需要实现", "需要完成", "需要做", "还需", "尚未",
]

_CONCLUSION_PATTERNS = [
    "结论", "决定", "确定", "最终方案", "总结", "总之",
    "conclusion", "decision", "decided", "agreed", "final",
    "we will", "plan is",
]


def _log(message: str):
    if not os.environ.get("CLAW_MEM_SILENT"):
        print(message)


# ── Configuration ───────────────────────────────────────────────

@dataclass
class ProactiveCompressionConfig:
    """Configuration for proactive compression checker."""

    enabled: bool = True
    proactive_threshold: float = 0.7       # trigger at 70% utilization
    warning_threshold: float = 0.8          # alert only (unchanged)
    compression_ratio: float = 0.5          # target ratio after compression
    min_memories_to_compress: int = 20      # don't trigger below this count
    cooldown_stores: int = 5               # skip N store() calls after a compress
    max_summary_length: int = 500           # max chars for the compressed summary
    max_working_memory: int = 100           # capacity ceiling for working_memory


# ── Proactive Compression Checker ────────────────────────────────

class ProactiveCompressionChecker:
    """Lightweight proactive compression checker.

    Called after every store(). When working_memory reaches proactive_threshold
    (default 70%), identifies critical items to keep in-place and compresses
    the rest into an archived semantic-memory entry.

    Does NOT depend on CMS (enable_cms can be False).
    """

    def __init__(self, memory_manager, config: ProactiveCompressionConfig = None):
        self._mm = memory_manager  # MemoryManager reference
        self._config = config or ProactiveCompressionConfig()
        self._store_count_since_last = 0
        self._last_compression_time: Optional[str] = None

    # ── public ──────────────────────────────────────────────────

    def check_and_compress(self) -> Optional[Dict[str, Any]]:
        """Post-store entry point. Return compression stats dict or None."""
        if not self._config.enabled:
            return None

        self._store_count_since_last += 1

        # Cooldown gate
        if self._store_count_since_last < self._config.cooldown_stores:
            return None

        wm = self._mm.working_memory
        total = len(wm)
        if total < self._config.min_memories_to_compress:
            return None

        utilization = total / max(self._config.max_working_memory, 1)
        if utilization < self._config.proactive_threshold:
            return None

        # ── trigger compression ──
        self._store_count_since_last = 0
        self._last_compression_time = datetime.now().isoformat()

        critical, compressible = self._identify_critical(wm)

        if not compressible:
            _log(f"⚠️  Proactive compression: all {total} items are critical, nothing to compress")
            return {"total": total, "critical": len(critical), "compressed": 0}

        summary = self._compress_to_summary(compressible)
        topics = self._extract_topics(compressible)

        # Keep critical items + a lightweight note
        note = {
            "id": f"comp_{total}",
            "content": f"[compression] {len(compressible)} items archived to semantic memory",
            "type": "episodic",
            "tags": ["compression"],
            "metadata": {"compressed_count": len(compressible), "time": self._last_compression_time},
            "timestamp": self._last_compression_time,
            "session_id": self._mm.session_id,
        }
        kept = critical + [note]
        self._mm.working_memory = kept

        # Sink AFTER replacing working_memory so the archived entry
        # is appended rather than overwritten.
        self._sink_to_semantic(summary, topics)

        _log(f"🔄 Proactive compression: {len(compressible)} items compressed → {len(critical)} critical kept "
             f"(utilization {utilization:.1%} → ~{len(kept) / max(self._config.max_working_memory, 1):.1%})")

        return {
            "total": total,
            "critical": len(critical),
            "compressed": len(compressible),
            "summary_len": len(summary),
            "utilization_before": utilization,
            "utilization_after": len(kept) / max(self._config.max_working_memory, 1),
        }

    # ── internal helpers ────────────────────────────────────────

    def _identify_critical(
        self, memories: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """Split working_memory into (critical, compressible) groups."""
        critical: List[Dict] = []
        compressible: List[Dict] = []

        # Always keep the most recent 5 memories
        recent_cutoff = max(0, len(memories) - 5)

        for i, m in enumerate(memories):
            if self._is_critical(m) or i >= recent_cutoff:
                critical.append(m)
            else:
                compressible.append(m)

        return critical, compressible

    def _is_critical(self, memory: Dict) -> bool:
        """Check whether a single memory entry is critical (should be kept)."""
        # 1. Critical tags
        tags = {t.lower() for t in (memory.get("tags") or [])}
        if tags & _CRITICAL_TAGS:
            return True

        # 2. Content pattern match: TODO or conclusion
        content = memory.get("content", "") or ""
        lower = content.lower()
        if any(p.lower() in lower for p in _TODO_PATTERNS):
            return True
        if any(p.lower() in lower for p in _CONCLUSION_PATTERNS):
            return True

        # 3. Metadata importance score
        meta = memory.get("metadata") or {}
        importance = meta.get("importance", 0)
        if isinstance(importance, (int, float)) and importance >= 0.7:
            return True

        return False

    def _compress_to_summary(self, compressible: List[Dict]) -> str:
        """Merge compressible memories into a single summary string."""
        if not compressible:
            return ""

        # Group by type
        by_type: Dict[str, List[str]] = {}
        for m in compressible:
            mt = m.get("type", "episodic")
            content = (m.get("content") or "").strip()
            if len(content) > 80:
                content = content[:77] + "..."
            by_type.setdefault(mt, []).append(content)

        lines = []
        for mt, items in by_type.items():
            sampled = items[:10]  # take at most 10 per type
            lines.append(f"[{mt}] {len(items)} items:")
            for item in sampled:
                lines.append(f"  - {item}")
            if len(items) > 10:
                lines.append(f"  ... and {len(items) - 10} more")

        summary = "\n".join(lines)
        if len(summary) > self._config.max_summary_length:
            summary = summary[: self._config.max_summary_length - 3] + "..."

        return summary

    def _extract_topics(self, compressible: List[Dict]) -> List[str]:
        """Extract topics from tags of compressible items."""
        topics: List[str] = []
        seen = set()
        for m in compressible:
            for tag in (m.get("tags") or []):
                if tag and tag not in seen:
                    seen.add(tag)
                    topics.append(tag)
        return topics[:10]

    def _sink_to_semantic(self, summary: str, topics: List[str]) -> None:
        """Archive the compressed summary to semantic memory (L2).

        Temporarily disables proactive compression on the manager to prevent
        re-entry when the archived entry's store() triggers another check.
        """
        saved = self._mm.enable_proactive_compression
        self._mm.enable_proactive_compression = False
        try:
            self._mm.store(
                content=f"[archived] {summary}",
                memory_type="semantic",
                tags=["archived", "compressed"] + topics,
                metadata={
                    "source": "proactive_compression",
                    "compressed_at": self._last_compression_time,
                    "compressed_session": self._mm.session_id,
                },
            )
        except Exception:
            # Best-effort: if the semantic store() itself fails we don't
            # want to crash the original store() call.
            _log("⚠️  Proactive compression: failed to sink to semantic memory")
        finally:
            self._mm.enable_proactive_compression = saved
