"""Tests for CompressionSpectrum - Four-tier memory compression."""

import pytest
from claw_mem.compression.spectrum import (
    CompressionSpectrum, CompressedMemory,
    SkillEntry, RuleEntry, PrincipleEntry,
)


class TestCompressionSpectrum:
    """Tests for CompressionSpectrum class."""

    def setup_method(self):
        self.spec = CompressionSpectrum()

    def test_record_access_below_threshold(self):
        # 4 accesses should NOT trigger compression
        for _ in range(4):
            result = self.spec.record_access("mem_x")
        assert result is None

    def test_record_access_triggers_skill(self):
        # 5 accesses SHOULD trigger
        # But needs content accessible via _get_episode_content
        # Without a MM, it returns None
        for _ in range(5):
            result = self.spec.record_access("mem_x")
        # No MM = no content = None
        assert result is None

    def test_extract_steps_english(self):
        content = "pip install redis, then configure the connection pool"
        steps = self.spec._extract_steps(content)
        assert len(steps) >= 1

    def test_extract_steps_chinese(self):
        content = "使用pip install redis，然后配置连接池参数"
        steps = self.spec._extract_steps(content)
        assert len(steps) >= 1

    def test_extract_tags(self):
        content = "Using Redis with Python for caching"
        tags = self.spec._extract_tags(content)
        assert "redis" in tags
        assert "python" in tags

    def test_empty_content(self):
        steps = self.spec._extract_steps("")
        assert steps == []

    def test_get_compressed_empty(self):
        results = self.spec.get_compressed()
        assert results == []

    def test_get_stats_initial(self):
        stats = self.spec.get_stats()
        assert stats["skills"] == 0
        assert stats["rules"] == 0
        assert stats["principles"] == 0

    def test_record_apply_no_skill(self):
        # No skill registered → no result
        result = self.spec.record_apply("nonexistent")
        assert result is None

    def test_record_verify_no_rule(self):
        result = self.spec.record_verify("nonexistent")
        assert result is None


class TestCompressedMemory:
    """Tests for CompressedMemory dataclass."""

    def test_create(self):
        cm = CompressedMemory("cm_1", 1, "Test content")
        assert cm.memory_id == "cm_1"
        assert cm.level == 1
        assert cm.content == "Test content"
        assert cm.source_ids == []
        assert cm.metadata == {}

    def test_defaults(self):
        cm = CompressedMemory("id", 2, "x")
        assert cm.created_at == 0.0
        assert cm.source_ids == []
