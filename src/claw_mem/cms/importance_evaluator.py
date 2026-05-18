# Copyright 2026 Peter Cheng
"""Importance evaluator for CMS Perception Layer (v3.0.0-rc.1).

Evaluates memory importance using base score + access boost + recency boost,
enabling prioritization for compression and retention decisions.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

TYPE_IMPORTANCE = {
    "critical": 1.0,
    "preference": 0.8,
    "decision": 0.7,
    "fact": 0.5,
    "task": 0.4,
    "chat": 0.2,
}


@dataclass
class ImportanceScore:
    """Importance evaluation result for a single memory."""

    memory_id: str
    base_score: float  # Content type base score (0.0-1.0)
    access_boost: float  # Access frequency boost (0.0-0.3)
    recency_boost: float  # Recency boost (0.0-0.2)
    total_score: float  # Combined score (0.0-1.5)
    content_type: str  # Detected content type

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "base_score": round(self.base_score, 4),
            "access_boost": round(self.access_boost, 4),
            "recency_boost": round(self.recency_boost, 4),
            "total_score": round(self.total_score, 4),
            "content_type": self.content_type,
        }


class ImportanceEvaluator:
    """Evaluates memory importance using multiple scoring factors.

    Score formula:
        total = base(content_type) + access_boost + recency_boost

    Where:
        base:       Content type classification (0.2 - 1.0)
        access:     +0.1 per 5 accesses, capped at 0.3
        recency:    +0.2 * (1 - age/30d), capped at 0.2
    """

    def __init__(self, memory_manager=None):
        self._mm = memory_manager
        self._access_counts: Dict[str, int] = {}
        self._type_cache: Dict[str, str] = {}

    def evaluate(self, memory_id: str) -> ImportanceScore:
        """Evaluate importance for a single memory.

        Args:
            memory_id: Memory ID to evaluate.

        Returns:
            ImportanceScore with all component scores.
        """
        content = self._get_content(memory_id)
        content_type = self._detect_type(content) if content else "chat"

        # Base score from content type
        base = TYPE_IMPORTANCE.get(content_type, 0.2)

        # Access boost
        access_count = self._access_counts.get(memory_id, 0)
        access_boost = min(0.3, (access_count // 5) * 0.1)

        # Recency boost
        recency_boost = self._calc_recency_boost(memory_id)

        total = base + access_boost + recency_boost

        return ImportanceScore(
            memory_id=memory_id,
            base_score=base,
            access_boost=access_boost,
            recency_boost=recency_boost,
            total_score=total,
            content_type=content_type,
        )

    def evaluate_batch(self, memory_ids: List[str]) -> Dict[str, ImportanceScore]:
        """Evaluate importance for multiple memories."""
        results = {}
        for mid in memory_ids:
            results[mid] = self.evaluate(mid)
        return results

    def get_important_memories(
        self, threshold: float = 0.5, limit: int = 50
    ) -> List[ImportanceScore]:
        """Get memories above importance threshold.

        Args:
            threshold: Minimum total_score.
            limit: Maximum results.

        Returns:
            List of ImportanceScore ordered by total_score descending.
        """
        # Gather all memory IDs from the manager
        all_ids: List[str] = []
        if self._mm:
            try:
                episodic = self._mm.episodic.get_all()
                all_ids.extend(m.get("id", "") for m in episodic if m.get("id"))
            except Exception:
                pass

        scores = self.evaluate_batch(all_ids)
        important = [s for s in scores.values() if s.total_score >= threshold]
        important.sort(key=lambda s: s.total_score, reverse=True)
        return important[:limit]

    def record_access(self, memory_id: str) -> None:
        """Record a memory access for scoring calculation."""
        self._access_counts[memory_id] = self._access_counts.get(memory_id, 0) + 1

    def _get_content(self, memory_id: str) -> Optional[str]:
        """Get memory content from MemoryManager."""
        if self._mm is None:
            return None
        try:
            node = None
            if hasattr(self._mm, "multi_graph") and self._mm.multi_graph:
                node = self._mm.multi_graph.get_node(memory_id)
            if node:
                return getattr(node, "content", "")
        except Exception:
            pass
        return None

    def _detect_type(self, content: str) -> str:
        """Rule-based content type detection."""
        lower = content.lower()
        if any(k in lower for k in ["critical", "critical_rule", "always inject"]):
            return "critical"
        if any(k in lower for k in ["prefer", "preference", "喜欢", "偏好"]):
            return "preference"
        if any(k in lower for k in ["decide", "decision", "choose", "决定", "选择"]):
            return "decision"
        if any(k in lower for k in ["important", "note", "fact", "重要", "记住"]):
            return "fact"
        if any(k in lower for k in ["task", "working on", "building", "任务", "开发"]):
            return "task"
        return "chat"

    def _calc_recency_boost(self, memory_id: str) -> float:
        """Calculate recency boost based on memory age."""
        if self._mm is None:
            return 0.0
        try:
            node = None
            if hasattr(self._mm, "multi_graph") and self._mm.multi_graph:
                node = self._mm.multi_graph.get_node(memory_id)
            if node and hasattr(node, "created_at"):
                created = node.created_at
                if hasattr(created, "timestamp"):
                    created = created.timestamp()
                elif isinstance(created, (int, float)):
                    pass
                else:
                    return 0.0
                age_days = (time.time() - created) / 86400.0
                return max(0.0, 0.2 * (1.0 - age_days / 30.0))
        except Exception:
            pass
        return 0.0
