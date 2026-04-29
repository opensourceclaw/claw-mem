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
Query Cache for claw-mem v2.5.0
LRU cache with TTL for search results
"""

import time
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from collections import OrderedDict
from dataclasses import dataclass
import threading


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    results: List[Dict]
    timestamp: float
    access_count: int = 0


class QueryCache:
    """LRU Cache with TTL for query results

    Features:
    - LRU eviction
    - TTL expiration
    - Access frequency tracking
    - Thread-safe operations
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: float = 300.0,
        min_access_count: int = 2
    ):
        """Initialize cache

        Args:
            max_size: Maximum number of entries
            ttl_seconds: Time-to-live in seconds
            min_access_count: Minimum accesses before frequency boost
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.min_access_count = min_access_count

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Stats
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, top_k: int = 10) -> str:
        """Generate cache key from query"""
        key_data = f"{query.lower().strip()}:{top_k}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, top_k: int = 10) -> Optional[List[Dict]]:
        """Get cached results

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Cached results or None
        """
        key = self._make_key(query, top_k)

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry.timestamp > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None

            # Update access order (move to end)
            self._cache.move_to_end(key)
            entry.access_count += 1

            self._hits += 1
            return entry.results

    def put(self, query: str, results: List[Dict], top_k: int = 10):
        """Cache results

        Args:
            query: Search query
            results: Search results
            top_k: Number of results
        """
        key = self._make_key(query, top_k)

        with self._lock:
            # Evict if needed
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            # Store
            self._cache[key] = CacheEntry(
                results=results,
                timestamp=time.time(),
                access_count=1
            )

    def invalidate(self, query: Optional[str] = None):
        """Invalidate cache

        Args:
            query: Specific query to invalidate, or None for all
        """
        with self._lock:
            if query is None:
                self._cache.clear()
            else:
                key = self._make_key(query)
                self._cache.pop(key, None)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Statistics dictionary
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds
            }

    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            now = time.time()
            expired = [
                key for key, entry in self._cache.items()
                if now - entry.timestamp > self.ttl_seconds
            ]
            for key in expired:
                del self._cache[key]


# Global cache instance
_query_cache: Optional[QueryCache] = None


def get_query_cache(
    max_size: int = 1000,
    ttl_seconds: float = 300.0
) -> QueryCache:
    """Get global query cache instance"""
    global _query_cache

    if _query_cache is None:
        _query_cache = QueryCache(
            max_size=max_size,
            ttl_seconds=ttl_seconds
        )

    return _query_cache
