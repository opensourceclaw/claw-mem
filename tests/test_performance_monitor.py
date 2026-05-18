"""Tests for PerformanceMonitor (v2.19.0)."""

import pytest
from claw_mem.monitor.performance import PerformanceMonitor


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor."""

    def setup_method(self):
        self.pm = PerformanceMonitor()

    def test_record_search(self):
        self.pm.record_search(1.5)
        self.pm.record_search(2.0)
        self.pm.record_search(3.5)
        stats = self.pm.get_stats()
        assert stats["search_count"] == 3
        assert stats["avg_latency_ms"] > 0

    def test_record_cache_hit(self):
        self.pm.record_cache_hit()
        stats = self.pm.get_stats()
        assert stats["cache_hits"] == 1

    def test_record_cache_miss(self):
        self.pm.record_cache_miss()
        stats = self.pm.get_stats()
        assert stats["cache_misses"] == 1

    def test_cache_hit_rate(self):
        self.pm.record_cache_hit()
        self.pm.record_cache_hit()
        self.pm.record_cache_miss()
        stats = self.pm.get_stats()
        assert abs(stats["cache_hit_rate"] - 2/3) < 0.01

    def test_percentiles(self):
        for i in range(100):
            self.pm.record_search(float(i + 1))
        stats = self.pm.get_stats()
        assert "p50_latency_ms" in stats
        assert "p95_latency_ms" in stats
        assert "p99_latency_ms" in stats
        assert stats["p95_latency_ms"] >= stats["p50_latency_ms"]

    def test_min_max(self):
        self.pm.record_search(5.0)
        self.pm.record_search(1.0)
        self.pm.record_search(10.0)
        stats = self.pm.get_stats()
        assert stats["min_latency_ms"] <= 1.0
        assert stats["max_latency_ms"] >= 10.0

    def test_reset(self):
        self.pm.record_search(5.0)
        self.pm.record_cache_hit()
        self.pm.reset()
        stats = self.pm.get_stats()
        assert stats["search_count"] == 0
        assert stats["cache_hits"] == 0

    def test_stats_fields(self):
        stats = self.pm.get_stats()
        required = [
            "search_count", "avg_latency_ms", "min_latency_ms",
            "max_latency_ms", "p50_latency_ms", "p95_latency_ms",
            "p99_latency_ms", "cache_hits", "cache_misses",
            "cache_hit_rate", "uptime_seconds", "memory_mb",
        ]
        for field in required:
            assert field in stats, f"Missing field: {field}"
