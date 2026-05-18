"""Tests for MultiGraphMemory - Four orthogonal subgraph index layer."""

import pytest
from claw_mem.graph.multi_graph import (
    SubGraphType,
    SubGraph,
    GraphEdge,
    MultiGraphMemory,
    EDGE_TO_SUBGRAPH,
    SUBGRAPH_EXPANSION_WEIGHT,
)
from claw_mem.graph.nodes import NodeType
from claw_mem.graph.edges import EdgeType

# ============================================================================
# SubGraph tests
# ============================================================================


class TestSubGraph:
    """Unit tests for SubGraph (adjacency list + reverse adjacency)."""

    def test_create_empty(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        assert g.name == SubGraphType.TEMPORAL
        assert g.edge_count == 0
        assert len(g.nodes) == 0

    def test_add_node(self):
        g = SubGraph(SubGraphType.SEMANTIC)
        g.add_node("n1")
        assert "n1" in g.nodes
        g.add_node("n1")  # idempotent
        assert len(g.nodes) == 1

    def test_add_directed_edge(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("n1", "n2", weight=0.9, directed=True)
        assert g.has_edge("n1", "n2")
        assert not g.has_edge("n2", "n1")
        assert g.edge_count == 1

    def test_add_undirected_edge(self):
        g = SubGraph(SubGraphType.SEMANTIC)
        g.add_edge("n1", "n2", weight=0.8, directed=False)
        assert g.has_edge("n1", "n2")
        assert g.has_edge("n2", "n1")
        assert g.edge_count == 1

    def test_get_neighbors_depth_1(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("n1", "n2", weight=0.9, directed=True)
        g.add_edge("n1", "n3", weight=0.7, directed=True)
        neighbors = g.get_neighbors("n1", max_depth=1)
        assert "n2" in neighbors
        assert "n3" in neighbors
        assert "n1" not in neighbors

    def test_get_neighbors_nonexistent(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        assert g.get_neighbors("nonexistent") == {}

    def test_get_edges_from(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("a", "b", directed=True)
        g.add_edge("a", "c", directed=True)
        edges = g.get_edges_from("a")
        assert len(edges) == 2
        targets = {t for t, _ in edges}
        assert targets == {"b", "c"}

    def test_get_edges_to(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("x", "z", directed=True)
        g.add_edge("y", "z", directed=True)
        sources = g.get_edges_to("z")
        assert len(sources) == 2
        src_ids = {t for t, _ in sources}
        assert src_ids == {"x", "y"}

    def test_update_weight(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("n1", "n2", weight=1.0, directed=True)
        assert g.update_weight("n1", "n2", 0.5)
        assert g.edge_weights[("n1", "n2")] == 0.5

    def test_update_weight_nonexistent(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        assert not g.update_weight("a", "b", 0.5)

    def test_memory_estimate(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("a", "b")
        assert g.memory_estimate > 0

    def test_serialize_roundtrip(self):
        g = SubGraph(SubGraphType.TEMPORAL)
        g.add_edge("n1", "n2", 0.9)
        g.add_edge("n2", "n3", 0.7)
        d = g.to_dict()
        g2 = SubGraph.from_dict(d)
        assert g2.name == SubGraphType.TEMPORAL
        assert g2.edge_count == g.edge_count
        assert g2.has_edge("n1", "n2")
        assert g2.has_edge("n2", "n3")


# ============================================================================
# GraphEdge tests
# ============================================================================


class TestGraphEdge:
    """Unit tests for GraphEdge dataclass."""

    def test_create_and_serialize(self):
        edge = GraphEdge("a", "b", 0.85, "next", 100.0)
        d = edge.to_dict()
        assert d["s"] == "a"
        assert d["t"] == "b"
        assert d["w"] == 0.85
        assert d["e"] == "next"
        assert d["c"] == 100.0

    def test_deserialize(self):
        d = {"s": "x", "t": "y", "w": 0.5, "e": "related_to", "c": 200.0}
        edge = GraphEdge.from_dict(d)
        assert edge.source_id == "x"
        assert edge.target_id == "y"
        assert edge.weight == 0.5

    def test_deserialize_defaults(self):
        edge = GraphEdge.from_dict({"s": "a", "t": "b"})
        assert edge.weight == 1.0
        assert edge.edge_type == ""
        assert edge.created_at == 0.0


# ============================================================================
# MultiGraphMemory tests
# ============================================================================


class TestMultiGraphMemory:
    """Unit tests for MultiGraphMemory class."""

    def setup_method(self):
        self.mg = MultiGraphMemory()

    def test_add_node(self):
        self.mg.add_node("mem_1", "Test content", NodeType.EPISODE)
        assert self.mg.node_count() == 1
        node = self.mg.get_node("mem_1")
        assert node is not None
        assert node.type == NodeType.EPISODE

    def test_add_node_idempotent(self):
        self.mg.add_node("mem_1", "First", NodeType.EPISODE)
        self.mg.add_node("mem_1", "Second", NodeType.FACT)
        assert self.mg.node_count() == 1

    def test_add_node_registers_in_all_subgraphs(self):
        self.mg.add_node("n1", "Test", NodeType.EPISODE)
        for sg in SubGraphType:
            assert "n1" in self.mg._graphs[sg].nodes

    def test_add_edge_temporal(self):
        self.mg.add_node("n1", "Hello", NodeType.EPISODE)
        self.mg.add_node("n2", "World", NodeType.EPISODE)
        self.mg.add_edge("n1", "n2", EdgeType.NEXT, weight=0.9)
        assert self.mg._graphs[SubGraphType.TEMPORAL].has_edge("n1", "n2")

    def test_add_edge_semantic(self):
        self.mg.add_node("a", "X", NodeType.FACT)
        self.mg.add_node("b", "Y", NodeType.FACT)
        self.mg.add_edge("a", "b", EdgeType.RELATED_TO, weight=0.85)
        assert self.mg._graphs[SubGraphType.SEMANTIC].has_edge("a", "b")
        assert self.mg._graphs[SubGraphType.SEMANTIC].has_edge("b", "a")

    def test_add_edge_causal(self):
        self.mg.add_node("ep", "Ep", NodeType.EPISODE)
        self.mg.add_node("fact", "Fact", NodeType.FACT)
        self.mg.add_edge("fact", "ep", EdgeType.DERIVED_FROM)
        assert self.mg._graphs[SubGraphType.CAUSAL].has_edge("fact", "ep")

    def test_add_edge_entity(self):
        self.mg.add_node("n1", "AI", NodeType.EPISODE)
        self.mg.add_node("c1", "concept", NodeType.CONCEPT)
        self.mg.add_edge("n1", "c1", EdgeType.HAS_CONCEPT)
        assert self.mg._graphs[SubGraphType.ENTITY].has_edge("n1", "c1")

    def test_has_edge_across_subgraphs(self):
        self.mg.add_node("a", "A", NodeType.EPISODE)
        self.mg.add_node("b", "B", NodeType.EPISODE)
        self.mg.add_edge("a", "b", EdgeType.NEXT)
        assert self.mg.has_edge("a", "b")

    def test_get_related(self):
        self.mg.add_node("n1", "A", NodeType.EPISODE)
        self.mg.add_node("n2", "B", NodeType.EPISODE)
        self.mg.add_node("n3", "C", NodeType.EPISODE)
        self.mg.add_edge("n1", "n2", EdgeType.NEXT, 1.0)
        self.mg.add_edge("n1", "n3", EdgeType.NEXT, 0.5)
        related = self.mg.get_related("n1", SubGraphType.TEMPORAL, limit=10)
        assert related[0] == "n2"  # higher weight first

    def test_get_expanded_nodes(self):
        self.mg.add_node("n1", "A", NodeType.EPISODE)
        self.mg.add_node("n2", "B", NodeType.EPISODE)
        self.mg.add_node("n3", "C", NodeType.EPISODE)
        self.mg.add_edge("n1", "n2", EdgeType.NEXT, 1.0)
        self.mg.add_edge("n2", "n3", EdgeType.NEXT, 0.8)
        expanded = self.mg.get_expanded_nodes(["n1"], max_depth=2, max_expansion=10)
        assert "n2" in expanded
        assert expanded["n1"] == 1.0  # seed weight

    def test_get_expanded_nodes_empty_seeds(self):
        expanded = self.mg.get_expanded_nodes([])
        assert len(expanded) == 0

    def test_multi_graph_search(self):
        self.mg.add_node("s1", "Seed 1", NodeType.EPISODE)
        self.mg.add_node("s2", "Seed 2", NodeType.EPISODE)
        self.mg.add_node("nb", "Neighbor", NodeType.FACT)
        self.mg.add_edge("s1", "nb", EdgeType.NEXT, 1.0)
        results = self.mg.multi_graph_search(["s1", "s2"], k=10)
        result_ids = [r[0] for r in results]
        assert "s1" in result_ids
        assert "s2" in result_ids

    def test_multi_graph_search_empty(self):
        results = self.mg.multi_graph_search([], k=5)
        assert results == []

    def test_apply_decay(self):
        self.mg.add_node("a", "A", NodeType.EPISODE)
        self.mg.add_node("b", "B", NodeType.EPISODE)
        self.mg.add_edge("a", "b", EdgeType.NEXT, 1.0)
        updated = self.mg.apply_decay({("a", "b"): 0.5})
        assert updated >= 1
        assert self.mg._graphs[SubGraphType.TEMPORAL].edge_weights[("a", "b")] == 0.5

    def test_remove_expired_edges(self):
        self.mg.add_node("a", "A", NodeType.EPISODE)
        self.mg.add_node("b", "B", NodeType.EPISODE)
        self.mg.add_node("c", "C", NodeType.EPISODE)
        self.mg.add_edge("a", "b", EdgeType.NEXT, 0.5)
        self.mg.add_edge("b", "c", EdgeType.NEXT, 0.01)  # below threshold
        removed = self.mg.remove_expired_edges(threshold=0.05)
        assert removed >= 1
        assert not self.mg._graphs[SubGraphType.TEMPORAL].has_edge("b", "c")

    def test_get_stats(self):
        self.mg.add_node("n1", "A", NodeType.EPISODE)
        self.mg.add_node("n2", "B", NodeType.EPISODE)
        self.mg.add_edge("n1", "n2", EdgeType.NEXT)
        stats = self.mg.get_stats()
        assert stats["total_nodes"] == 2
        assert isinstance(stats["subgraphs"], dict)

    def test_serialize_roundtrip(self):
        self.mg.add_node("n1", "Test A", NodeType.EPISODE)
        self.mg.add_node("n2", "Test B", NodeType.FACT)
        self.mg.add_edge("n1", "n2", EdgeType.NEXT, 1.0)
        self.mg.add_edge("n1", "n2", EdgeType.RELATED_TO, 0.8)

        d = self.mg.to_dict()
        mg2 = MultiGraphMemory.from_dict(d)
        assert mg2.node_count() == 2
        assert mg2.has_edge("n1", "n2")

    def test_bulk_nodes(self):
        for i in range(100):
            self.mg.add_node(f"n{i}", f"Content {i}", NodeType.EPISODE)
        assert self.mg.node_count() == 100

    def test_bulk_edges(self):
        for i in range(50):
            self.mg.add_node(f"n{i}", f"C{i}", NodeType.EPISODE)
        for i in range(49):
            self.mg.add_edge(f"n{i}", f"n{i+1}", EdgeType.NEXT)
        assert self.mg._graphs[SubGraphType.TEMPORAL].edge_count == 49


# ============================================================================
# Integration: EDGE_TO_SUBGRAPH mapping
# ============================================================================


class TestEdgeSubGraphMapping:
    """Verify edge type to subgraph routing."""

    def test_next_to_temporal(self):
        assert EDGE_TO_SUBGRAPH[EdgeType.NEXT] == SubGraphType.TEMPORAL

    def test_derived_from_to_causal(self):
        assert EDGE_TO_SUBGRAPH[EdgeType.DERIVED_FROM] == SubGraphType.CAUSAL

    def test_related_to_to_semantic(self):
        assert EDGE_TO_SUBGRAPH[EdgeType.RELATED_TO] == SubGraphType.SEMANTIC

    def test_has_concept_to_entity(self):
        assert EDGE_TO_SUBGRAPH[EdgeType.HAS_CONCEPT] == SubGraphType.ENTITY

    def test_all_edge_types_mapped(self):
        for et in EdgeType:
            assert et in EDGE_TO_SUBGRAPH, f"Missing mapping: {et}"


class TestExpansionWeights:
    """Verify expansion weight defaults."""

    def test_all_subgraphs_have_weight(self):
        for sg in SubGraphType:
            assert sg in SUBGRAPH_EXPANSION_WEIGHT

    def test_weights_in_range(self):
        for w in SUBGRAPH_EXPANSION_WEIGHT.values():
            assert 0.0 <= w <= 1.0
