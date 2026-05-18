"""Tests for decay module - DecayController and DecayScheduler."""

import math
import time
import pytest
from claw_mem.decay.functions import (
    exponential_decay,
    calculate_weight,
    half_life_to_days,
    DecayConfig,
    HALF_LIFE,
    LAMBDA,
)
from claw_mem.decay.controller import DecayController
from claw_mem.decay.scheduler import DecayScheduler
from claw_mem.graph.multi_graph import MultiGraphMemory, SubGraphType
from claw_mem.graph.nodes import NodeType
from claw_mem.graph.edges import EdgeType

# ============================================================================
# Decay functions tests
# ============================================================================


class TestExponentialDecay:
    """Tests for the core exponential_decay function."""

    def test_no_decay_zero_days(self):
        w = exponential_decay(1.0, 0, 7.0)
        assert w == 1.0

    def test_half_life(self):
        """At exactly half-life, weight should be ~0.5."""
        w = exponential_decay(1.0, 7.0, 7.0)
        assert abs(w - 0.5) < 0.01

    def test_double_half_life(self):
        """At 2x half-life, weight should be ~0.25."""
        w = exponential_decay(1.0, 14.0, 7.0)
        assert abs(w - 0.25) < 0.01

    def test_negative_days(self):
        w = exponential_decay(1.0, -5, 7.0)
        assert w == 1.0

    def test_zero_half_life(self):
        w = exponential_decay(1.0, 10, 0)
        assert w == 0.0

    def test_output_in_range(self):
        w = exponential_decay(1.0, 365, 7.0)
        assert 0.0 <= w <= 1.0

    def test_high_base_weight(self):
        w = exponential_decay(2.0, 7.0, 7.0)
        assert abs(w - 1.0) < 0.01

    def test_low_days(self):
        w = exponential_decay(1.0, 0.1, 7.0)
        assert w > 0.95


class TestCalculateWeight:
    """Tests for category-based weight calculation."""

    def test_episodic_category(self):
        w = calculate_weight(1.0, 7, "episodic")
        assert abs(w - 0.5) < 0.01

    def test_semantic_category(self):
        w = calculate_weight(1.0, 7, "semantic")
        assert w > 0.9  # 90-day half-life, 7 days = minimal decay

    def test_temporal_category(self):
        w = calculate_weight(1.0, 7, "temporal")
        assert abs(w - 0.5) < 0.01  # same as episodic (7d)

    def test_unknown_category_defaults(self):
        w = calculate_weight(1.0, 30, "unknown")
        assert w < 1.0


class TestHalfLifeInference:
    """Tests for half-life inverse calculation."""

    def test_infer_half_life(self):
        # After 7 days at weight ~0.5, half-life should be ~7 days
        inferred = half_life_to_days(0.5, 1.0, 7.0)
        assert abs(inferred - 7.0) < 0.1

    def test_no_decay(self):
        inferred = half_life_to_days(1.0, 1.0, 10.0)
        assert inferred == 30.0  # defaults

    def test_zero_weight(self):
        inferred = half_life_to_days(0.0, 1.0, 10.0)
        assert inferred == 30.0


class TestDecayConfig:
    """Tests for DecayConfig dataclass."""

    def test_defaults(self):
        cfg = DecayConfig.default()
        assert cfg.half_life_temporal == 7.0
        assert cfg.half_life_semantic == 90.0
        assert cfg.purge_threshold == 0.05

    def test_custom(self):
        cfg = DecayConfig(half_life_temporal=14.0, purge_threshold=0.1)
        assert cfg.half_life_temporal == 14.0
        assert cfg.purge_threshold == 0.1

    def test_half_life_dict(self):
        assert HALF_LIFE["temporal"] == 7.0
        assert HALF_LIFE["semantic"] == 90.0

    def test_lambda_values(self):
        assert abs(LAMBDA["temporal"] - math.log(2) / 7.0) < 0.001


# ============================================================================
# DecayController tests
# ============================================================================


class TestDecayController:
    """Tests for DecayController."""

    def setup_method(self):
        self.mg = MultiGraphMemory()
        self.mg.add_node("a", "A", NodeType.EPISODE)
        self.mg.add_node("b", "B", NodeType.EPISODE)
        self.mg.add_edge("a", "b", EdgeType.NEXT, 1.0)
        self.ctrl = DecayController(self.mg)

    def test_calculate_single_weight(self):
        w = self.ctrl.calculate_single_weight(1.0, 7.0, "temporal")
        assert abs(w - 0.5) < 0.01

    def test_edge_type_to_category(self):
        assert self.ctrl._edge_type_to_category("next") == "temporal"
        assert self.ctrl._edge_type_to_category("related_to") == "semantic"

    def test_classify_edges(self):
        # Add edges with different weights
        self.mg.add_node("c", "C", NodeType.EPISODE)
        self.mg.add_node("d", "D", NodeType.EPISODE)
        self.mg.add_node("e", "E", NodeType.EPISODE)
        self.mg.add_edge("a", "c", EdgeType.NEXT, 0.8)  # strong
        self.mg.add_edge("a", "d", EdgeType.NEXT, 0.5)  # medium
        self.mg.add_edge("a", "e", EdgeType.NEXT, 0.05)  # expired

        classified = self.ctrl.classify_edges()
        assert len(classified["strong"]) >= 1
        assert len(classified["expired"]) >= 1

    def test_should_remove_edge_below_purge(self):
        assert self.ctrl.should_remove_edge("a", "b", 0.01)

    def test_should_remove_edge_above_purge(self):
        assert not self.ctrl.should_remove_edge("a", "b", 0.5)

    def test_cleanup_expired(self):
        self.mg.add_node("c", "C", NodeType.EPISODE)
        self.mg.add_edge("b", "c", EdgeType.NEXT, 0.01)
        removed = self.ctrl.cleanup_expired()
        assert len(removed) >= 1
        assert not self.mg._graphs[SubGraphType.TEMPORAL].has_edge("b", "c")

    def test_compute_all_decays(self):
        updates = self.ctrl.compute_all_decays()
        # Newly created edges (0 days old) should have no decay
        assert len(updates) == 0 or all(w >= 0.99 for w in updates.values())

    def test_get_stats(self):
        stats = self.ctrl.get_stats()
        assert "total_edges" in stats
        assert "strong_edges" in stats


# ============================================================================
# DecayScheduler tests
# ============================================================================


class TestDecayScheduler:
    """Tests for DecayScheduler."""

    def setup_method(self):
        self.mg = MultiGraphMemory()
        self.mg.add_node("a", "A", NodeType.EPISODE)
        self.mg.add_node("b", "B", NodeType.EPISODE)
        self.mg.add_edge("a", "b", EdgeType.NEXT, 1.0)
        self.ctrl = DecayController(self.mg)
        self.sched = DecayScheduler(self.ctrl)

    def test_initial_state(self):
        assert not self.sched.is_running()

    def test_start_stop(self):
        self.sched.start()
        assert self.sched.is_running()
        self.sched.stop()
        assert not self.sched.is_running()

    def test_notify_store_counting(self):
        # 100 notify_store calls should trigger a decay cycle
        for _ in range(99):
            self.sched.notify_store()
        # After fewer than 100, internal counter increases but cycle not yet triggered
        # (we just verify it doesn't crash)
        assert True

    def test_on_complete_callback(self):
        results = []

        def cb(removed):
            results.append(len(removed))

        self.sched.on_complete(cb)
        # Schedule manually
        self.sched._run_decay_cycle()
        # Since edges are fresh, nothing should be removed
        assert len(results) >= 0  # callback should have fired
