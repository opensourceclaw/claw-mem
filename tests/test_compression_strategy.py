"""Tests for CompressionStrategySelector (v3.0.0-rc.2)."""

import pytest
from claw_mem.cms.compression_strategy import CompressionStrategySelector
from claw_mem.cms.compression_result import CompressionPlan


class TestCompressionStrategySelector:
    def setup_method(self):
        self.selector = CompressionStrategySelector()

    def test_select_aggressive(self):
        plan = self.selector.select(utilization=0.95, total_memories=1000)
        assert plan.strategy == "aggressive"
        assert plan.target_reduction == 0.70
        assert "deduplicate" in plan.suggested_actions

    def test_select_balanced(self):
        plan = self.selector.select(utilization=0.80, total_memories=1000)
        assert plan.strategy == "balanced"
        assert plan.target_reduction == 0.50
        assert "summarize" in plan.suggested_actions

    def test_select_conservative(self):
        plan = self.selector.select(utilization=0.50, total_memories=1000)
        assert plan.strategy == "conservative"
        assert plan.target_reduction == 0.20

    def test_select_boundary_75(self):
        plan = self.selector.select(utilization=0.76, total_memories=100)
        assert plan.strategy == "balanced"

    def test_select_boundary_90(self):
        plan = self.selector.select(utilization=0.91, total_memories=100)
        assert plan.strategy == "aggressive"

    def test_plan_to_dict(self):
        plan = self.selector.select(utilization=0.85, total_memories=500)
        d = plan.to_dict()
        assert d["strategy"] in ("aggressive", "balanced", "conservative")
        assert "utilization" in d
        assert "suggested_actions" in d

    def test_estimated_token_savings(self):
        plan = self.selector.select(utilization=0.95, total_memories=1000)
        assert plan.estimated_token_savings > 0
