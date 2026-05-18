"""Tests for CompressionSpectrum trigger logic (v2.18.0)."""

import pytest
from claw_mem.compression.spectrum import CompressionSpectrum


class TestCompressionTrigger:
    """Tests for access/apply/verify trigger mechanisms."""

    def test_record_access_cumulative(self):
        cs = CompressionSpectrum(access_threshold=3)
        assert cs._episode_access.get("test_id", 0) == 0
        cs.record_access("test_id")
        assert cs._episode_access["test_id"] == 1
        cs.record_access("test_id")
        assert cs._episode_access["test_id"] == 2
        cs.record_access("test_id")
        assert cs._episode_access["test_id"] == 3

    def test_record_apply_no_match(self):
        cs = CompressionSpectrum()
        result = cs.record_apply("nonexistent")
        assert result is None

    def test_record_verify_no_match(self):
        cs = CompressionSpectrum()
        result = cs.record_verify("nonexistent")
        assert result is None

    def test_threshold_is_reached_after_n(self):
        cs = CompressionSpectrum(access_threshold=2)
        cs.record_access("id_1")
        assert cs._episode_access["id_1"] == 1
        cs.record_access("id_1")
        assert cs._episode_access["id_1"] == 2  # threshold reached

    def test_different_ids_independent(self):
        cs = CompressionSpectrum(access_threshold=5)
        cs.record_access("a")
        cs.record_access("a")
        cs.record_access("b")
        assert cs._episode_access["a"] == 2
        assert cs._episode_access["b"] == 1

    def test_configure_thresholds_affects_trigger(self):
        cs = CompressionSpectrum(access_threshold=10)
        # 9 accesses, no trigger
        for _ in range(9):
            cs.record_access("mem")
        assert cs._episode_access["mem"] == 9
        # Lower threshold
        cs.configure_thresholds(access=5)
        # Should now be >= 5, but record_access still needs to be called
        cs.record_access("mem")
        assert cs._episode_access["mem"] == 10

    def test_stats_reflects_trigger_state(self):
        cs = CompressionSpectrum()
        for i in range(3):
            cs.record_access(f"mem_{i}")
        stats = cs.get_stats()
        assert stats["total_episodes_tracked"] == 3

    def test_skill_threshold_boundary(self):
        cs = CompressionSpectrum(access_threshold=5)
        # 4 accesses = below threshold
        for _ in range(4):
            result = cs.record_access("id")
            assert result is None  # no compression (no content via MM)
        # 5 accesses = threshold, but no MM so still None
        result = cs.record_access("id")
        assert cs._episode_access["id"] == 5
