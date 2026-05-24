"""
HippocampalStore — fast, short-term memory with LRU cache and TTL.

Simulates the hippocampus: rapid encoding, temporary storage,
importance tagging for consolidation to neocortex.
"""

import math
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class Memory:
    """A single memory entry in the dual system.

    Attributes:
        memory_id: Unique identifier.
        content: Memory content.
        memory_type: Type (episodic, semantic, procedural).
        importance: Importance score for consolidation priority.
        created_at: Creation timestamp.
        ttl_seconds: Time-to-live (hippocampal only).
        access_count: Number of times retrieved.
        last_accessed: Last access timestamp.
        metadata: Additional metadata.
    """

    memory_id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    memory_type: str = "episodic"
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 86400
    access_count: int = 0
    last_accessed: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if this memory's TTL has expired."""
        if self.ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Age of this memory in seconds."""
        return time.time() - self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "created_at": self.created_at,
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "metadata": self.metadata,
        }


class HippocampalStore:
    """Fast, short-term memory store with LRU cache and TTL.

    Simulates hippocampal function:
    - O(1) store and retrieve via dict + OrderedDict LRU
    - Automatic TTL expiration
    - Importance tagging for consolidation priority
    - Thread-safe operations

    Usage::

        store = HippocampalStore()
        mid = store.store(Memory(content="Important fact", importance=0.8))
        results = store.retrieve("fact")
    """

    def __init__(self, capacity: int = 10000, ttl_seconds: int = 86400,
                 lru_cache_size: int = 1000):
        self._capacity = capacity
        self._ttl_seconds = ttl_seconds
        self._lru_cache_size = lru_cache_size
        self._store: Dict[str, Memory] = {}
        self._lru: OrderedDict = OrderedDict()
        self._lock = threading.RLock()

    def store(self, memory: Memory) -> str:
        """Store a memory entry. Evicts LRU if at capacity.

        Args:
            memory: Memory to store.

        Returns:
            The memory_id.
        """
        with self._lock:
            if len(self._store) >= self._capacity:
                self._evict_lru()

            if memory.ttl_seconds <= 0:
                memory.ttl_seconds = self._ttl_seconds

            self._store[memory.memory_id] = memory
            self._update_lru(memory.memory_id)
            return memory.memory_id

    def retrieve(self, query: str, limit: int = 10) -> List[Memory]:
        """Retrieve memories matching a query.

        Simple keyword-based search in hippocampal store.
        Expired entries are automatically removed.

        Args:
            query: Search query string.
            limit: Maximum results.

        Returns:
            List of matching Memory objects.
        """
        with self._lock:
            self._cleanup_expired()
            query_lower = query.lower()
            results = []
            for mem in self._store.values():
                if query_lower in mem.content.lower():
                    mem.access_count += 1
                    mem.last_accessed = time.time()
                    self._update_lru(mem.memory_id)
                    results.append(mem)

            # Sort by importance * recency
            now = time.time()
            results.sort(
                key=lambda m: (m.importance * 5.0) + (1.0 / max(m.age_seconds, 1)),
                reverse=True,
            )
            return results[:limit]

    def mark_for_consolidation(self, memory_id: str, importance: float) -> bool:
        """Mark a memory with importance for consolidation.

        Args:
            memory_id: The memory to mark.
            importance: Importance score (0.0-1.0).

        Returns:
            True if the memory was found and updated.
        """
        with self._lock:
            mem = self._store.get(memory_id)
            if mem is None:
                return False
            mem.importance = max(mem.importance, importance)
            return True

    def get_pending_consolidation(self, min_importance: float = 0.0,
                                  limit: int = 100) -> List[Memory]:
        """Get memories queued for consolidation.

        Returns memories sorted by importance descending.

        Args:
            min_importance: Minimum importance threshold.
            limit: Maximum memories to return.

        Returns:
            List of Memory objects ready for consolidation.
        """
        with self._lock:
            candidates = [m for m in self._store.values()
                          if m.importance >= min_importance]
            candidates.sort(key=lambda m: m.importance, reverse=True)
            return candidates[:limit]

    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a single memory by ID."""
        with self._lock:
            mem = self._store.get(memory_id)
            if mem and not mem.is_expired:
                mem.access_count += 1
                mem.last_accessed = time.time()
                self._update_lru(memory_id)
                return mem
            return None

    def remove(self, memory_id: str) -> bool:
        """Remove a memory. Returns True if removed."""
        with self._lock:
            if memory_id in self._store:
                del self._store[memory_id]
                self._lru.pop(memory_id, None)
                return True
            return False

    def remove_batch(self, memory_ids: List[str]) -> int:
        """Remove multiple memories. Returns count removed."""
        count = 0
        for mid in memory_ids:
            if self.remove(mid):
                count += 1
        return count

    def size(self) -> int:
        """Current number of stored memories."""
        return len(self._store)

    def clear(self) -> None:
        """Clear all stored memories."""
        with self._lock:
            self._store.clear()
            self._lru.clear()

    # ── Internal ────────────────────────────────────────────────────────────────

    def _update_lru(self, memory_id: str) -> None:
        """Update LRU tracking for a memory."""
        self._lru.pop(memory_id, None)
        self._lru[memory_id] = True
        if len(self._lru) > self._lru_cache_size * 2:
            # Trim old entries from LRU
            while len(self._lru) > self._lru_cache_size:
                self._lru.popitem(last=False)

    def _evict_lru(self) -> None:
        """Evict the least recently used memory."""
        if self._lru:
            oldest, _ = self._lru.popitem(last=False)
            self._store.pop(oldest, None)

    def _cleanup_expired(self) -> int:
        """Remove all expired memories. Returns count removed."""
        expired = [mid for mid, mem in self._store.items() if mem.is_expired]
        for mid in expired:
            self._store.pop(mid, None)
            self._lru.pop(mid, None)
        return len(expired)
