"""Tests for CompressionSpectrum configuration (v2.18.0)."""

import pytest
from claw_mem.compression.spectrum import CompressionSpectrum


class TestCompressionConfig:
    """Tests for default configuration and custom thresholds."""

    def test_create_default(self):
        cs = CompressionSpectrum()
        assert cs._skill_access_threshold == 5
        assert cs._rule_apply_threshold == 3
        assert cs._principle_verify_threshold == 2

    def test_create_custom_thresholds(self):
        cs = CompressionSpectrum(
            access_threshold=3,
            apply_threshold=5,
            verify_threshold=1,
        )
        assert cs._skill_access_threshold == 3
        assert cs._rule_apply_threshold == 5
        assert cs._principle_verify_threshold == 1

    def test_get_stats_has_enabled(self):
        cs = CompressionSpectrum()
        stats = cs.get_stats()
        assert stats["enabled"] is True
        assert "thresholds" in stats
        assert stats["thresholds"]["skill_access"] == 5


class TestConfigureThresholds:
    """Tests for runtime threshold configuration."""

    def test_configure_all(self):
        cs = CompressionSpectrum()
        cs.configure_thresholds(access=10, apply=6, verify=4)
        assert cs._skill_access_threshold == 10
        assert cs._rule_apply_threshold == 6
        assert cs._principle_verify_threshold == 4

    def test_configure_partial(self):
        cs = CompressionSpectrum()
        cs.configure_thresholds(access=8)
        assert cs._skill_access_threshold == 8
        assert cs._rule_apply_threshold == 3  # unchanged

    def test_configure_none(self):
        cs = CompressionSpectrum(access_threshold=7)
        cs.configure_thresholds()
        assert cs._skill_access_threshold == 7  # unchanged

    def test_configure_single_param(self):
        cs = CompressionSpectrum()
        cs.configure_thresholds(verify=1)
        assert cs._principle_verify_threshold == 1
        assert cs._skill_access_threshold == 5  # unchanged
