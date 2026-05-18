# Copyright 2026 Peter Cheng
"""Context switcher for CMS Phase 3 (v3.0.0-rc.3).

Manages context switching between sessions with configurable strategies.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SwitchResult:
    from_session: str
    to_session: str
    strategy: str
    preserved_memories: List[str] = field(default_factory=list)
    total_memories: int = 0
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "from_session": self.from_session,
            "to_session": self.to_session,
            "strategy": self.strategy,
            "preserved_memories": self.preserved_memories,
            "total_memories": self.total_memories,
            "success": self.success,
        }


@dataclass
class MergeResult:
    session_ids: List[str]
    merged_count: int
    total_unique: int

    def to_dict(self) -> dict:
        return {
            "session_ids": self.session_ids,
            "merged_count": self.merged_count,
            "total_unique": self.total_unique,
        }


class ContextSwitcher:
    """Manages context switching between sessions.

    Strategies:
      - preserve_important: Keep high-importance memories in new context.
      - full_switch: Complete switch, no preservation.
      - merge_context: Merge memories from multiple contexts.
    """

    def __init__(self, importance_evaluator=None, memory_manager=None):
        self._evaluator = importance_evaluator
        self._mm = memory_manager

    def switch(
        self, from_id: str, to_id: str, strategy: str = "preserve_important"
    ) -> SwitchResult:
        """Switch context from one session to another.

        Args:
            from_id: Source session ID.
            to_id: Target session ID.
            strategy: Switching strategy.

        Returns:
            SwitchResult with preserved memories.
        """
        preserved: List[str] = []

        if strategy == "preserve_important" and self._evaluator:
            try:
                important = self._evaluator.get_important_memories(threshold=0.5, limit=20)
                preserved = [s.memory_id for s in important]
            except Exception:
                pass

        elif strategy == "merge_context":
            preserved = self._merge_sessions([from_id, to_id])

        return SwitchResult(
            from_session=from_id,
            to_session=to_id,
            strategy=strategy,
            preserved_memories=preserved[:50],
            total_memories=len(preserved),
            success=True,
        )

    def merge(self, context_ids: List[str]) -> MergeResult:
        """Merge multiple contexts into one.

        Args:
            context_ids: Session IDs to merge.

        Returns:
            MergeResult with merged counts.
        """
        all_ids = self._merge_sessions(context_ids)
        return MergeResult(
            session_ids=list(context_ids),
            merged_count=len(context_ids),
            total_unique=len(all_ids),
        )

    def get_active_contexts(self) -> List[str]:
        """Get all active context IDs."""
        if self._mm is None:
            return []
        return []

    def _merge_sessions(self, session_ids: List[str]) -> List[str]:
        """Collect all memory IDs from multiple sessions."""
        all_ids: List[str] = []
        seen = set()
        for sid in session_ids:
            if self._mm:
                try:
                    memories = self._mm.episodic.get_all()
                    for m in memories:
                        mid = m.get("id", "")
                        if mid and mid not in seen:
                            seen.add(mid)
                            all_ids.append(mid)
                except Exception:
                    pass
        return all_ids
