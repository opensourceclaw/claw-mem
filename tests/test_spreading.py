"""Tests for SpreadingActivation - Graph-based activation spreading."""

import pytest
from claw_mem.graph.multi_graph import MultiGraphMemory, SubGraphType
from claw_mem.graph.nodes import NodeType
from claw_mem.graph.edges import EdgeType
from claw_mem.retrieval.spreading import SpreadingActivation, spreading_bfs


class TestSpreadingBFS:
    """Tests for the standalone spreading_bfs function."""

    def setup_method(self):
        self.graph = MultiGraphMemory()
        for i in range(6):
            self.graph.add_node(f"n{i}", f"Node {i}", NodeType.EPISODE)
        # n0 → n1 → n2 → n3 (temporal chain)
        self.graph.add_edge("n0", "n1", EdgeType.NEXT, 1.0)
        self.graph.add_edge("n1", "n2", EdgeType.NEXT, 1.0)
        self.graph.add_edge("n2", "n3", EdgeType.NEXT, 1.0)
        # n0 → n4 (semantic)
        self.graph.add_edge("n0", "n4", EdgeType.RELATED_TO, 0.8)
        # n4 → n5 (causal)
        self.graph.add_edge("n4", "n5", EdgeType.DERIVED_FROM, 0.9)

    def test_single_seed(self):
        seeds = {"n0": 1.0}
        activations = spreading_bfs(
            seeds, self.graph, max_depth=2, decay_factor=0.5, threshold=0.05
        )
        assert "n0" in activations
        assert activations["n0"] == 1.0
        assert "n1" in activations  # depth 1

    def test_activation_decays_with_depth(self):
        seeds = {"n0": 1.0}
        activations = spreading_bfs(
            seeds, self.graph, max_depth=2, decay_factor=0.5, threshold=0.01
        )
        # n1 depth=1: 1.0 * 0.5^1 = 0.5 * edge_weight
        act_n1 = activations.get("n1", 0)
        # n2 depth=2: 0.5 * 0.5 = 0.25 * edge_weight
        act_n2 = activations.get("n2", 0)
        assert act_n2 < act_n1  # decay per hop

    def test_threshold_pruning(self):
        seeds = {"n0": 1.0}
        activations = spreading_bfs(seeds, self.graph, max_depth=2, decay_factor=0.1, threshold=0.5)
        # With heavy decay, deep nodes should be pruned
        total = len(activations)
        assert total <= 3  # n0 + maybe n1

    def test_depth_limit(self):
        seeds = {"n0": 1.0}
        activations = spreading_bfs(
            seeds, self.graph, max_depth=0, decay_factor=0.5, threshold=0.01
        )
        assert len(activations) == 1  # only seed

    def test_empty_seeds(self):
        activations = spreading_bfs({}, self.graph)
        assert activations == {}

    def test_max_nodes_limit(self):
        seeds = {f"n{i}": 1.0 for i in range(3)}
        activations = spreading_bfs(
            seeds, self.graph, max_depth=2, decay_factor=0.5, threshold=0.01, max_nodes=4
        )
        # max_nodes includes seeds; up to 1 spill allowed before next check
        assert len(activations) <= 4

    def test_multi_path_max_aggregation(self):
        # n0 → n2 via temporal (n0→n1→n2) AND via semantic (n0→n4→n5, but n2 is separate)
        # Add direct edge n0→n2
        self.graph.add_edge("n0", "n2", EdgeType.RELATED_TO, 0.6)
        seeds = {"n0": 1.0}
        activations = spreading_bfs(
            seeds, self.graph, max_depth=2, decay_factor=0.5, threshold=0.01
        )
        assert "n2" in activations


class TestSpreadingActivation:
    """Tests for SpreadingActivation class."""

    def setup_method(self):
        self.graph = MultiGraphMemory()
        self.graph.add_node("a", "A", NodeType.EPISODE)
        self.graph.add_node("b", "B", NodeType.EPISODE)
        self.graph.add_node("c", "C", NodeType.FACT)
        self.graph.add_node("d", "D", NodeType.CONCEPT)
        self.graph.add_edge("a", "b", EdgeType.NEXT, 1.0)
        self.graph.add_edge("a", "c", EdgeType.RELATED_TO, 0.9)
        self.graph.add_edge("c", "d", EdgeType.HAS_CONCEPT, 0.7)

        self.spreader = SpreadingActivation(self.graph)

    def test_activate_basic(self):
        seeds = {"a": 1.0, "c": 0.8}
        activations = self.spreader.activate(seeds)
        assert "a" in activations
        assert "c" in activations

    def test_activate_returns_seeds(self):
        seeds = {"a": 0.9}
        activations = self.spreader.activate(seeds)
        assert activations["a"] == 0.9

    def test_edge_type_filter_temporal(self):
        seeds = {"a": 1.0}
        activations = self.spreader.activate(seeds, intent="temporal")
        # Only temporal edges (NEXT) should expand
        assert "b" in activations  # via NEXT

    def test_edge_type_filter_entity(self):
        seeds = {"c": 1.0}
        activations = self.spreader.activate(seeds, intent="entity")
        # HAS_CONCEPT edge should work
        assert "d" in activations

    def test_configure_runtime(self):
        self.spreader.configure(max_depth=1, decay_factor=0.3, threshold=0.5)
        seeds = {"a": 1.0}
        activations = self.spreader.activate(seeds)
        # With threshold 0.5 and decay_factor 0.3, depth-1 activation should be pruned
        # activation = 1.0 * 0.3^1 = 0.3 < 0.5 → pruned
        assert len(activations) <= 2

    def test_get_stats(self):
        stats = self.spreader.get_stats()
        assert "max_depth" in stats
        assert "decay_factor" in stats
        assert "threshold" in stats
        assert "edge_weights" in stats

    def test_weak_edge_skip(self):
        self.graph.add_edge("a", "d", EdgeType.RELATED_TO, 0.05)
        seeds = {"a": 1.0}
        activations = self.spreader.activate(seeds)
        # Edge weight 0.05 yields very low activation, likely pruned
        assert "d" not in activations or activations["d"] < 0.1
