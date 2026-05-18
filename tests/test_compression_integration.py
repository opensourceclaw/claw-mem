"""Integration tests for CMS Phase 2 compression (v3.0.0-rc.2)."""

import pytest
from claw_mem.cms.session_summary import SessionSummaryGenerator
from claw_mem.cms.memory_deduplicator import MemoryDeduplicator
from claw_mem.cms.compression_strategy import CompressionStrategySelector
from claw_mem.cms.compression_result import (
    CompressionResult, CompressionPlan, SessionSummary, DeduplicationResult,
)


class TestCompressionIntegration:
    def test_full_pipeline(self):
        """Simulate: utilization check → strategy → summary."""
        # Phase 1: check capacity
        utilization = 0.85

        # Phase 2: select strategy
        selector = CompressionStrategySelector()
        plan = selector.select(utilization, total_memories=100)
        assert plan.strategy == "balanced"

        # Phase 2: generate summary
        gen = SessionSummaryGenerator()
        memories = [
            {"id": "1", "content": "We decided to use PostgreSQL"},
            {"id": "2", "content": "I prefer dark mode"},
            {"id": "3", "content": "Implement caching layer"},
        ]
        summary = gen.generate("s1", memories, plan.strategy if plan.strategy != "balanced" else "key_points")
        assert summary.memory_count == 3

    def test_dedup_then_summary(self):
        gen = SessionSummaryGenerator()
        dedup = MemoryDeduplicator(similarity_threshold=0.6)
        memories = [
            {"id": "1", "content": "hello world test message one"},
            {"id": "2", "content": "hello world test message two"},
            {"id": "3", "content": "completely different content here"},
        ]
        summary = gen.generate("s1", memories)
        assert summary.session_id == "s1"

    def test_compression_result_to_dict(self):
        plan = CompressionPlan("balanced", 0.85, 0.5, ["summarize"], 5000)
        summary = SessionSummary("s1", "Test", ["D1"], [], [], 100, 5)
        result = CompressionResult(
            session_id="s1", plan=plan, summary=summary,
            original_token_count=10000, final_token_count=5000,
            reduction_ratio=0.5, execution_time_ms=25.0,
        )
        d = result.to_dict()
        assert d["session_id"] == "s1"
        assert d["reduction_ratio"] == 0.5
        assert d["plan"]["strategy"] == "balanced"
        assert d["summary"] is not None

    def test_strategy_aggressive_actions(self):
        selector = CompressionStrategySelector()
        plan = selector.select(0.95, 1000)
        assert "archive_expired" in plan.suggested_actions

    def test_integration_without_summary(self):
        plan = CompressionPlan("conservative", 0.5, 0.2, ["summarize"], 100)
        result = CompressionResult(
            session_id="s1", plan=plan,
            original_token_count=1000, final_token_count=800,
            reduction_ratio=0.2, execution_time_ms=5.0,
        )
        d = result.to_dict()
        assert d["summary"] is None
        assert d["dedup"] is None
