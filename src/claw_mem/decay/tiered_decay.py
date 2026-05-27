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

"""
TieredDecayEngine (F2 · v4.7.0)

Three-tier storage decay: HOT (current session), WARM (recently accessed),
COLD (long-term). Evicts based on composite score of recency, frequency,
and importance.
"""

import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..memory_manager import MemoryManager
    from ..llm_provider import LLMProvider
    from .functions import DecayConfig


_IMPORTANCE_PROMPT = (
    "Rate the importance of this memory on a scale of 0.0 to 1.0 "
    "(0=trivial, 0.5=useful, 0.8=very important, 1.0=critical). "
    "Return only the number.\n\nMemory: {content}"
)


class TierLevel(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


def _now_iso() -> str:
    return datetime.now().isoformat()


class TieredDecayEngine:
    """Three-tier storage decay engine for memory lifecycle management.

    Memories flow: HOT → WARM → COLD → EVICTED.
    Access promotes memories upward; time pushes them downward.
    Composite scoring decides eviction order.
    """

    def __init__(
        self,
        manager: "MemoryManager",
        config: "DecayConfig" = None,
        llm_provider: "LLMProvider" = None,
        hot_ttl: int = 3600,
        warm_ttl_days: int = 7,
        cold_ttl_days: int = 30,
        max_hot: int = 100,
        max_warm: int = 500,
        max_cold: int = 2000,
    ):
        self.manager = manager
        self.config = config
        self.llm_provider = llm_provider

        self.hot_ttl = hot_ttl          # seconds
        self.warm_ttl = warm_ttl_days * 86400
        self.cold_ttl = cold_ttl_days * 86400
        self.max_hot = max_hot
        self.max_warm = max_warm
        self.max_cold = max_cold

        # Track access timestamps for recency scoring
        self._access_log: Dict[str, List[float]] = {}
        self._importance_cache: Dict[str, float] = {}
        self._last_cycle: float = 0.0

    # ── classification ─────────────────────────────────────────────────

    def classify(self, memory: Dict[str, Any]) -> TierLevel:
        """Classify a single memory into a tier based on its age and metadata."""
        meta = memory.get("metadata", {})

        # Deprecated memories go directly to COLD for immediate eviction
        if meta.get("deprecated") in ("true", "True", "1"):
            return TierLevel.COLD

        # Use creation timestamp for age calculation
        created_at = memory.get("created_at") or memory.get("timestamp") or _now_iso()
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            created_dt = datetime.now()

        age_seconds = (datetime.now() - created_dt.replace(tzinfo=None)).total_seconds()

        if age_seconds <= self.hot_ttl:
            return TierLevel.HOT
        elif age_seconds <= self.warm_ttl:
            return TierLevel.WARM
        else:
            return TierLevel.COLD

    def promote(self, memory_id: str) -> Optional[TierLevel]:
        """Record an access, potentially promoting the memory tier.

        Promotion rules:
          COLD → WARM if recently accessed (resets TTL)
          WARM → HOT if accessed within hot TTL
          HOT stays HOT
        """
        if not memory_id:
            return None

        now = time.time()
        if memory_id not in self._access_log:
            self._access_log[memory_id] = []
        self._access_log[memory_id].append(now)

        # Look up current memory
        all_m = self.manager.semantic.get_all()
        mem = next((m for m in all_m if m.get("id") == memory_id), None)
        if mem is None:
            return None

        current = self.classify(mem)
        if current in (TierLevel.HOT, TierLevel.WARM):
            return current
        # COLD → WARM promotion: record access and return
        freq = self._access_frequency(memory_id)
        return TierLevel.WARM if freq >= 2 else TierLevel.COLD

    # ── importance scoring ─────────────────────────────────────────────

    def get_importance(self, memory: Dict[str, Any]) -> float:
        """Score memory importance (0.0–1.0).

        Uses cached LLM score or rule-based fallback.
        """
        mid = memory.get("id", "")
        if mid and mid in self._importance_cache:
            return self._importance_cache[mid]

        # Try LLM scoring
        if self.llm_provider:
            try:
                content = memory.get("content", "")
                score_text = self.llm_provider.generate(
                    _IMPORTANCE_PROMPT.format(content=content),
                    max_tokens=16,
                )
                score = self._parse_score(score_text)
                if score is not None:
                    if mid:
                        self._importance_cache[mid] = score
                    return score
            except Exception:
                pass

        # Rule-based fallback
        score = self._rule_importance(memory)
        if mid:
            self._importance_cache[mid] = score
        return score

    @staticmethod
    def _parse_score(text: str) -> Optional[float]:
        if not text:
            return None
        try:
            score = float(text.strip())
            return max(0.0, min(1.0, score))
        except ValueError:
            return None

    @staticmethod
    def _rule_importance(memory: Dict[str, Any]) -> float:
        """Rule-based importance fallback when LLM is unavailable."""
        content = memory.get("content", "")
        tags = memory.get("tags", [])
        meta = memory.get("metadata", {})
        score = 0.3  # baseline

        # Longer content may be more important
        if len(content) > 200:
            score += 0.15
        elif len(content) > 50:
            score += 0.05

        # Presence of tags
        if tags:
            score += 0.05

        # Critical tags
        critical_keywords = ("critical", "important", "essential", "preference", "rule")
        if any(kw in " ".join(tags).lower() for kw in critical_keywords):
            score += 0.2

        # Explicit importance in metadata
        if meta.get("importance"):
            try:
                score = float(meta["importance"])
            except (ValueError, TypeError):
                pass

        return max(0.0, min(1.0, score))

    # ── access metrics ─────────────────────────────────────────────────

    def _access_frequency(self, memory_id: str) -> int:
        timestamps = self._access_log.get(memory_id, [])
        now = time.time()
        # Count accesses within the last 14 days
        cutoff = now - 14 * 86400
        return sum(1 for ts in timestamps if ts >= cutoff)

    def _access_recency(self, memory_id: str) -> float:
        """Seconds since last access (lower = more recent)."""
        timestamps = self._access_log.get(memory_id, [])
        if not timestamps:
            return float("inf")
        return time.time() - max(timestamps)

    # ── eviction ───────────────────────────────────────────────────────

    def _composite_score(self, memory: Dict[str, Any]) -> float:
        """Composite eviction score. Lower score = evict first.

        Formula: norm_recency * 0.4 + norm_freq * 0.3 + importance * 0.3
        """
        mid = memory.get("id", "")
        importance = self.get_importance(memory)

        recency = self._access_recency(mid)
        # Normalize: recently accessed → higher score
        if recency == float("inf") or recency <= 0:
            norm_rec = 0.0
        else:
            ttl_x2 = self.cold_ttl * 2
            norm_rec = max(0.0, 1.0 - recency / ttl_x2)

        freq = self._access_frequency(mid)
        norm_freq = min(1.0, freq / 5.0)  # cap at 5 accesses

        return norm_rec * 0.4 + norm_freq * 0.3 + importance * 0.3

    def evict(self) -> int:
        """Evict low-score memories, preferentially from COLD tier.

        Always evicts deprecated memories first, then applies composite scoring.
        Returns count of evicted memories.
        """
        storage = self.manager.semantic
        all_memories = storage.get_all()

        evicted_ids: List[str] = []
        non_evicted: List[Dict[str, Any]] = []

        # Phase 1: always evict deprecated
        for m in all_memories:
            meta = m.get("metadata", {})
            if meta.get("deprecated") in ("true", "True", "1"):
                evicted_ids.append(m.get("id", ""))
            else:
                non_evicted.append(m)

        # Respect max tier capacities
        # Gather per-tier counts
        tiers: Dict[TierLevel, List[Dict[str, Any]]] = {
            TierLevel.HOT: [],
            TierLevel.WARM: [],
            TierLevel.COLD: [],
        }
        for m in non_evicted:
            tier = self.classify(m)
            tiers[tier].append(m)

        # Evict from COLD tier if over capacity
        max_map = {
            TierLevel.HOT: self.max_hot,
            TierLevel.WARM: self.max_warm,
            TierLevel.COLD: self.max_cold,
        }

        for tier, max_cap in max_map.items():
            if tier == TierLevel.HOT:
                continue  # Don't evict from HOT tier
            tier_mems = tiers[tier]
            overflow = len(tier_mems) - max_cap
            if overflow <= 0:
                continue
            # Score and sort: lowest score first
            scored = [(self._composite_score(m), m) for m in tier_mems]
            scored.sort(key=lambda x: x[0])
            for _, m in scored[:overflow]:
                evicted_ids.append(m.get("id", ""))

        if not evicted_ids:
            return 0

        # Mark evicted memories as deprecated (they'll be cleaned next cycle)
        valid_ids = set(eid for eid in evicted_ids if eid)
        for m in all_memories:
            if m.get("id") in valid_ids:
                m["metadata"]["deprecated"] = "true"

        self._rewrite_file(storage, all_memories)
        return len(valid_ids)

    # ── full cycle ─────────────────────────────────────────────────────

    def run_cycle(self) -> Dict[str, Any]:
        """Run a complete decay cycle: classify, score, evict.

        Returns stats dict.
        """
        t0 = time.monotonic()
        storage = self.manager.semantic
        all_m = storage.get_all()

        # Classify all
        tier_counts = {TierLevel.HOT: 0, TierLevel.WARM: 0, TierLevel.COLD: 0}
        for m in all_m:
            tier = self.classify(m)
            tier_counts[tier] += 1

        # Evict
        evicted = self.evict()

        duration = round((time.monotonic() - t0) * 1000, 1)
        self._last_cycle = time.time()

        return {
            "total": len(all_m),
            "hot": tier_counts[TierLevel.HOT],
            "warm": tier_counts[TierLevel.WARM],
            "cold": tier_counts[TierLevel.COLD],
            "evicted": evicted,
            "duration_ms": duration,
        }

    @staticmethod
    def _rewrite_file(storage, memories: List[Dict[str, Any]]) -> None:
        """Rewrite the MEMORY.md file with updated memories."""
        with open(storage.file_path, "w", encoding="utf-8") as f:
            f.write("# MEMORY.md\n\n")
            f.write("<!-- Core Memory - Permanent Storage -->\n\n")
            for mem in memories:
                f.write(storage._format_memory(mem))

    def __repr__(self) -> str:
        return (
            f"TieredDecayEngine(hot={self.hot_ttl}s, warm={self.warm_ttl//86400}d, "
            f"cold={self.cold_ttl//86400}d)"
        )
