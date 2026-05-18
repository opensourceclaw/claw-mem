# Copyright 2026 Peter Cheng
"""LRU cache with TTL for query results (v2.19.0)."""

import time
import threading
from typing import Dict, List, Optional
from collections import OrderedDict


class QueryCache:
    """LRU cache with TTL expiration for query results.

    Designed for caching Engram engine lookup results (List[str] memory IDs).
    Thread-safe via internal lock.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, query: str) -> Optional[List[str]]:
        with self._lock:
            if query not in self._cache:
                self._misses += 1
                return None
            ts = self._timestamps.get(query, 0)
            if time.time() - ts > self._ttl_seconds:
                del self._cache[query]
                self._timestamps.pop(query, None)
                self._misses += 1
                return None
            self._cache.move_to_end(query)
            self._hits += 1
            return list(self._cache[query])

    def set(self, query: str, results: List[str]) -> None:
        with self._lock:
            if query in self._cache:
                self._cache.move_to_end(query)
            else:
                while len(self._cache) >= self._max_size:
                    old = self._cache.popitem(last=False)
                    self._timestamps.pop(old[0], None)
            self._cache[query] = list(results)
            self._timestamps[query] = time.time()

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        return len(self._cache)

    def stats(self) -> dict:
        return {
            "size": self.size,
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "ttl_seconds": self._ttl_seconds,
        }
