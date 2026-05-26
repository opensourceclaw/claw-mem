"""
MemoryPool — shared memory pool for cross-agent memory sharing.

In-memory storage with optional file-backed persistence.
Supports store, query, filtering, PII auto-filtering, and
thread-safe operations for claw-mem v4.0.
"""

from typing import Any, Dict, List, Optional
import threading
import json
import time
import os

from .agnostic import MemoryRecord


class MemoryPool:
    """Shared memory pool for cross-agent memory.

    In-memory by default (fast, no disk I/O for MVP).
    Optional file-backed persistence via storage_path.

    Thread-safe with auto PII filtering before store.

    Example:
        >>> pool = MemoryPool()
        >>> record = MemoryRecord(id="r1", agent_id="a1",
        ...     memory_type="episodic", content="hello",
        ...     tags=["greeting"], timestamp=0.0)
        >>> pool.store(record)
        >>> results = pool.query({})
        >>> pool.stats()
        >>> pool.clear()
    """

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize pool with optional file-backed storage.

        Args:
            storage_path: Path to JSON file for persistence.
        """
        self._records: List[MemoryRecord] = []
        self._lock = threading.Lock()
        self.storage_path = storage_path

        # Load from file if exists
        if storage_path and os.path.exists(storage_path):
            self._load()

    def store(self, record: MemoryRecord) -> str:
        """Store a record to the shared pool. Auto-filters PII.

        Args:
            record: The MemoryRecord to store.

        Returns:
            The record ID.
        """
        from .agnostic import AgentAgnosticMemory

        # Auto-filter PII if source is local
        if record.source == "local":
            record.content = AgentAgnosticMemory._strip_pii(record.content)

        with self._lock:
            self._records.append(record)

        # Persist if file-backed
        if self.storage_path:
            self._save()

        return record.id

    def query(self, filter: Dict[str, Any]) -> List[MemoryRecord]:
        """Query across all agents' memories with optional filters.

        Args:
            filter: Dict with optional keys: agent_id, memory_type,
                    tags (any match), since, until, min_confidence.

        Returns:
            List of matching MemoryRecords.
        """
        results: List[MemoryRecord] = []

        with self._lock:
            for record in self._records:
                if self._matches(record, filter):
                    results.append(record)

        return results

    def get_agent_memories(self, agent_id: str) -> List[MemoryRecord]:
        """Get all memories from a specific agent.

        Args:
            agent_id: The agent ID to query.

        Returns:
            List of MemoryRecords for the agent.
        """
        return self.query({"agent_id": agent_id})

    def stats(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dict with total_records, agent_count, top_tags,
            oldest/newest timestamps.
        """
        with self._lock:
            if not self._records:
                return {
                    "total_records": 0,
                    "agent_count": 0,
                    "top_tags": [],
                    "oldest": None,
                    "newest": None,
                }

            agents = set(r.agent_id for r in self._records)
            tag_counts: Dict[str, int] = {}
            for r in self._records:
                for tag in r.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:5]

            timestamps = [r.timestamp for r in self._records]

            return {
                "total_records": len(self._records),
                "agent_count": len(agents),
                "top_tags": [t[0] for t in top_tags],
                "oldest": min(timestamps),
                "newest": max(timestamps),
            }

    def cleanup(self, max_age_days: int = 30) -> int:
        """Remove records older than max_age_days.

        Args:
            max_age_days: Remove records older than this many days.

        Returns:
            Number of records removed.
        """
        cutoff = time.time() - (max_age_days * 86400)
        with self._lock:
            before = len(self._records)
            self._records = [r for r in self._records if r.timestamp > cutoff]
            removed = before - len(self._records)

        if removed > 0 and self.storage_path:
            self._save()

        return removed

    def clear(self) -> None:
        """Clear all records (for testing)."""
        with self._lock:
            self._records.clear()
        if self.storage_path and os.path.exists(self.storage_path):
            os.remove(self.storage_path)

    def _matches(self, record: MemoryRecord, filt: Dict[str, Any]) -> bool:
        """Check if a record matches a filter.

        Args:
            record: The record to check.
            filt: Filter dictionary.

        Returns:
            True if the record matches all filter criteria.
        """
        if "agent_id" in filt and record.agent_id != filt["agent_id"]:
            return False
        if "memory_type" in filt and record.memory_type != filt["memory_type"]:
            return False
        if "tags" in filt:
            req_tags = set(filt["tags"])
            if not req_tags.issubset(set(record.tags)):
                return False
        if "since" in filt and record.timestamp < filt["since"]:
            return False
        if "until" in filt and record.timestamp > filt["until"]:
            return False
        if "min_confidence" in filt and record.confidence < filt["min_confidence"]:
            return False
        return True

    def _save(self) -> None:
        """Persist records to storage_path."""
        if not self.storage_path:
            return
        data = [
            {
                "id": r.id,
                "agent_id": r.agent_id,
                "memory_type": r.memory_type,
                "content": r.content,
                "tags": r.tags,
                "timestamp": r.timestamp,
                "confidence": r.confidence,
                "source": r.source,
            }
            for r in self._records
        ]
        with open(self.storage_path, "w") as f:
            json.dump(data, f)

    def _load(self) -> None:
        """Load records from storage_path."""
        if not self.storage_path:
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            self._records = [
                MemoryRecord(
                    id=d["id"],
                    agent_id=d["agent_id"],
                    memory_type=d["memory_type"],
                    content=d["content"],
                    tags=d["tags"],
                    timestamp=d["timestamp"],
                    confidence=d.get("confidence", 1.0),
                    source=d.get("source", "shared"),
                )
                for d in data
            ]
        except (json.JSONDecodeError, KeyError):
            self._records = []
