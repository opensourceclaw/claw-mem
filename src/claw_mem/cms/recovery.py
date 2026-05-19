# Copyright 2026 Peter Cheng
"""Recovery mechanism for CMS Phase 3 (v3.0.0-rc.3)."""

from dataclasses import dataclass, field
from typing import List, Optional

from .snapshot import SessionSnapshot, SnapshotInfo, SnapshotStorage


@dataclass
class RecoveryResult:
    session_id: str
    snapshot_id: str
    strategy: str
    recovered_count: int
    errors: List[str] = field(default_factory=list)
    success: bool = True

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "snapshot_id": self.snapshot_id,
            "strategy": self.strategy,
            "recovered_count": self.recovered_count,
            "errors": self.errors,
            "success": self.success,
        }


@dataclass
class ValidationResult:
    snapshot_id: str
    is_valid: bool
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "is_valid": self.is_valid,
            "issues": self.issues,
        }


class RecoveryMechanism:
    """Session state recovery with snapshot validation.

    Strategies:
      - latest: Use the most recent snapshot.
      - specific: Use a specific snapshot by ID.
      - best_effort: Try latest, then previous snapshots.
    """

    def __init__(self, snapshot_storage: SnapshotStorage = None, memory_manager=None):
        self._storage = snapshot_storage or SnapshotStorage()
        self._mm = memory_manager

    def recover(
        self, session_id: str, snapshot_id: str = None, strategy: str = "latest"
    ) -> RecoveryResult:
        """Recover session state from a snapshot.

        Args:
            session_id: Session to recover.
            snapshot_id: Specific snapshot (for 'specific' strategy).
            strategy: Recovery strategy.

        Returns:
            RecoveryResult with count and any errors.
        """
        errors: List[str] = []
        snap: Optional[SessionSnapshot] = None

        if strategy == "specific" and snapshot_id:
            snap = self._storage.load(snapshot_id)
            if snap is None:
                errors.append(f"Snapshot not found: {snapshot_id}")

        elif strategy == "best_effort":
            snapshots = self._storage.list(session_id)
            for info in sorted(snapshots, key=lambda s: s.timestamp, reverse=True):
                snap = self._storage.load(info.snapshot_id)
                if snap:
                    break
            if snap is None:
                errors.append("No valid snapshots found")

        else:  # latest
            snapshots = self._storage.list(session_id)
            if snapshots:
                latest = max(snapshots, key=lambda s: s.timestamp)
                snap = self._storage.load(latest.snapshot_id)
            if snap is None:
                errors.append("No snapshots available")

        count = 0
        if snap:
            # Validate checksum
            validation = self.validate_snapshot(snap.snapshot_id)
            if validation.is_valid:
                count = len(snap.memory_ids)
            else:
                errors.extend(validation.issues)

        return RecoveryResult(
            session_id=session_id,
            snapshot_id=snap.snapshot_id if snap else "",
            strategy=strategy,
            recovered_count=count,
            errors=errors,
            success=len(errors) == 0,
        )

    def list_snapshots(self, session_id: str) -> List[SnapshotInfo]:
        return self._storage.list(session_id)

    def validate_snapshot(self, snapshot_id: str) -> ValidationResult:
        """Validate a snapshot's integrity via checksum."""
        snap = self._storage.load(snapshot_id)
        if snap is None:
            return ValidationResult(
                snapshot_id=snapshot_id,
                is_valid=False,
                issues=["Snapshot not found"],
            )
        expected = snap.compute_checksum()
        if expected != snap.checksum:
            return ValidationResult(
                snapshot_id=snapshot_id,
                is_valid=False,
                issues=[f"Checksum mismatch: {expected} vs {snap.checksum}"],
            )
        return ValidationResult(snapshot_id=snapshot_id, is_valid=True)
