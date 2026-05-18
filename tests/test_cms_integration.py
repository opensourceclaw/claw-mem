"""Integration tests for CMS Perception Layer (v3.0.0-rc.1)."""

import pytest
from claw_mem.cms import (
    CapacityMonitor, ContextWarningHook, ImportanceEvaluator,
    CapacityStats, CapacityTrend, WarningEvent, ImportanceScore,
)


class TestCMSIntegration:
    """Integration tests: CMS components working together."""

    def test_monitor_hook_integration(self):
        monitor = CapacityMonitor(memory_threshold=100, warning_level=0.0)
        hook = ContextWarningHook(monitor, cooldown_seconds=0)

        event = hook.check_and_emit()
        assert event is not None
        assert isinstance(event, WarningEvent)

    def test_evaluator_batch(self):
        evaluator = ImportanceEvaluator()
        scores = evaluator.evaluate_batch(["a", "b", "c"])
        assert len(scores) == 3
        for mid, score in scores.items():
            assert isinstance(score, ImportanceScore)
            assert score.memory_id == mid

    def test_capacity_stats_roundtrip(self):
        stats = CapacityStats(total_memories=100, total_tokens=5000,
                             by_type={"episodic": 80, "semantic": 20},
                             utilization=0.5, threshold=200)
        d = stats.to_dict()
        assert d["total_memories"] == 100
        assert d["utilization"] == 0.5

    def test_capacity_trend(self):
        trend = CapacityTrend(growth_rate=1.5, estimated_time_to_full=3600.0)
        d = trend.to_dict()
        assert d["growth_rate"] == 1.5

    def test_importance_evaluator_record_then_eval(self):
        evaluator = ImportanceEvaluator()
        evaluator.record_access("mem_1")
        evaluator.record_access("mem_1")
        evaluator.record_access("mem_1")
        evaluator.record_access("mem_1")
        evaluator.record_access("mem_1")
        score = evaluator.evaluate("mem_1")
        # 5 accesses = +0.1 boost
        assert isinstance(score, ImportanceScore)

    def test_full_perception_workflow(self):
        """Simulate a full perception workflow."""
        # 1. Monitor capacity
        monitor = CapacityMonitor(memory_threshold=100, warning_level=0.8)
        stats = monitor.get_stats()
        assert isinstance(stats, CapacityStats)

        # 2. Check if warning needed
        should_warn = monitor.should_warn(stats)
        assert isinstance(should_warn, bool)

        # 3. If warning, emit event
        if should_warn:
            hook = ContextWarningHook(monitor, cooldown_seconds=0)
            event = hook.check_and_emit()
            if event:
                d = event.to_dict()
                assert "severity" in d

        # 4. Evaluate importance
        evaluator = ImportanceEvaluator()
        score = evaluator.evaluate("test_mem")
        assert isinstance(score, ImportanceScore)
        assert 0.0 <= score.total_score <= 1.5

    def test_disabled_cms_no_errors(self):
        """CMS components should handle nil memory_manager gracefully."""
        monitor = CapacityMonitor()  # no memory_manager
        stats = monitor.get_stats()
        assert stats.total_memories == 0
