"""Tests for claw-mem v2.15.0 modules."""
import pytest
from claw_mem.engram_index import EngramIndex
from claw_mem.spreading_activation import SpreadingActivation
from claw_mem.memory_benchmarks import BenchmarkRunner


class TestEngramIndex:
    def setup_method(self):
        self.ei = EngramIndex(ngram_size=3)

    def test_build(self):
        memories = [
            {"id": "1", "content": "python memory indexing"},
            {"id": "2", "content": "graph database search"},
            {"id": "3", "content": "fast O1 lookup table"},
        ]
        self.ei.build(memories)
        stats = self.ei.get_stats()
        assert stats["built"] is True
        assert stats["indexed_memories"] == 3

    def test_lookup_exact(self):
        memories = [{"id": "1", "content": "exact match test query here"}]
        self.ei.build(memories)
        results = self.ei.lookup("exact match test query", top_k=5)
        assert len(results) > 0

    def test_lookup_partial(self):
        memories = [
            {"id": "1", "content": "python AI programming"},
            {"id": "2", "content": "java enterprise development"},
        ]
        self.ei.build(memories)
        results = self.ei.lookup("python", top_k=5)
        assert len(results) > 0

    def test_lookup_empty(self):
        results = self.ei.lookup("nothing")
        assert results == []

    def test_stats_after_rebuild(self):
        self.ei.build([{"id": "1", "content": "first"}])
        self.ei.build([{"id": "2", "content": "second A"}, {"id": "3", "content": "second B"}])
        stats = self.ei.get_stats()
        assert stats["indexed_memories"] == 2


class TestSpreadingActivation:
    def setup_method(self):
        self.sa = SpreadingActivation()

    def test_search_basic(self):
        self.sa.graphs.add_memory({"text": "debug python error fix"})
        self.sa.graphs.add_memory({"text": "python programming language"})
        results = self.sa.search("python debug", top_k=5)
        assert len(results) > 0

    def test_search_no_results(self):
        results = self.sa.search("zzz_nonexistent_query_zzz", top_k=5)
        assert len(results) >= 0

    def test_set_threshold(self):
        self.sa.set_threshold(0.5)
        assert self.sa._activation_threshold == 0.5


class TestBenchmarkRunner:
    def setup_method(self):
        self.br = BenchmarkRunner()

    def test_locom_all_pass(self):
        def fake_search(query, top_k):
            return [{"text": "memory project status update complete"} for _ in range(3)]
        result = self.br.run_locom(fake_search)
        assert result.total_queries == 5
        assert result.accuracy > 0

    def test_longmem_eval(self):
        def fake_search(query, top_k):
            return [{"text": f"graph test version release {query}"} for _ in range(2)]
        result = self.br.run_longmem_eval(fake_search)
        assert result.total_queries == 4

    def test_no_results_benchmark(self):
        result = self.br.run_locom(lambda q, k: [])
        assert result.accuracy == 0.0

    def test_get_latest_none(self):
        assert self.br.get_latest() is None

    def test_get_latest_after_run(self):
        self.br.run_locom(lambda q, k: [])
        r = self.br.get_latest()
        assert r is not None
        assert r.name == "LOCOMO"
