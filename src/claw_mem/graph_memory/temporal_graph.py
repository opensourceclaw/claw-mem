"""Temporal ordering graph — edges based on chronological order."""

import bisect
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TemporalGraph:
    """Temporal ordering graph with chronological adjacency."""

    def __init__(self):
        self._nodes: Dict[str, Dict] = {}
        self._timeline: List[tuple] = []  # (timestamp, node_id)

    def add_node(self, memory_id: str, timestamp: float) -> None:
        """Add a node with timestamp, maintaining chronological order."""
        self._nodes[memory_id] = {"timestamp": timestamp}
        bisect.insort(self._timeline, (timestamp, memory_id))

    def get_before(self, timestamp: float, limit: int = 10) -> List[str]:
        """Get memories before a given timestamp."""
        results = []
        for ts, nid in self._timeline:
            if ts < timestamp:
                results.append(nid)
        return results[-limit:]

    def get_after(self, timestamp: float, limit: int = 10) -> List[str]:
        """Get memories after a given timestamp."""
        results = []
        for ts, nid in self._timeline:
            if ts > timestamp:
                results.append(nid)
                if len(results) >= limit:
                    break
        return results

    def get_range(self, start: float, end: float) -> List[str]:
        """Get memories within a time range."""
        return [
            nid for ts, nid in self._timeline
            if start <= ts <= end
        ]

    def get_recent(self, limit: int = 10) -> List[str]:
        """Get most recent memories."""
        return [nid for _, nid in self._timeline[-limit:]]

    def count(self) -> int:
        return len(self._nodes)
