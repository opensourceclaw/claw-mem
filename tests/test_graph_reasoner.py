"""Tests for GraphReasoner + PathResult (F2 · v4.10.0)."""

import pytest

from claw_mem.extraction.openie_extractor import Triplet
from claw_mem.graph.graph_reasoner import GraphReasoner, PathResult


# ── PathResult dataclass ──────────────────────────────────────────────

class TestPathResult:
    def test_empty_path(self):
        pr = PathResult(path=[], length=0, confidence=0.0)
        assert pr.length == 0
        assert pr.confidence == 0.0
        assert "empty" in repr(pr)

    def test_single_step(self):
        pr = PathResult(
            path=[("a", "knows", "b")],
            length=1,
            confidence=0.9,
        )
        assert pr.length == 1
        assert len(pr.path) == 1
        assert "a" in repr(pr)
        assert "b" in repr(pr)

    def test_default_confidence(self):
        pr = PathResult(path=[], length=0)
        assert pr.confidence == 1.0


# ── GraphReasoner - construction ──────────────────────────────────────

class TestGraphConstruction:
    def test_add_single_triplet(self):
        gr = GraphReasoner()
        gr.add_triplet("张三", "负责", "电商项目")
        assert "张三" in gr._graph
        assert "电商项目" in gr._graph
        assert len(gr._graph["张三"]) == 1

    def test_add_multiple_triplets(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("b", "knows", "c")
        gr.add_triplet("a", "knows", "c")
        assert len(gr._graph["a"]) == 2
        assert len(gr._graph["b"]) == 1
        assert len(gr._graph["c"]) == 0  # c has no outgoing edges

    def test_add_triplet_with_confidence(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "likes", "b", confidence=0.5)
        edges = gr._graph["a"]
        assert edges[0][2] == 0.5  # confidence is third element

    def test_add_triplets_batch(self):
        gr = GraphReasoner()
        triplets = [
            Triplet("张三", "负责", "电商项目", 0.9, "rule"),
            Triplet("李四", "是", "工程师", 0.7, "rule"),
            Triplet("张三", "在", "北京", 0.6, "rule"),
        ]
        gr.add_triplets(triplets)
        assert len(gr._graph["张三"]) == 2
        assert len(gr._graph["李四"]) == 1

    def test_node_normalization(self):
        gr = GraphReasoner()
        gr.add_triplet(" 张三 ", "负责", "电商项目")
        # Should be normalized: stripped, lowercased
        assert "张三" in gr._graph

    def test_reverse_edges_maintained(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        # b should have a reverse entry from a
        assert "b" in gr._reverse
        assert len(gr._reverse["b"]) == 1
        assert gr._reverse["b"][0][1] == "a"  # reverse points back


# ── GraphReasoner - path finding ──────────────────────────────────────

class TestPathFinding:
    def test_direct_path(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        paths = gr.find_paths("a", "b")
        assert len(paths) >= 1
        assert paths[0].length == 1

    def test_two_hop_path(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("b", "knows", "c")
        paths = gr.find_paths("a", "c")
        assert len(paths) >= 1
        shortest = min(p.length for p in paths)
        assert shortest == 2

    def test_no_path(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("c", "knows", "d")
        paths = gr.find_paths("a", "d")
        assert paths == []

    def test_node_not_in_graph(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        assert gr.find_paths("a", "z") == []
        assert gr.find_paths("z", "a") == []

    def test_max_depth_limit(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("b", "knows", "c")
        gr.add_triplet("c", "knows", "d")
        # With max_depth=2, a→d should be unreachable
        paths = gr.find_paths("a", "d", max_depth=2)
        assert paths == []
        # With max_depth=3, a→d should be reachable
        paths_3 = gr.find_paths("a", "d", max_depth=3)
        assert len(paths_3) >= 1

    def test_cycle_avoidance(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("b", "knows", "a")  # creates a cycle
        gr.add_triplet("b", "knows", "c")
        paths = gr.find_paths("a", "c", max_depth=5)
        assert len(paths) >= 1
        # No path should have cycles (repeated nodes)
        for p in paths:
            nodes_in_path = set()
            for s, _, o in p.path:
                nodes_in_path.add(s)
                nodes_in_path.add(o)
            assert len(p.path) <= len(nodes_in_path)

    def test_path_confidence(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b", 0.9)
        gr.add_triplet("b", "knows", "c", 0.8)
        paths = gr.find_paths("a", "c")
        assert len(paths) >= 1
        expected = round(0.9 * 0.8, 4)
        assert paths[0].confidence == expected


# ── GraphReasoner - related nodes ─────────────────────────────────────

class TestRelatedNodes:
    def test_one_hop(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("a", "knows", "c")
        related = gr.find_related("a", max_depth=1)
        assert set(related) == {"b", "c"}

    def test_two_hops(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("b", "knows", "c")
        related = gr.find_related("a", max_depth=2)
        assert "b" in related
        assert "c" in related
        assert "a" not in related  # source not included

    def test_unknown_node(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        related = gr.find_related("z")
        assert related == []

    def test_empty_graph(self):
        gr = GraphReasoner()
        assert gr.find_related("a") == []


# ── GraphReasoner - node importance ───────────────────────────────────

class TestNodeImportance:
    def test_importance_basic(self):
        gr = GraphReasoner()
        gr.add_triplet("a", "knows", "b")
        gr.add_triplet("a", "knows", "c")
        gr.add_triplet("d", "knows", "a")
        importance = gr.node_importance()
        assert "a" in importance
        # a has: out=2 (→b, →c) + in=1 (←d) = 3 total
        # b has: out=0 + in=1 = 1
        # c has: out=0 + in=1 = 1
        # d has: out=1 + in=0 = 1
        # max = 3, so a should be 1.0
        assert importance["a"] == 1.0
        assert importance["b"] == pytest.approx(1.0 / 3, abs=0.01)

    def test_importance_empty_graph(self):
        gr = GraphReasoner()
        assert gr.node_importance() == {}

    def test_importance_all_zero_degree(self):
        gr = GraphReasoner()
        gr._graph["a"] = []
        gr._graph["b"] = []
        gr._reverse["a"] = []
        gr._reverse["b"] = []
        importance = gr.node_importance()
        assert importance["a"] == 0.0
        assert importance["b"] == 0.0
