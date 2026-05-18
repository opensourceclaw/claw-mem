# Copyright 2026 Peter Cheng
"""Memory deduplicator for CMS Phase 2 (v3.0.0-rc.2).

Uses EngramIndex for fast similarity lookup, then clusters and
merges duplicate/similar memories.
"""

from typing import Dict, List, Optional, Set, Tuple
from .compression_result import DeduplicationResult


class MemoryDeduplicator:
    """Find and merge similar/duplicate memories.

    Uses EngramIndex for O(1) similarity lookup, then applies
    Jaccard similarity threshold for clustering.
    """

    def __init__(self, memory_manager=None,
                 similarity_threshold: float = 0.85):
        self._mm = memory_manager
        self._similarity_threshold = similarity_threshold

    def deduplicate(self, memory_ids: List[str]) -> DeduplicationResult:
        """Deduplicate a list of memory IDs.

        Args:
            memory_ids: List of memory IDs to check.

        Returns:
            DeduplicationResult with clusters, kept/removed IDs.
        """
        if not memory_ids:
            return DeduplicationResult(
                original_count=0, deduplicated_count=0,
                reduction_ratio=0.0, merged_clusters=[],
                kept_memories=[], removed_memories=[],
            )

        # Get contents
        contents: Dict[str, str] = {}
        for mid in memory_ids:
            c = self._get_content(mid)
            if c:
                contents[mid] = c

        if not contents:
            return DeduplicationResult(
                original_count=len(memory_ids),
                deduplicated_count=len(memory_ids),
                reduction_ratio=0.0, merged_clusters=[],
                kept_memories=list(memory_ids),
                removed_memories=[],
            )

        # Find similarity pairs using Engram
        similar_pairs = self._find_similar_pairs(contents)

        # Build clusters (Union-Find)
        clusters = self._build_clusters(list(contents.keys()), similar_pairs)

        # Determine keep/remove per cluster
        kept = []
        removed = []
        merged = []

        for cluster in clusters:
            if len(cluster) == 1:
                kept.append(cluster[0])
            else:
                merged.append(cluster)
                # Keep the longest content, remove others
                cluster.sort(key=lambda mid: len(contents.get(mid, "")), reverse=True)
                kept.append(cluster[0])
                removed.extend(cluster[1:])

        original = len(contents)
        deduped = len(kept)
        ratio = 1.0 - (deduped / original) if original > 0 else 0.0

        return DeduplicationResult(
            original_count=original,
            deduplicated_count=deduped,
            reduction_ratio=ratio,
            merged_clusters=merged,
            kept_memories=kept,
            removed_memories=removed,
        )

    def _find_similar_pairs(self, contents: Dict[str, str]) -> List[Tuple[str, str]]:
        """Find pairs of similar memories using Engram."""
        pairs = []
        ids = list(contents.keys())

        if self._mm and hasattr(self._mm, 'engram') and self._mm.engram:
            for i, mid in enumerate(ids):
                results = self._mm.engram.lookup(
                    contents[mid], top_k=min(5, len(ids))
                )
                for result_id, score in results:
                    if result_id != mid and score >= self._similarity_threshold:
                        pairs.append((mid, result_id))
        else:
            # Fallback: simple word overlap
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    sim = self._word_overlap(
                        contents[ids[i]], contents[ids[j]]
                    )
                    if sim >= self._similarity_threshold:
                        pairs.append((ids[i], ids[j]))

        return pairs

    def _build_clusters(self, all_ids: List[str],
                        pairs: List[Tuple[str, str]]) -> List[List[str]]:
        """Union-Find clustering."""
        parent = {mid: mid for mid in all_ids}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for a, b in pairs:
            union(a, b)

        clusters: Dict[str, List[str]] = {}
        for mid in all_ids:
            root = find(mid)
            clusters.setdefault(root, []).append(mid)

        return list(clusters.values())

    def _get_content(self, memory_id: str) -> str:
        """Get memory content from MemoryManager."""
        if self._mm is None:
            return ""
        try:
            if hasattr(self._mm, 'multi_graph') and self._mm.multi_graph:
                node = self._mm.multi_graph.get_node(memory_id)
                if node:
                    return getattr(node, 'content', '')
        except Exception:
            pass
        return ""

    def _word_overlap(self, a: str, b: str) -> float:
        """Simple Jaccard word overlap."""
        wa = set(a.lower().split())
        wb = set(b.lower().split())
        if not wa or not wb:
            return 0.0
        return len(wa & wb) / len(wa | wb)
