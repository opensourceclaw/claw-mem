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
SemanticMergeScheduler (F1 · v4.7.0)

Detects semantically similar memories, merges them via LLM generation,
and marks source memories as deprecated.
"""

import math
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..memory_manager import MemoryManager
    from ..llm_provider import LLMProvider
    from ..retrieval.embedding_service import EmbeddingService


_MERGE_SYSTEM_PROMPT = (
    "You are a memory consolidation assistant. Merge the following related memories "
    "into one concise, factual statement. "
    "Preserve all unique information from both memories. "
    "Do not add new information. "
    "If the memories contradict each other, keep the more specific one."
)

_MERGE_PROMPT_TEMPLATE = (
    "You are a memory consolidation assistant. "
    "Merge the following related memories into one concise, "
    "factual statement. Preserve all unique information."
    "\n\n"
    "Memory A: {mem_a}"
    "\n\n"
    "Memory B: {mem_b}"
    "\n\n"
    "Merged memory:"
)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Cosine similarity between two vectors (pure Python, no numpy)."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticMergeScheduler:
    """Detects and merges semantically similar memories using LLM generation.

    Run periodically (every N interactions) to keep the semantic memory store
    compact and free of redundant entries.

    Attributes:
        merge_interval: Number of interactions between merge cycles.
        high_sim_threshold: Pairs above this are direct-merged (0.85+).
        med_sim_threshold:  Pairs above this are candidate for merging (0.65+).
    """

    def __init__(
        self,
        manager: "MemoryManager",
        llm_provider: "LLMProvider",
        embedding_service: "EmbeddingService" = None,
        merge_interval: int = 100,
        merge_check: str = "auto",
        high_sim_threshold: float = 0.85,
        med_sim_threshold: float = 0.65,
    ):
        self.manager = manager
        self.llm_provider = llm_provider
        self._embedding_service = embedding_service
        self.merge_interval = merge_interval
        self.merge_check = merge_check
        self.high_sim_threshold = high_sim_threshold
        self.med_sim_threshold = med_sim_threshold
        self._last_merge_at: float = 0.0
        self._merge_count: int = 0

    @property
    def embedding_service(self) -> "EmbeddingService":
        """Lazy-load EmbeddingService if not injected."""
        if self._embedding_service is None:
            from ..retrieval.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    # ── lifecycle ──────────────────────────────────────────────────────

    def should_run(self, interaction_count: int) -> bool:
        """Return True if enough interactions have passed since last merge."""
        if interaction_count < self.merge_interval:
            return False
        return (interaction_count % self.merge_interval) == 0

    # ── candidate detection ────────────────────────────────────────────

    def find_merge_candidates(self) -> List[Tuple[str, str, float]]:
        """Find semantic memory pairs above the medium similarity threshold.

        Returns:
            List of (id1, id2, similarity) tuples, sorted by similarity descending.
        """
        storage = self.manager.semantic
        all_memories = storage.get_all()

        # Filter out deprecated memories and those without IDs
        active: List[Dict[str, Any]] = []
        for m in all_memories:
            meta = m.get("metadata", {})
            if meta.get("deprecated") in ("true", "True", "1"):
                continue
            mid = m.get("id")
            if not mid:
                continue
            content = m.get("content", "")
            if not content or not content.strip():
                continue
            active.append(m)

        n = len(active)
        if n < 2:
            return []

        # Compute embeddings for all active memories
        texts = [m["content"] for m in active]
        embeddings = self.embedding_service.encode(texts)

        # Pairwise similarity
        candidates: List[Tuple[str, str, float]] = []
        for i in range(n):
            for j in range(i + 1, n):
                sim = _cosine_similarity(embeddings[i], embeddings[j])
                if sim >= self.med_sim_threshold:
                    candidates.append((active[i]["id"], active[j]["id"], sim))

        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates

    # ── merge single pair ──────────────────────────────────────────────

    def merge_pair(
        self, mem1: Dict[str, Any], mem2: Dict[str, Any], similarity: float
    ) -> Optional[Dict[str, Any]]:
        """Merge two memory records into one using LLM generation.

        Stores the merged memory and marks the two source memories as deprecated
        on success. Returns the new memory dict or None on failure.
        """
        content_a = mem1.get("content", "")
        content_b = mem2.get("content", "")
        if not content_a or not content_b:
            return None

        # Build prompt
        prompt = _MERGE_PROMPT_TEMPLATE.format(mem_a=content_a, mem_b=content_b)

        # Generate merged text via LLM
        merged_text = self.llm_provider.generate(prompt, system="", max_tokens=256)
        if not merged_text:
            return None

        # Collect tags from both sources
        tags = list(set(mem1.get("tags", []) + mem2.get("tags", [])))

        # Merge metadata (excluding internal keys)
        merged_meta: Dict[str, str] = {}
        for key, val in mem1.get("metadata", {}).items():
            merged_meta[key] = str(val)
        for key, val in mem2.get("metadata", {}).items():
            merged_meta[key] = str(val)
        merged_meta["merged_from"] = f"{mem1.get('id', '?')},{mem2.get('id', '?')}"
        merged_meta["merge_similarity"] = f"{similarity:.4f}"

        # Store the merged memory
        new_record = {
            "content": merged_text,
            "tags": tags,
            "metadata": merged_meta,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            self.manager.store(
                content=merged_text,
                memory_type="semantic",
                tags=tags,
                metadata=merged_meta,
                update_index=True,
            )
        except Exception:
            return None

        # Mark source memories as deprecated
        self._mark_deprecated([mem1.get("id", ""), mem2.get("id", "")])

        self._merge_count += 1
        return new_record

    def _mark_deprecated(self, memory_ids: List[str]) -> None:
        """Mark semantic memories as deprecated in the MEMORY.md file."""
        valid_ids = {mid for mid in memory_ids if mid}
        if not valid_ids:
            return

        storage = self.manager.semantic
        all_memories = storage.get_all()
        for mem in all_memories:
            if mem.get("id") in valid_ids:
                mem["metadata"]["deprecated"] = "true"

        self._rewrite_semantic_file(storage, all_memories)

    @staticmethod
    def _rewrite_semantic_file(storage, memories: List[Dict[str, Any]]) -> None:
        """Rewrite the MEMORY.md file with updated memories list."""
        with open(storage.file_path, "w", encoding="utf-8") as f:
            f.write("# MEMORY.md\n\n")
            f.write("<!-- Core Memory - Permanent Storage -->\n\n")
            for mem in memories:
                f.write(storage._format_memory(mem))

    # ── full cycle ─────────────────────────────────────────────────────

    def run_merge_cycle(self) -> Dict[str, Any]:
        """Run a complete merge cycle.

        Returns stats: {merged_count, skipped_count, errors, candidates_found,
                        pairs_processed, duration_ms}
        """
        t0 = time.monotonic()
        stats: Dict[str, Any] = {
            "merged_count": 0,
            "skipped_count": 0,
            "errors": 0,
            "candidates_found": 0,
        }

        # Find candidates
        candidates = self.find_merge_candidates()
        stats["candidates_found"] = len(candidates)

        # Track already-merged IDs to avoid re-merging
        processed: set = set()

        for id1, id2, sim in candidates:
            if id1 in processed or id2 in processed:
                stats["skipped_count"] += 1
                continue

            # Look up memory records
            storage = self.manager.semantic
            all_m = storage.get_all()
            mem1 = next((m for m in all_m if m.get("id") == id1), None)
            mem2 = next((m for m in all_m if m.get("id") == id2), None)
            if mem1 is None or mem2 is None:
                stats["skipped_count"] += 1
                continue

            # Adjust merge strategy based on similarity
            try:
                result = self.merge_pair(mem1, mem2, sim)
                if result is not None:
                    stats["merged_count"] += 1
                    processed.add(id1)
                    processed.add(id2)
                else:
                    stats["skipped_count"] += 1
            except Exception:
                stats["errors"] += 1

        stats["pairs_processed"] = stats["merged_count"] + stats["skipped_count"]
        stats["duration_ms"] = round((time.monotonic() - t0) * 1000, 1)
        self._last_merge_at = time.time()
        return stats

    def __repr__(self) -> str:
        return (
            f"SemanticMergeScheduler(interval={self.merge_interval}, "
            f"merged={self._merge_count})"
        )
