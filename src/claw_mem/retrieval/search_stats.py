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
Search Statistics Tracker for claw-mem v2.9.0

Real-time monitoring of search accuracy, latency, and throughput.
"""

import time
import threading
from typing import Any, Dict, List, Optional
from collections import deque


class SearchStats:
    """Real-time search performance statistics tracker.

    Tracks latency percentiles (P50/P95/P99), cache hit rates,
    query throughput, and accuracy feedback.

    Usage:
        stats = SearchStats()
        stats.record_search(latency_ms=5.2, cache_hit=False)
        stats.record_accuracy_feedback(relevant_count=8, total=10)
        print(stats.get_stats())
    """

    def __init__(self, max_history: int = 1000):
        """Initialize stats tracker.

        Args:
            max_history: Maximum number of latency records to keep
        """
        self.max_history = max_history
        self._lock = threading.Lock()

        # Latency tracking
        self._latencies: deque = deque(maxlen=max_history)

        # Counters
        self.total_searches: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0

        # Accuracy tracking
        self.total_relevant: int = 0
        self.total_results: int = 0
        self.accuracy_samples: int = 0

    def record_search(self, latency_ms: float, cache_hit: bool = False):
        """Record a search operation.

        Args:
            latency_ms: Search latency in milliseconds
            cache_hit: Whether the result was served from cache
        """
        with self._lock:
            self.total_searches += 1
            self._latencies.append(latency_ms)
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

    def record_accuracy_feedback(self, relevant_count: int, total: int):
        """Record search accuracy feedback.

        Args:
            relevant_count: Number of relevant results
            total: Total number of results returned
        """
        if total > 0:
            with self._lock:
                self.total_relevant += relevant_count
                self.total_results += total
                self.accuracy_samples += 1

    def get_latency_percentile(self, p: float) -> float:
        """Calculate latency percentile.

        Args:
            p: Percentile (0-100, e.g. 50 for P50, 95 for P95)

        Returns:
            Latency in ms at the given percentile
        """
        with self._lock:
            if not self._latencies:
                return 0.0
            sorted_lat = sorted(self._latencies)
            index = int(len(sorted_lat) * p / 100)
            index = min(index, len(sorted_lat) - 1)
            return sorted_lat[index]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive search statistics.

        Returns:
            Dict with latency, cache, accuracy, and throughput stats
        """
        with self._lock:
            total = self.total_searches
            cache_hit_rate = (
                (self.cache_hits / total * 100) if total > 0 else 0.0
            )
            accuracy = (
                (self.total_relevant / self.total_results * 100)
                if self.total_results > 0 else 0.0
            )

            latencies = list(self._latencies)
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            sorted_lat = sorted(latencies) if latencies else [0]

            def _pct(p):
                if not sorted_lat:
                    return 0.0
                idx = min(int(len(sorted_lat) * p / 100), len(sorted_lat) - 1)
                return sorted_lat[idx]

            return {
                "total_searches": total,
                "latency": {
                    "avg_ms": round(avg_latency, 2),
                    "min_ms": round(sorted_lat[0], 2) if sorted_lat else 0.0,
                    "max_ms": round(sorted_lat[-1], 2) if sorted_lat else 0.0,
                    "p50_ms": round(_pct(50), 2),
                    "p95_ms": round(_pct(95), 2),
                    "p99_ms": round(_pct(99), 2),
                },
                "cache": {
                    "hits": self.cache_hits,
                    "misses": self.cache_misses,
                    "hit_rate_pct": round(cache_hit_rate, 1),
                },
                "accuracy": {
                    "avg_pct": round(accuracy, 1),
                    "samples": self.accuracy_samples,
                    "total_relevant": self.total_relevant,
                    "total_results": self.total_results,
                },
            }

    def reset(self):
        """Reset all statistics."""
        with self._lock:
            self._latencies.clear()
            self.total_searches = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.total_relevant = 0
            self.total_results = 0
            self.accuracy_samples = 0


# Global stats instance
_search_stats: Optional[SearchStats] = None


def get_search_stats() -> SearchStats:
    """Get global search statistics tracker."""
    global _search_stats
    if _search_stats is None:
        _search_stats = SearchStats()
    return _search_stats


__all__ = [
    'SearchStats',
    'get_search_stats',
]
