"""TTL cache with statistics for claw-mem v3.4.0.

Provides a thread-safe time-to-live cache with automatic
expiration, manual invalidation, and hit/miss statistics.
"""

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """A cache entry with TTL support.

    Attributes:
        value: The cached value.
        created_at: Unix timestamp when the entry was created.
        ttl: Time-to-live in seconds. -1 means no expiry.
    """

    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: float = 300.0

    def is_expired(self) -> bool:
        """Check if the entry has expired.

        Returns:
            True if the TTL has elapsed.
        """
        if self.ttl < 0:
            return False
        return time.time() - self.created_at > self.ttl


class TTLCache:
    """Thread-safe TTL cache with statistics.

    Automatically evicts expired entries on access and supports
    manual invalidation. Tracks hit/miss/eviction counts.

    Attributes:
        default_ttl: Default TTL in seconds for new entries.
        max_size: Maximum number of entries before eviction.

    Example:
        >>> cache = TTLCache(default_ttl=60, max_size=100)
        >>> cache.set("key", "value")
        >>> cache.get("key")
        'value'
        >>> cache.get_stats()
        {'hits': 1, 'misses': 0, 'evictions': 0, 'size': 1}
    """

    def __init__(
        self, default_ttl: float = 300.0, max_size: int = 1000
    ) -> None:
        """Initialize the TTL cache.

        Args:
            default_ttl: Default TTL for entries in seconds.
            max_size: Maximum cache capacity.
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = Lock()
        self._stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache.

        Returns None if the key is missing or the entry has expired.

        Args:
            key: The cache key.

        Returns:
            Cached value or None.
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None
            if entry.is_expired():
                del self._cache[key]
                self._stats["evictions"] += 1
                self._stats["misses"] += 1
                return None
            self._stats["hits"] += 1
            return entry.value

    def set(
        self, key: str, value: Any, ttl: Optional[float] = None
    ) -> None:
        """Store a value in the cache.

        If the cache is at capacity, no eviction is performed
        (entries are only evicted on expiry or manual invalidation).

        Args:
            key: The cache key.
            value: The value to store.
            ttl: Optional TTL override. Uses default_ttl if None.
        """
        with self._lock:
            ttl_value = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(
                value=value, ttl=ttl_value
            )

    def invalidate(self, key: str) -> bool:
        """Remove a key from the cache.

        Args:
            key: The cache key to remove.

        Returns:
            True if the key was found and removed.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with hits, misses, evictions, and current size.
        """
        with self._lock:
            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "size": len(self._cache),
            }
