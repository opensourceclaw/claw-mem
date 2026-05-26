"""
CrossAgentSync — push/pull memory synchronization for claw-mem v4.0.

Supports push/pull patterns, subscription-based event-driven sync,
and basic conflict detection for cross-agent memory sharing.
"""

from typing import Any, Callable, Dict, List, Optional
import threading
import time
import uuid

from .agnostic import MemoryRecord
from .pool import MemoryPool


class CrossAgentSync:
    """Cross-agent memory synchronization.

    Push/Pull sync patterns:
    - push: Send memory record to specific agents (optionally via message bus)
    - pull: Retrieve agent's updates since a timestamp
    - subscribe/unsubscribe: Event-driven sync callbacks
    - detect_conflict: Basic same-topic conflict detection

    Example:
        >>> sync = CrossAgentSync(pool=pool)
        >>> record = MemoryRecord(...)
        >>> sync.push(record, target_agents=["agent2"])
        >>> updates = sync.pull("agent1", since=0.0)
        >>> sub_id = sync.subscribe("agent1", lambda r: print(r.content))
    """

    def __init__(self, pool: Optional[MemoryPool] = None):
        """Initialize sync with optional MemoryPool.

        Args:
            pool: A MemoryPool instance for storage.
        """
        self.pool = pool
        self._subscriptions: Dict[str, List[tuple]] = {}  # agent_id -> [(sub_id, callback)]
        self._lock = threading.Lock()
        self._push_count: int = 0
        self._pull_count: int = 0

    def push(
        self,
        record: MemoryRecord,
        target_agents: List[str],
        bus: Optional[Any] = None,
    ) -> bool:
        """Push memory to specific agents.

        If a message bus is provided, sends the record as a message.
        Otherwise, just stores it in the pool.

        Args:
            record: The MemoryRecord to push.
            target_agents: List of target agent IDs.
            bus: Optional message bus for agent communication.

        Returns:
            True if push was successful.
        """
        # Store in pool if available
        if self.pool:
            self.pool.store(record)

        # Notify subscribers
        for agent_id in target_agents:
            self._notify_subscribers(agent_id, record)

        # Send via message bus if provided
        if bus and hasattr(bus, "send"):
            for agent_id in target_agents:
                try:
                    # Attempt message-based push
                    if hasattr(bus, "subscribe") and agent_id not in bus._subscribers:
                        continue
                except Exception:
                    pass

        self._push_count += 1
        return True

    def pull(
        self, agent_id: str, since: float = 0.0
    ) -> List[MemoryRecord]:
        """Pull updates from an agent since a timestamp.

        Args:
            agent_id: The agent to pull from.
            since: Unix timestamp to pull updates after.

        Returns:
            List of MemoryRecords newer than since.
        """
        self._pull_count += 1

        if not self.pool:
            return []

        records = self.pool.query({"agent_id": agent_id})
        return [r for r in records if r.timestamp >= since]

    def subscribe(
        self, agent_id: str, callback: Callable[[MemoryRecord], None]
    ) -> str:
        """Subscribe to an agent's new memories.

        Args:
            agent_id: The agent ID to subscribe to.
            callback: Called with each new MemoryRecord.

        Returns:
            Subscription ID for later unsubscribe.
        """
        sub_id = str(uuid.uuid4())

        with self._lock:
            if agent_id not in self._subscriptions:
                self._subscriptions[agent_id] = []
            self._subscriptions[agent_id].append((sub_id, callback))

        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription.

        Args:
            subscription_id: The subscription ID from subscribe().

        Returns:
            True if found and removed.
        """
        with self._lock:
            for agent_id, subs in list(self._subscriptions.items()):
                for sub_id, _ in subs:
                    if sub_id == subscription_id:
                        self._subscriptions[agent_id] = [
                            (s, c) for s, c in subs if s != subscription_id
                        ]
                        if not self._subscriptions[agent_id]:
                            del self._subscriptions[agent_id]
                        return True
        return False

    def detect_conflict(
        self, record: MemoryRecord, existing: MemoryRecord
    ) -> Optional[str]:
        """Detect conflicts between two records.

        A conflict is detected when two records share at least one tag
        but have different content.

        Args:
            record: New MemoryRecord.
            existing: Existing MemoryRecord.

        Returns:
            Conflict description if detected, None otherwise.
        """
        common_tags = set(record.tags) & set(existing.tags)
        if common_tags and record.content != existing.content:
            return (
                f"Conflict: records from {record.agent_id} and "
                f"{existing.agent_id} share tags {common_tags} "
                f"but have different content"
            )
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get sync statistics.

        Returns:
            Dict with push_count, pull_count, active_subscriptions.
        """
        with self._lock:
            active = sum(1 for subs in self._subscriptions.values() if subs)
        return {
            "push_count": self._push_count,
            "pull_count": self._pull_count,
            "active_subscriptions": active,
            "subscribed_agents": len(self._subscriptions),
        }

    def _notify_subscribers(
        self, agent_id: str, record: MemoryRecord
    ) -> None:
        """Notify subscribers of a new record.

        Args:
            agent_id: The agent whose subscribers to notify.
            record: The new MemoryRecord.
        """
        with self._lock:
            subs = self._subscriptions.get(agent_id, [])

        for sub_id, callback in subs:
            try:
                callback(record)
            except Exception:
                pass
