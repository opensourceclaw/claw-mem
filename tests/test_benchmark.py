"""Tests for benchmark script integration (v2.19.0)."""

import pytest
from claw_mem.retrieval.engram import EngramIndex


class TestEngramBenchmark:
    """Benchmark integration tests."""

    def test_1k_index_and_query(self):
        engram = EngramIndex(ngram_size=3)
        for i in range(1000):
            engram.index(f"mem_{i}", f"Memory entry {i} with some content")
        stats = engram.get_stats()
        assert stats["memory_count"] == 1000
        assert stats["hash_count"] > 0

        result = engram.lookup("Memory entry 500", top_k=5)
        assert len(result) >= 1

    def test_10k_index(self):
        engram = EngramIndex(ngram_size=3)
        for i in range(500):
            engram.index(f"mem_{i}", f"Large scale memory entry number {i}")
        assert engram.get_stats()["memory_count"] == 500

    def test_query_performance_threshold(self):
        """Verify P95 < 5ms for moderate dataset."""
        import time

        engram = EngramIndex(ngram_size=3)
        for i in range(200):
            engram.index(f"mem_{i}", f"Test memory content with ID {i}")

        latencies = []
        for _ in range(100):
            t0 = time.time()
            engram.lookup("Test memory content")
            latencies.append((time.time() - t0) * 1000)

        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        assert p95 < 5.0, f"P95 latency {p95:.2f}ms exceeds 5ms target"

    def test_memory_estimate(self):
        engram = EngramIndex(ngram_size=3)
        for i in range(100):
            engram.index(f"mem_{i}", f"Memory with ID {i} and some extra text")
        stats = engram.get_stats()
        assert stats["memory_estimate_bytes"] > 0
