# Copyright 2026 Peter Cheng
"""Compression result data classes for CMS Phase 2 (v3.0.0-rc.2)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SessionSummary:
    """Structured session summary."""

    session_id: str
    overview: str
    decisions: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    token_count: int = 0
    memory_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "overview": self.overview,
            "decisions": self.decisions,
            "preferences": self.preferences,
            "actions": self.actions,
            "token_count": self.token_count,
            "memory_count": self.memory_count,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DeduplicationResult:
    """Result of memory deduplication."""

    original_count: int
    deduplicated_count: int
    reduction_ratio: float
    merged_clusters: List[List[str]]  # Groups of merged memory IDs
    kept_memories: List[str]  # IDs of kept memories
    removed_memories: List[str]  # IDs of removed (duplicate) memories

    def to_dict(self) -> dict:
        return {
            "original_count": self.original_count,
            "deduplicated_count": self.deduplicated_count,
            "reduction_ratio": round(self.reduction_ratio, 4),
            "merged_clusters": self.merged_clusters,
            "kept_memories": self.kept_memories,
            "removed_memories": self.removed_memories,
        }


@dataclass
class CompressionPlan:
    """Compression execution plan."""

    strategy: str  # "aggressive" / "balanced" / "conservative"
    utilization: float
    target_reduction: float  # Target reduction ratio
    suggested_actions: List[str]  # ["deduplicate", "summarize", "archive"]
    estimated_token_savings: int

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "utilization": round(self.utilization, 4),
            "target_reduction": round(self.target_reduction, 4),
            "suggested_actions": self.suggested_actions,
            "estimated_token_savings": self.estimated_token_savings,
        }


@dataclass
class CompressionResult:
    """Full compression execution result."""

    session_id: str
    plan: CompressionPlan
    summary: Optional[SessionSummary] = None
    dedup: Optional[DeduplicationResult] = None
    original_token_count: int = 0
    final_token_count: int = 0
    reduction_ratio: float = 0.0
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "plan": self.plan.to_dict(),
            "summary": self.summary.to_dict() if self.summary else None,
            "dedup": self.dedup.to_dict() if self.dedup else None,
            "original_token_count": self.original_token_count,
            "final_token_count": self.final_token_count,
            "reduction_ratio": round(self.reduction_ratio, 4),
            "execution_time_ms": round(self.execution_time_ms, 2),
        }
