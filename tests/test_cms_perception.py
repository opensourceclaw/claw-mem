"""Tests for CMS Perception Layer (v3.0.0-rc.1)."""

import pytest
from claw_mem.cms.capacity_monitor import (
    CapacityMonitor,
    CapacityStats,
    CapacityTrend,
)
from claw_mem.cms.context_warning_hook import (
    ContextWarningHook,
    WarningEvent,
)
from claw_mem.cms.importance_evaluator import (
    ImportanceEvaluator,
    ImportanceScore,
    TYPE_IMPORTANCE,
)


class TestCapacityMonitor:
    """Tests for CapacityMonitor."""

    def setup_method(self):
        self.monitor = CapacityMonitor(
            token_threshold=8000,
            memory_threshold=100,
            warning_level=0.8,
        )

    def test_get_stats(self):
        stats = self.monitor.get_stats()
        assert isinstance(stats, CapacityStats)
        assert stats.total_memories >= 0
        assert stats.threshold == 100
        assert 0.0 <= stats.utilization <= 1.0

    def test_should_warn_below_threshold(self):
        assert not self.monitor.should_warn()

    def test_should_warn_with_low_threshold(self):
        m = CapacityMonitor(memory_threshold=100, warning_level=0.0)
        assert m.should_warn()

    def test_get_trend_initial(self):
        trend = self.monitor.get_trend()
        assert isinstance(trend, CapacityTrend)
        assert trend.growth_rate >= 0

    def test_check_returns_none_when_ok(self):
        result = self.monitor.check()
        assert result is None

    def test_stats_to_dict(self):
        stats = self.monitor.get_stats()
        d = stats.to_dict()
        assert "total_memories" in d
        assert "utilization" in d


class TestContextWarningHook:
    """Tests for ContextWarningHook."""

    def setup_method(self):
        self.monitor = CapacityMonitor(
            memory_threshold=100,
            warning_level=0.0,  # always trigger
        )
        self.hook = ContextWarningHook(self.monitor, cooldown_seconds=0)

    def test_emit_warning(self):
        event = self.hook.check_and_emit()
        assert event is not None
        assert isinstance(event, WarningEvent)
        assert event.severity in ("info", "warning", "critical")

    def test_on_memory_stored(self):
        # First call: store_count=1, 1%10 != 0, no check
        result = self.hook.on_memory_stored("mem_1")
        assert result is None

    def test_get_stats(self):
        stats = self.hook.get_stats()
        assert "warning_count" in stats
        assert "cooldown_seconds" in stats

    def test_warning_event_to_dict(self):
        event = WarningEvent(
            severity="warning",
            message="test",
            utilization=0.85,
            threshold=0.8,
            total_memories=10,
        )
        d = event.to_dict()
        assert d["severity"] == "warning"
        assert d["utilization"] == 0.85

    def test_determine_severity(self):
        assert self.hook._determine_severity(0.96) == "critical"
        assert self.hook._determine_severity(0.88) == "warning"
        assert self.hook._determine_severity(0.82) == "info"


class TestImportanceEvaluator:
    """Tests for ImportanceEvaluator."""

    def setup_method(self):
        self.eval = ImportanceEvaluator()

    def test_evaluate_no_mm(self):
        score = self.eval.evaluate("mem_123")
        assert isinstance(score, ImportanceScore)
        assert score.memory_id == "mem_123"
        assert score.content_type == "chat"
        assert score.base_score == 0.2

    def test_evaluate_batch(self):
        scores = self.eval.evaluate_batch(["a", "b", "c"])
        assert len(scores) == 3
        assert all(isinstance(s, ImportanceScore) for s in scores.values())

    def test_get_important_memories_empty(self):
        results = self.eval.get_important_memories()
        assert results == []

    def test_detect_type_critical(self):
        assert self.eval._detect_type("critical_rule: always inject") == "critical"

    def test_detect_type_preference(self):
        assert self.eval._detect_type("I prefer dark mode") == "preference"
        assert self.eval._detect_type("用户偏好中文") == "preference"

    def test_detect_type_decision(self):
        assert self.eval._detect_type("We decided to use PostgreSQL") == "decision"

    def test_detect_type_fact(self):
        assert self.eval._detect_type("Important: use Python 3.10") == "fact"

    def test_detect_type_task(self):
        assert self.eval._detect_type("Working on building a REST API") == "task"

    def test_record_access(self):
        self.eval.record_access("mem_1")
        self.eval.record_access("mem_1")
        assert self.eval._access_counts["mem_1"] == 2

    def test_score_to_dict(self):
        score = ImportanceScore("id", 0.5, 0.1, 0.05, 0.65, "fact")
        d = score.to_dict()
        assert d["memory_id"] == "id"
        assert d["total_score"] == 0.65

    def test_type_importance_values(self):
        assert TYPE_IMPORTANCE["critical"] == 1.0
        assert TYPE_IMPORTANCE["preference"] == 0.8
        assert TYPE_IMPORTANCE["decision"] == 0.7
        assert TYPE_IMPORTANCE["fact"] == 0.5
        assert TYPE_IMPORTANCE["chat"] == 0.2
