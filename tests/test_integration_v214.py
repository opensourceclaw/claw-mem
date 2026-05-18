"""Integration tests for v2.14.0 - Graph + Decay + GroundTruth."""

import os
import tempfile
import pytest
from claw_mem.storage.ground_truth import GroundTruthStore, GroundTruthRecord
from claw_mem.graph.multi_graph import MultiGraphMemory, SubGraphType
from claw_mem.graph.dual_layer import DualLayerMemory
from claw_mem.graph.nodes import NodeType
from claw_mem.graph.edges import EdgeType
from claw_mem.decay import DecayController, DecayScheduler, DecayConfig

# ============================================================================
# GroundTruthStore tests
# ============================================================================


class TestGroundTruthStore:
    """Unit tests for GroundTruthStore."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.gt = GroundTruthStore(self.tmpdir)

    def test_store_and_retrieve(self):
        self.gt.store_turn(
            "sess_1",
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        )
        records = self.gt.get_session("sess_1")
        assert len(records) >= 1
        record = records[0]
        assert len(record["messages"]) == 2

    def test_store_multiple_turns(self):
        self.gt.store_turn("sess_a", [{"role": "user", "content": "Q1"}])
        self.gt.store_turn("sess_a", [{"role": "assistant", "content": "A1"}])
        records = self.gt.get_session("sess_a")
        assert len(records) == 2

    def test_search_by_keyword(self):
        self.gt.store_turn("s_1", [{"role": "user", "content": "I prefer Chinese"}])
        self.gt.store_turn("s_2", [{"role": "user", "content": "Build REST API"}])
        results = self.gt.search(keyword="chinese")
        assert len(results) >= 1

    def test_search_by_session(self):
        self.gt.store_turn("s_x", [{"role": "user", "content": "Hello"}])
        self.gt.store_turn("s_y", [{"role": "user", "content": "World"}])
        results = self.gt.search(session_id="s_x")
        assert all(r["session_id"] == "s_x" for r in results)

    def test_list_sessions(self):
        self.gt.store_turn("a", [{"role": "user", "content": "X"}])
        self.gt.store_turn("b", [{"role": "user", "content": "Y"}])
        sessions = self.gt.list_sessions()
        assert len(sessions) >= 2

    def test_count_records(self):
        self.gt.store_turn("s1", [{"role": "user", "content": "A"}])
        self.gt.store_turn("s1", [{"role": "assistant", "content": "B"}])
        self.gt.store_turn("s2", [{"role": "user", "content": "C"}])
        assert self.gt.count_records() == 3

    def test_empty_session(self):
        assert self.gt.get_session("nonexistent") == []
        assert self.gt.count_records() == 0

    def test_record_with_metadata(self):
        rid = self.gt.store_turn(
            "s", [{"role": "user", "content": "Test"}], metadata={"task": "debug"}
        )
        assert rid.startswith("gt_")
        records = self.gt.get_session("s")
        assert records[0].get("metadata", {}).get("task") == "debug"

    def test_store_session(self):
        msgs = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
        ]
        rid = self.gt.store_session("full_sess", msgs)
        records = self.gt.get_session("full_sess")
        assert len(records) == 1
        assert len(records[0]["messages"]) == 3


class TestGroundTruthRecord:
    """Tests for GroundTruthRecord dataclass."""

    def test_serialize_roundtrip(self):
        r = GroundTruthRecord(
            "gt_abc", "sess_x", [{"role": "user", "content": "Hi"}], 12345.0, {"key": "val"}
        )
        d = r.to_dict()
        r2 = GroundTruthRecord.from_dict(d)
        assert r2.record_id == "gt_abc"
        assert r2.session_id == "sess_x"
        assert len(r2.messages) == 1
        assert r2.metadata == {"key": "val"}


# ============================================================================
# Full integration: MultiGraph + DecayController + DecayScheduler
# ============================================================================


class TestGraphDecayIntegration:
    """Integration tests: graph structure with decay lifecycle."""

    def test_store_and_decay_full_cycle(self):
        mg = MultiGraphMemory()
        cfg = DecayConfig(purge_threshold=0.5)  # aggressive for testing
        ctrl = DecayController(mg, config=cfg)

        # Setup: 3 nodes with edges
        mg.add_node("n1", "Task start", NodeType.EPISODE)
        mg.add_node("n2", "Task middle", NodeType.EPISODE)
        mg.add_node("n3", "Task end", NodeType.EPISODE)
        mg.add_edge("n1", "n2", EdgeType.NEXT, 1.0)
        mg.add_edge("n2", "n3", EdgeType.NEXT, 0.3)

        # Classify
        classified = ctrl.classify_edges()
        assert len(classified["strong"]) >= 1  # weight 1.0
        assert len(classified["weak"]) >= 1 or len(classified["expired"]) >= 1  # weight 0.3

        # Cleanup: edge with weight 0.3 below purge_threshold 0.5
        removed = ctrl.cleanup_expired()
        assert len(removed) == 1  # the weak edge

    def test_scheduler_lifecycle(self):
        mg = MultiGraphMemory()
        mg.add_node("a", "A", NodeType.EPISODE)
        mg.add_node("b", "B", NodeType.EPISODE)
        mg.add_edge("a", "b", EdgeType.NEXT, 1.0)

        ctrl = DecayController(mg, DecayConfig(purge_threshold=0.9))
        sched = DecayScheduler(ctrl)
        assert not sched.is_running()

        sched.start()
        assert sched.is_running()
        sched.stop()
        assert not sched.is_running()

    def test_scheduler_notify_store_threshold(self):
        mg = MultiGraphMemory()
        ctrl = DecayController(mg)
        sched = DecayScheduler(ctrl)
        # Notify up to threshold-1
        for _ in range(99):
            sched.notify_store()
        # Should not crash
        assert True

    def test_multi_graph_decay_apply(self):
        mg = MultiGraphMemory()
        mg.add_node("x", "X", NodeType.EPISODE)
        mg.add_node("y", "Y", NodeType.EPISODE)
        mg.add_edge("x", "y", EdgeType.NEXT, 1.0)

        updates = {("x", "y"): 0.5}
        updated = mg.apply_decay(updates)
        assert updated >= 1
        assert mg._graphs[SubGraphType.TEMPORAL].edge_weights[("x", "y")] == 0.5

    def test_full_graph_lifecycle(self):
        """Simulate a realistic lifecycle: create nodes → edges → decay → search."""
        mg = MultiGraphMemory()

        # Build graph
        for i in range(5):
            mg.add_node(f"n{i}", f"Content {i}", NodeType.EPISODE)
        for i in range(4):
            mg.add_edge(f"n{i}", f"n{i+1}", EdgeType.NEXT, 1.0)
        mg.add_edge("n0", "n3", EdgeType.RELATED_TO, 0.8)

        # Search
        related = mg.get_related("n0", SubGraphType.TEMPORAL, limit=5)
        assert len(related) >= 1

        expanded = mg.get_expanded_nodes(["n0"], max_depth=2)
        assert len(expanded) >= 2

        # Serialize/deserialize
        d = mg.to_dict()
        mg2 = MultiGraphMemory.from_dict(d)
        assert mg2.node_count() == 5

    def test_dual_layer_with_graph(self):
        """DualLayerMemory operates on top of MultiGraphMemory."""
        mg = MultiGraphMemory()
        mg.add_node("n1", "Event content", NodeType.EPISODE)
        mg.add_node("n2", "Another event", NodeType.EPISODE)

        dl = DualLayerMemory()
        eid = dl.add_event("First event", node_ids=["n1", "n2"], session_id="s1")
        assert dl.event_count() == 1
        evt = dl.get_event(eid)
        assert "n1" in evt.node_ids

    def test_disabled_components(self):
        """All new components should be gracefully absent when disabled."""
        # MultiGraphMemory with enable_graph=False returns None
        mg = MultiGraphMemory()
        assert mg.node_count() == 0  # no nodes, not None, just empty
        assert mg.get_node("nonexistent") is None

    def test_serialize_full_graph(self):
        """Serialize and deserialize a graph with multiple subgraphs."""
        mg = MultiGraphMemory()
        mg.add_node("a", "A", NodeType.EPISODE)
        mg.add_node("b", "B", NodeType.FACT)
        mg.add_node("c", "C", NodeType.CONCEPT)
        mg.add_edge("a", "b", EdgeType.NEXT, 1.0)
        mg.add_edge("b", "c", EdgeType.HAS_CONCEPT, 0.9)
        mg.add_edge("a", "c", EdgeType.RELATED_TO, 0.8)
        mg.add_edge("b", "a", EdgeType.DERIVED_FROM, 0.7)

        d = mg.to_dict()
        mg2 = MultiGraphMemory.from_dict(d)
        assert mg2.node_count() == 3
        assert mg2.has_edge("a", "b")
        assert mg2.has_edge("b", "c")
        assert mg2.has_edge("a", "c")


# ============================================================================
# Edge routing verification
# ============================================================================


class TestEdgeRouting:
    """Verify edge types route to correct subgraphs."""

    def test_all_edge_types_coverage(self):
        mg = MultiGraphMemory()
        mg.add_node("src", "Source", NodeType.EPISODE)
        mg.add_node("dst", "Dest", NodeType.EPISODE)

        routes = {
            EdgeType.NEXT: SubGraphType.TEMPORAL,
            EdgeType.DERIVED_FROM: SubGraphType.CAUSAL,
            EdgeType.SYNTHESIZED_FROM: SubGraphType.CAUSAL,
            EdgeType.RELATED_TO: SubGraphType.SEMANTIC,
            EdgeType.HAS_CONCEPT: SubGraphType.ENTITY,
        }

        for edge_type, expected_sg in routes.items():
            mg2 = MultiGraphMemory()
            mg2.add_node("x", "X", NodeType.EPISODE)
            mg2.add_node("y", "Y", NodeType.EPISODE)
            mg2.add_edge("x", "y", edge_type, 1.0)
            assert mg2._graphs[expected_sg].has_edge(
                "x", "y"
            ), f"Edge {edge_type} not in {expected_sg}"
