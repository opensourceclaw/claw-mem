# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
"""Tests for retrieval/search_stats.py (v2.9.0)"""

import pytest
from claw_mem.retrieval.search_stats import SearchStats, get_search_stats


class TestSearchStats:
    def test_init(self):
        stats = SearchStats()
        s = stats.get_stats()
        assert s["total_searches"] == 0
        assert s["latency"]["avg_ms"] == 0.0

    def test_record_search(self):
        stats = SearchStats()
        stats.record_search(latency_ms=5.0, cache_hit=False)
        s = stats.get_stats()
        assert s["total_searches"] == 1
        assert s["cache"]["misses"] == 1

    def test_record_cache_hit(self):
        stats = SearchStats()
        stats.record_search(latency_ms=0.5, cache_hit=True)
        s = stats.get_stats()
        assert s["cache"]["hits"] == 1
        assert s["cache"]["hit_rate_pct"] == 100.0

    def test_cache_hit_rate(self):
        stats = SearchStats()
        stats.record_search(latency_ms=5.0, cache_hit=False)
        stats.record_search(latency_ms=0.5, cache_hit=True)
        stats.record_search(latency_ms=0.3, cache_hit=True)
        s = stats.get_stats()
        assert s["cache"]["hits"] == 2
        assert s["cache"]["hit_rate_pct"] == pytest.approx(66.7, 0.1)

    def test_latency_percentiles(self):
        stats = SearchStats()
        for i in range(1, 11):
            stats.record_search(latency_ms=float(i))
        s = stats.get_stats()
        assert s["latency"]["avg_ms"] == 5.5
        assert 5.0 <= s["latency"]["p50_ms"] <= 6.0
        assert s["latency"]["p95_ms"] >= 9.0

    def test_latency_empty(self):
        stats = SearchStats()
        assert stats.get_latency_percentile(50) == 0.0

    def test_accuracy_feedback(self):
        stats = SearchStats()
        stats.record_accuracy_feedback(relevant_count=8, total=10)
        stats.record_accuracy_feedback(relevant_count=6, total=10)
        s = stats.get_stats()
        assert s["accuracy"]["samples"] == 2
        assert s["accuracy"]["avg_pct"] == 70.0

    def test_accuracy_zero(self):
        stats = SearchStats()
        stats.record_accuracy_feedback(relevant_count=0, total=0)
        s = stats.get_stats()
        assert s["accuracy"]["samples"] == 0

    def test_reset(self):
        stats = SearchStats()
        stats.record_search(latency_ms=5.0)
        stats.reset()
        s = stats.get_stats()
        assert s["total_searches"] == 0

    def test_latency_p99(self):
        stats = SearchStats()
        for i in range(100):
            stats.record_search(latency_ms=float(i + 1))
        s = stats.get_stats()
        assert s["latency"]["p99_ms"] >= 99.0

    def test_global_instance(self):
        s1 = get_search_stats()
        s2 = get_search_stats()
        assert s1 is s2
