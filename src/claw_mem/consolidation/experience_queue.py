"""
claw-mem v2.10.0 - Experience Queue

Priority queue for experiences awaiting weight consolidation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import heapq


@dataclass(order=True)
class QueueItem:
    """Prioritized queue item."""
    priority: float  # Higher = processed first
    experience: Any = field(compare=False)
    enqueued_at: str = field(compare=False, default="")


class ExperienceQueue:
    """Priority queue for consolidation candidates.

    Higher-priority experiences (classified as "high") are
    processed first. The queue has a max size; oldest items
    are evicted when full.
    """

    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self._queue: List[QueueItem] = []
        self._processed_count = 0

    def enqueue(self, experience: Dict[str, Any], priority: float = 0.5):
        """Add an experience to the queue.

        Args:
            experience: Experience dict
            priority: Processing priority (0-1, higher = first)
        """
        import datetime
        item = QueueItem(
            priority=-priority,  # Negate for max-heap behavior
            experience=experience,
            enqueued_at=datetime.datetime.utcnow().isoformat(),
        )
        heapq.heappush(self._queue, item)

        # Evict if over max size
        while len(self._queue) > self.max_size:
            heapq.heappop(self._queue)

    def dequeue_batch(self, batch_size: int = 8) -> List[Dict[str, Any]]:
        """Get next batch of highest-priority experiences.

        Args:
            batch_size: Number of experiences to dequeue

        Returns:
            List of experience dicts
        """
        batch = []
        for _ in range(min(batch_size, len(self._queue))):
            item = heapq.heappop(self._queue)
            batch.append(item.experience)
            self._processed_count += 1
        return batch

    def peek(self, n: int = 5) -> List[Dict[str, Any]]:
        """Peek at top N items without dequeueing."""
        return [item.experience for item in self._queue[:n]]

    @property
    def size(self) -> int:
        return len(self._queue)

    @property
    def processed(self) -> int:
        return self._processed_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self.size, "max_size": self.max_size,
            "processed": self.processed,
        }
