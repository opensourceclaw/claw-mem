# Copyright 2026 Peter Cheng
"""Snapshot storage for CMS Phase 3 (v3.0.0-rc.3)."""

import hashlib
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SessionSnapshot:
    session_id: str
    snapshot_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    state: str = "active"
    memories: List[Dict] = field(default_factory=list)
    memory_ids: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    checksum: str = ""

    def compute_checksum(self) -> str:
        data = json.dumps([
            self.session_id, self.state, self.memory_ids, self.metadata
        ], sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp.isoformat(),
            "state": self.state,
            "memory_ids": self.memory_ids,
            "metadata": self.metadata,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SessionSnapshot":
        ts = d.get("timestamp", "")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            session_id=d["session_id"],
            snapshot_id=d["snapshot_id"],
            timestamp=ts if isinstance(ts, datetime) else datetime.now(),
            state=d.get("state", "active"),
            memory_ids=d.get("memory_ids", []),
            metadata=d.get("metadata", {}),
            checksum=d.get("checksum", ""),
        )


@dataclass
class SnapshotInfo:
    session_id: str
    snapshot_id: str
    timestamp: datetime
    state: str
    size_bytes: int


class SnapshotStorage:
    """Snapshot persistence with full + delta support.

    Storage layout:
        ~/.claw-mem/snapshots/
            {session_id}/
                full_{snapshot_id}.json
                delta_{snapshot_id}.json
    """

    def __init__(self, workspace: str = None):
        if workspace is None:
            workspace = os.path.expanduser("~/.claw-mem")
        self._base = Path(workspace) / "snapshots"
        self._base.mkdir(parents=True, exist_ok=True)
        self._last_full: Dict[str, str] = {}  # session_id → snapshot_id

    def save(self, session_id: str, state: str = "active",
             memory_ids: List[str] = None,
             metadata: Dict = None) -> str:
        """Save a new snapshot.

        Returns:
            snapshot_id
        """
        snap = SessionSnapshot(
            session_id=session_id,
            snapshot_id=f"snap_{uuid.uuid4().hex[:16]}",
            state=state,
            memory_ids=list(memory_ids) if memory_ids else [],
            metadata=dict(metadata) if metadata else {},
        )
        snap.checksum = snap.compute_checksum()
        data = snap.to_dict()

        sdir = self._base / session_id.replace("/", "_")
        sdir.mkdir(parents=True, exist_ok=True)

        is_full = session_id not in self._last_full
        prefix = "full" if is_full else "delta"
        fpath = sdir / f"{prefix}_{snap.snapshot_id}.json"

        with open(fpath, 'w') as f:
            json.dump(data, f, indent=2)

        if is_full:
            self._last_full[session_id] = snap.snapshot_id
            # Store memory data in the snapshot
            fpath_mem = sdir / f"mem_{snap.snapshot_id}.json"
            with open(fpath_mem, 'w') as f:
                json.dump({"memory_ids": snap.memory_ids}, f)

        return snap.snapshot_id

    def load(self, snapshot_id: str) -> Optional[SessionSnapshot]:
        """Load a snapshot by ID."""
        for sdir in self._base.iterdir():
            if not sdir.is_dir():
                continue
            for fpath in sdir.glob("*.json"):
                if 'mem_' in fpath.stem:
                    continue
                if snapshot_id in fpath.stem:
                    with open(fpath) as f:
                        return SessionSnapshot.from_dict(json.load(f))
        return None

    def list(self, session_id: str) -> List[SnapshotInfo]:
        """List all snapshots for a session."""
        sdir = self._base / session_id.replace("/", "_")
        if not sdir.exists():
            return []
        results = []
        for pattern in ["full_*.json", "delta_*.json"]:
            for fpath in sorted(sdir.glob(pattern)):
                if 'mem_' in fpath.stem:
                    continue
                try:
                    with open(fpath) as f:
                        d = json.load(f)
                    ts = d.get("timestamp", "")
                    if isinstance(ts, str) and ts:
                        ts = datetime.fromisoformat(ts)
                    results.append(SnapshotInfo(
                        session_id=session_id,
                        snapshot_id=d.get("snapshot_id", fpath.stem),
                        timestamp=ts if isinstance(ts, datetime) else datetime.now(),
                        state=d.get("state", "unknown"),
                        size_bytes=fpath.stat().st_size,
                    ))
                except Exception:
                    pass
        return results

    def delete(self, snapshot_id: str) -> bool:
        """Delete a snapshot by ID."""
        deleted = False
        for sdir in self._base.iterdir():
            if not sdir.is_dir():
                continue
            for fpath in sdir.glob(f"*{snapshot_id}*.json"):
                if fpath.is_file():
                    fpath.unlink()
                    deleted = True
        return deleted
