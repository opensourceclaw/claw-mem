"""Tests for claw-mem v3.0.0 Temporal module."""

import pytest
from datetime import datetime, timezone, timedelta
from claw_mem.temporal import TimeWeightCalculator, TimeWeightConfig


class TestTimeWeightCalculator:
    def test_exponential_decay_recent(self):
        calc = TimeWeightCalculator()
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=1)).isoformat()
        weight = calc.calculate(ts, now)
        assert weight > 0.9  # Recent = high weight

    def test_exponential_decay_old(self):
        calc = TimeWeightCalculator()
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=365)).isoformat()
        weight = calc.calculate(ts, now)
        assert weight < 0.3  # Old = low weight

    def test_linear_decay(self):
        calc = TimeWeightCalculator(TimeWeightConfig(decay_type="linear"))
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=182)).isoformat()
        weight = calc.calculate(ts, now)
        assert 0.4 < weight < 0.7  # Mid-point

    def test_step_decay_recent(self):
        calc = TimeWeightCalculator(TimeWeightConfig(decay_type="step"))
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=3)).isoformat()
        weight = calc.calculate(ts, now)
        assert weight == 1.0

    def test_step_decay_old(self):
        cfg = TimeWeightConfig(decay_type="step", recent_window_days=7)
        calc = TimeWeightCalculator(cfg)
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=500)).isoformat()
        weight = calc.calculate(ts, now)
        assert weight == cfg.min_weight

    def test_min_weight_floor(self):
        cfg = TimeWeightConfig(half_life_days=1.0, min_weight=0.1)
        calc = TimeWeightCalculator(cfg)
        now = datetime.now(timezone.utc)
        ts = (now - timedelta(days=100)).isoformat()
        weight = calc.calculate(ts, now)
        assert weight >= cfg.min_weight

    def test_calculate_with_date_string(self):
        calc = TimeWeightCalculator()
        weight = calc.calculate("2024-01-01")
        assert 0.0 <= weight <= 1.0

    def test_calculate_with_iso_string(self):
        calc = TimeWeightCalculator()
        weight = calc.calculate("2024-01-01T12:00:00")
        assert 0.0 <= weight <= 1.0

    def test_calculate_invalid_timestamp(self):
        calc = TimeWeightCalculator()
        weight = calc.calculate("not-a-date")
        assert weight >= 0.0  # Falls back gracefully

    def test_apply_weights(self):
        calc = TimeWeightCalculator()
        now = datetime.now(timezone.utc)
        memories = [
            {"id": "m1", "content": "recent",
             "timestamp": (now - timedelta(days=1)).isoformat()},
            {"id": "m2", "content": "old",
             "timestamp": (now - timedelta(days=365)).isoformat()},
        ]
        result = calc.apply_weights(memories)
        assert "time_weight" in result[0]
        assert result[0]["time_weight"] > result[1]["time_weight"]

    def test_get_best_time_range_recent(self):
        calc = TimeWeightCalculator()
        r = calc.get_best_time_range("things done this week")
        assert r is not None

    def test_get_best_time_range_today(self):
        calc = TimeWeightCalculator()
        r = calc.get_best_time_range("what happened today")
        assert r == "1d"

    def test_get_best_time_range_none(self):
        calc = TimeWeightCalculator()
        r = calc.get_best_time_range("random search")
        assert r is None

    def test_config_to_dict(self):
        cfg = TimeWeightConfig()
        d = cfg.to_dict()
        assert d["decay_type"] == "exponential"
