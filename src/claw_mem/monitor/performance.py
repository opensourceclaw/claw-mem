# Copyright 2026 Peter Cheng
"""Performance monitor with latency histogram and hit-rate tracking (v2.19.0)."""

import time
import threading
import os
from collections import defaultdict
from typing import Dict, List


class PerformanceMonitor:
    """Tracks search latency, cache performance, and memory usage.

    Thread-safe for concurrent search recording.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._latencies: List[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        self._search_count = 0
        self._total_latency = 0.0
        self._min_latency = float("inf")
        self._max_latency = 0.0
        self._start_time = time.time()

    def record_search(self, latency_ms: float) -> None:
        with self._lock:
            self._search_count += 1
            self._latencies.append(latency_ms)
            self._total_latency += latency_ms
            if latency_ms < self._min_latency:
                self._min_latency = latency_ms
            if latency_ms > self._max_latency:
                self._max_latency = latency_ms

    def record_cache_hit(self) -> None:
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self._cache_misses += 1

    def get_stats(self) -> Dict:
        with self._lock:
            latencies = sorted(self._latencies) if self._latencies else [0]
            n = len(latencies)

            def percentile(p):
                idx = int(n * p / 100)
                return latencies[min(idx, n - 1)]

            return {
                "search_count": self._search_count,
                "avg_latency_ms": round(self._total_latency / max(1, n), 3),
                "min_latency_ms": round(
                    self._min_latency if self._min_latency != float("inf") else 0, 3
                ),
                "max_latency_ms": round(self._max_latency, 3),
                "p50_latency_ms": round(percentile(50), 3),
                "p95_latency_ms": round(percentile(95), 3),
                "p99_latency_ms": round(percentile(99), 3),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": (
                    self._cache_hits / max(1, self._cache_hits + self._cache_misses)
                ),
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "memory_mb": round(self._memory_usage_mb(), 2),
            }

    def _memory_usage_mb(self) -> float:
        try:
            import psutil

            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def reset(self) -> None:
        with self._lock:
            self._latencies.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._search_count = 0
            self._total_latency = 0.0
            self._min_latency = float("inf")
            self._max_latency = 0.0
            self._start_time = time.time()
