"""
claw-mem v2.9.1 - Belief Tracker

Tracks belief versions over time, recording when beliefs are
created, updated, or contradicted. Provides version history
for audit and debugging.

Belief lifecycle:
  Created → Updated (v1→v2→...) → Contradicted → [Resolved]
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BeliefVersion:
    """A single version of a belief."""
    belief_id: str
    statement: str
    confidence: float
    version: int
    created_at: str
    previous_statement: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "belief_id": self.belief_id,
            "statement": self.statement,
            "confidence": self.confidence,
            "version": self.version,
            "created_at": self.created_at,
            "previous_statement": self.previous_statement,
        }


@dataclass
class BeliefHistory:
    """Complete history of a belief."""
    belief_id: str
    versions: List[BeliefVersion] = field(default_factory=list)

    @property
    def current(self) -> Optional[BeliefVersion]:
        return self.versions[-1] if self.versions else None

    @property
    def version_count(self) -> int:
        return len(self.versions)

    def was_updated(self) -> bool:
        return len(self.versions) > 1


class BeliefTracker:
    """Track belief creation and evolution over time.

    Records every change to a belief, including:
    - Initial creation (v1)
    - Statement updates (v2, v3, ...)
    - Confidence changes
    - Contradictions

    Usage:
        tracker = BeliefTracker()
        tracker.record("BEL_001", "User prefers Python", 0.8)
        tracker.update("BEL_001", "User prefers Python >= 3.10", 0.9)
        history = tracker.get_history("BEL_001")
    """

    def __init__(self):
        # belief_id → list of BeliefVersion
        self._store: Dict[str, List[BeliefVersion]] = {}

    def record(self, belief_id: str, statement: str, confidence: float):
        """Record a new belief (v1).

        Args:
            belief_id: Unique belief identifier
            statement: Belief statement
            confidence: Confidence score (0.0-1.0)
        """
        version = BeliefVersion(
            belief_id=belief_id,
            statement=statement,
            confidence=confidence,
            version=1,
            created_at=datetime.utcnow().isoformat(),
        )
        self._store.setdefault(belief_id, []).append(version)

    def update(self, belief_id: str, statement: str, confidence: float):
        """Update an existing belief to a new version.

        Args:
            belief_id: Existing belief identifier
            statement: Updated statement
            confidence: Updated confidence
        """
        if belief_id not in self._store:
            self.record(belief_id, statement, confidence)
            return

        previous = self._store[belief_id][-1]
        new_version = BeliefVersion(
            belief_id=belief_id,
            statement=statement,
            confidence=confidence,
            version=previous.version + 1,
            created_at=datetime.utcnow().isoformat(),
            previous_statement=previous.statement,
        )
        self._store[belief_id].append(new_version)

    def get_current(self, belief_id: str) -> Optional[BeliefVersion]:
        """Get the current (latest) version of a belief."""
        versions = self._store.get(belief_id, [])
        return versions[-1] if versions else None

    def get_history(self, belief_id: str) -> List[BeliefVersion]:
        """Get all versions of a belief."""
        return self._store.get(belief_id, [])

    def get_all_ids(self) -> List[str]:
        """Get all belief IDs."""
        return list(self._store.keys())

    def get_all_current(self) -> List[BeliefVersion]:
        """Get current version of all beliefs."""
        return [
            versions[-1]
            for versions in self._store.values()
            if versions
        ]

    def get_changes_since(self, cutoff: str) -> List[BeliefVersion]:
        """Get beliefs changed after a timestamp.

        Args:
            cutoff: ISO timestamp string
        """
        changed = []
        for versions in self._store.values():
            for v in versions:
                if v.created_at > cutoff:
                    changed.append(v)
        return changed

    def count_beliefs(self) -> int:
        """Count unique beliefs."""
        return len(self._store)

    def count_versions(self) -> int:
        """Count total belief versions."""
        return sum(len(v) for v in self._store.values())
