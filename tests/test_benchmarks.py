"""Tests for claw-mem v2.11.0 Benchmark modules."""

import pytest
from claw_mem.benchmarks import (
    RecallAtK, MRR, Precision, EvalResult, EvaluationMetrics,
    MemBench, MemoryArena, ArenaTask, ArenaTaskType,
    EvoMemory, StreamTask,
    BenchmarkRunner, BenchmarkReport,
)


class TestRecallAtK:
    def test_perfect(self):
        r = RecallAtK.calculate(["a", "b", "c", "d"], {"a", "b"}, k=3)
        assert r == 1.0

    def test_partial(self):
        r = RecallAtK.calculate(["a", "d", "e", "b"], {"a", "b"}, k=2)
        assert r == 0.5

    def test_none(self):
        r = RecallAtK.calculate(["x", "y"], {"a", "b"}, k=5)
        assert r == 0.0

    def test_empty_relevant(self):
        r = RecallAtK.calculate(["a"], set(), k=5)
        assert r == 1.0

    def test_calculate_all(self):
        results = RecallAtK.calculate_all(
            ["a", "c", "b", "d"], {"a", "b"}, ks=[1, 3, 5])
        assert len(results) == 3
        assert results[0].k == 1
        assert results[1].metric == "recall"


class TestMRR:
    def test_first_position(self):
        r = MRR.calculate(["a", "b", "c"], {"a"})
        assert r == 1.0

    def test_third_position(self):
        r = MRR.calculate(["x", "y", "a"], {"a"})
        assert r == pytest.approx(1 / 3, 0.01)

    def test_not_found(self):
        r = MRR.calculate(["x", "y", "z"], {"a"})
        assert r == 0.0

    def test_batch(self):
        queries = [
            {"returned": ["a", "b"], "relevant": {"a"}},
            {"returned": ["x", "a"], "relevant": {"a"}},
        ]
        r = MRR.calculate_batch(queries)
        assert r > 0.5


class TestPrecision:
    def test_all_relevant(self):
        r = Precision.calculate(["a", "b", "c"], {"a", "b", "c"}, k=3)
        assert r == 1.0

    def test_half_relevant(self):
        r = Precision.calculate(["a", "x", "b", "y"], {"a", "b"}, k=4)
        assert r == 0.5

    def test_empty(self):
        r = Precision.calculate([], {"a"}, k=5)
        assert r == 0.0


class TestMemBench:
    def test_evaluate_retrieval(self):
        mb = MemBench()
        metrics = mb.evaluate_retrieval(["a", "c", "b", "d"], {"a", "b"})
        assert metrics.get("recall@1") > 0

    def test_evaluate_test_time_learning(self):
        mb = MemBench()
        r = mb.evaluate_test_time_learning(0.75)
        assert r["few_shot_accuracy"] == 0.75

    def test_evaluate_long_range(self):
        mb = MemBench()
        r = mb.evaluate_long_range([0.8, 0.9, 0.7])
        assert r["avg_consistency"] == 0.8

    def test_evaluate_forgetting(self):
        mb = MemBench()
        r = mb.evaluate_forgetting({"a", "b"}, {"b"}, {"a"})
        assert r["residue_count"] == 0
        assert r["forget_rate"] == 1.0


class TestMemoryArena:
    def test_add_and_run_task(self):
        arena = MemoryArena()
        arena.add_task(ArenaTask("T1", ArenaTaskType.WEB_NAVIGATION, "Test", steps=3))
        results = arena.run()
        assert len(results) == 1
        assert results[0].completed is True

    def test_run_multiple_tasks(self):
        arena = MemoryArena()
        for t in ArenaTaskType:
            arena.add_task(ArenaTask(t.value, t, f"Test {t.value}", steps=2))
        results = arena.run()
        assert len(results) == 4

    def test_get_summary(self):
        arena = MemoryArena()
        arena.add_task(ArenaTask("T1", ArenaTaskType.FORMAL_REASONING, "Test"))
        arena.run()
        s = arena.get_summary()
        assert s["total_tasks"] == 1
        assert s["completed"] == 1


class TestEvoMemory:
    def test_run_streaming(self):
        evo = EvoMemory()
        evo.add_task(StreamTask("E1", "Retrieval task", "search"))
        evo.add_task(StreamTask("E2", "Update task", "write"))
        results = evo.run()
        assert len(results) == 2

    def test_get_summary(self):
        evo = EvoMemory()
        evo.add_task(StreamTask("E1", "Test", "search"))
        evo.run()
        s = evo.get_summary()
        assert s["total_tasks"] == 1
        assert s["avg_accuracy"] > 0

    def test_exprag_baseline(self):
        evo = EvoMemory()
        evo.set_baseline(0.4)
        evo.add_task(StreamTask("E1", "Test"))
        results = evo.run()
        assert results[0].exprag_score is not None


class TestBenchmarkRunner:
    def test_run_all(self):
        runner = BenchmarkRunner()
        report = runner.run_all()
        assert isinstance(report, BenchmarkReport)

    def test_report_to_dict(self):
        runner = BenchmarkRunner()
        report = runner.run_all()
        d = report.to_dict()
        assert "arena" in d
        assert "membench" in d
        assert "evo_memory" in d
        assert "summary" in d

    def test_membench_mrr_in_summary(self):
        runner = BenchmarkRunner()
        report = runner.run_all()
        assert report.summary["membench_mrr"] is not None
