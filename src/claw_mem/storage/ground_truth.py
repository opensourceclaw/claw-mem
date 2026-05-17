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
GroundTruthStore - Complete raw conversation preservation.

Stores full conversation transcripts per session for traceability
and deep analysis. Complements Episodic Storage (structured memories)
by preserving the original dialogue in its entirety.
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class GroundTruthRecord:
    """A single raw conversation record."""

    record_id: str
    session_id: str
    messages: List[Dict]
    timestamp: float
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "session_id": self.session_id,
            "messages": self.messages,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GroundTruthRecord":
        return cls(
            record_id=d["record_id"],
            session_id=d["session_id"],
            messages=d.get("messages", []),
            timestamp=d.get("timestamp", 0.0),
            metadata=d.get("metadata", {}),
        )


class GroundTruthStore:
    """Preserves full raw conversation transcripts.

    Storage layout:
        ~/.claw-mem/ground_truth/
            session_{id}.json   # One JSON file per session

    Design: append-only files; one JSON array per session file.
    """

    def __init__(self, workspace: str = None):
        if workspace is None:
            workspace = os.path.expanduser("~/.claw-mem")
        self._base_dir = Path(workspace) / "ground_truth"
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        safe_id = session_id.replace("/", "_").replace(":", "_")
        return self._base_dir / f"session_{safe_id}.json"

    def store_turn(self, session_id: str, messages: List[Dict],
                   metadata: Optional[Dict] = None) -> str:
        """Store one or more conversation turns.

        Args:
            session_id: OpenClaw session identifier.
            messages: List of message dicts with 'role' and 'content'.
            metadata: Optional metadata for this batch.

        Returns:
            record_id (format: gt_<hex16>).
        """
        record = GroundTruthRecord(
            record_id=f"gt_{uuid.uuid4().hex[:16]}",
            session_id=session_id,
            messages=messages,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        filepath = self._session_path(session_id)
        session_data = self._load_session_file(filepath)
        session_data.append(record.to_dict())
        self._save_session_file(filepath, session_data)
        return record.record_id

    def store_session(self, session_id: str,
                      all_messages: List[Dict],
                      metadata: Optional[Dict] = None) -> str:
        """Store an entire session at once (called from agent_end)."""
        return self.store_turn(session_id, all_messages, metadata)

    def get_session(self, session_id: str) -> List[Dict]:
        """Get all records for a session."""
        return self._load_session_file(self._session_path(session_id))

    def search(self, session_id: Optional[str] = None,
               keyword: Optional[str] = None,
               limit: int = 50) -> List[Dict]:
        """Search raw conversations.

        Args:
            session_id: Optional session filter.
            keyword: Optional content keyword filter.
            limit: Maximum results.
        """
        results: List[Dict] = []
        kw_lower = keyword.lower() if keyword else None

        if session_id:
            paths = [self._session_path(session_id)]
        else:
            paths = sorted(
                self._base_dir.glob("session_*.json"),
                key=os.path.getmtime, reverse=True,
            )

        for fp in paths:
            sid = fp.stem.replace("session_", "") if isinstance(fp, Path) else None
            records = self._load_session_file(fp)
            for r in records:
                for m in r.get("messages", []):
                    if kw_lower and kw_lower not in str(m).lower():
                        continue
                    results.append({
                        "session_id": sid or session_id,
                        "message": m,
                        "timestamp": r.get("timestamp", 0),
                    })
                    if len(results) >= limit:
                        return results
        return results[:limit]

    def list_sessions(self) -> List[Dict]:
        """List all stored sessions with metadata."""
        sessions = []
        for f in sorted(
            self._base_dir.glob("session_*.json"),
            key=os.path.getmtime, reverse=True,
        ):
            sessions.append({
                "session_id": f.stem.replace("session_", ""),
                "file_size": f.stat().st_size,
                "last_modified": f.stat().st_mtime,
            })
        return sessions

    def count_records(self) -> int:
        total = 0
        for f in self._base_dir.glob("session_*.json"):
            data = self._load_session_file(f)
            total += len(data)
        return total

    # ── Internal helpers ────────────────────────────────────────────

    def _load_session_file(self, filepath: Path) -> List[Dict]:
        if not filepath.exists():
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_session_file(self, filepath: Path, data: List[Dict]) -> None:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
