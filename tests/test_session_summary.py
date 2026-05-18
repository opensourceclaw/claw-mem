"""Tests for SessionSummaryGenerator (v3.0.0-rc.2)."""

import pytest
from claw_mem.cms.session_summary import SessionSummaryGenerator
from claw_mem.cms.compression_result import SessionSummary


class TestSessionSummaryGenerator:
    def setup_method(self):
        self.gen = SessionSummaryGenerator()

    def test_generate_key_points(self):
        memories = [
            {"id": "1", "content": "We decided to use PostgreSQL"},
            {"id": "2", "content": "I prefer dark mode for the UI"},
            {"id": "3", "content": "Implement the REST API endpoint"},
            {"id": "4", "content": "Hello, how are you?"},
        ]
        summary = self.gen.generate("s1", memories, "key_points")
        assert isinstance(summary, SessionSummary)
        assert summary.session_id == "s1"
        assert len(summary.decisions) >= 1
        assert len(summary.preferences) >= 1
        assert len(summary.actions) >= 1
        assert summary.memory_count == 4

    def test_generate_chronological(self):
        memories = [
            {"id": "1", "content": "Start development"},
            {"id": "2", "content": "Fix bug in code"},
        ]
        summary = self.gen.generate("s2", memories, "chronological")
        assert summary.session_id == "s2"
        assert len(summary.overview) > 0

    def test_generate_default_strategy(self):
        memories = [{"id": "1", "content": "test"}]
        summary = self.gen.generate("s3", memories)
        assert summary.session_id == "s3"

    def test_empty_memories(self):
        summary = self.gen.generate("s4", [], "key_points")
        assert summary.decisions == []
        assert summary.preferences == []

    def test_token_count(self):
        memories = [
            {"id": "1", "content": "hello world test message here"},
        ]
        summary = self.gen.generate("s5", memories)
        assert summary.token_count > 0

    def test_decisions_chinese(self):
        memories = [{"id": "1", "content": "我们决定使用PostgreSQL数据库"}]
        summary = self.gen.generate("s6", memories, "key_points")
        assert len(summary.decisions) >= 1

    def test_preferences_chinese(self):
        memories = [{"id": "1", "content": "我喜欢中文回复"}]
        summary = self.gen.generate("s7", memories, "key_points")
        assert len(summary.preferences) >= 1

    def test_actions_chinese(self):
        memories = [{"id": "1", "content": "需要实现新的API接口"}]
        summary = self.gen.generate("s8", memories, "key_points")
        assert len(summary.actions) >= 1

    def test_summary_to_dict(self):
        summary = SessionSummary("s1", "Overview", ["D1"], ["P1"], ["A1"], 50, 10)
        d = summary.to_dict()
        assert d["session_id"] == "s1"
        assert d["overview"] == "Overview"
        assert d["decisions"] == ["D1"]
        assert "decisions" in d

    def test_build_overview(self):
        memories = [{"id": "1", "content": "x"}]
        overview = self.gen._build_overview(memories, [], [], [])
        assert "memories" in overview.lower()

    def test_mixed_content(self):
        memories = [
            {"id": "1", "content": "We decided on Redis, I prefer Python, and will implement caching"},
        ]
        summary = self.gen.generate("s9", memories, "key_points")
        # Should match at least 2 categories
        total = len(summary.decisions) + len(summary.preferences) + len(summary.actions)
        assert total >= 2
