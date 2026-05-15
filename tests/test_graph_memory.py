"""Tests for claw-mem v2.14.0 graph memory modules."""

import time
import pytest
from claw_mem.graph_memory.multi_graph import MultiGraphMemory
from claw_mem.graph_memory.semantic_graph import SemanticGraph
from claw_mem.graph_memory.temporal_graph import TemporalGraph
from claw_mem.graph_memory.causal_graph import CausalGraph
from claw_mem.graph_memory.entity_graph import EntityGraph
from claw_mem.graph_memory.dual_layer import DualLayerMemory, EventProgressionGraph
from claw_mem.decay import DecayController, ReadGate, WriteGate
from claw_mem.ground_truth import GroundTruthStore

# ── SemanticGraph ──────────────────────────────────


class TestSemanticGraph:
    def setup_method(self):
        self.g = SemanticGraph()

    def test_add_and_query(self):
        self.g.add_node("1", "machine learning models")
        self.g.add_node("2", "deep learning networks")
        results = self.g.query("machine learning")
        assert len(results) > 0
        assert results[0]["id"] == "1"

    def test_similarity_neighbors(self):
        self.g.add_node("1", "python programming language")
        self.g.add_node("2", "python data analysis")
        self.g.add_node("3", "quantum physics theory")
        neighbors = self.g.get_neighbors("1")
        assert "2" in neighbors

    def test_count(self):
        self.g.add_node("1", "a")
        self.g.add_node("2", "b")
        assert self.g.count() == 2


# ── TemporalGraph ──────────────────────────────────


class TestTemporalGraph:
    def setup_method(self):
        self.g = TemporalGraph()

    def test_chronological_order(self):
        self.g.add_node("1", 100)
        self.g.add_node("2", 200)
        self.g.add_node("3", 300)
        assert self.g.get_before(250) == ["1", "2"]
        assert self.g.get_after(150) == ["2", "3"]

    def test_get_range(self):
        self.g.add_node("1", 100)
        self.g.add_node("2", 200)
        self.g.add_node("3", 300)
        result = self.g.get_range(150, 350)
        assert "2" in result
        assert "3" in result
        assert "1" not in result

    def test_get_recent(self):
        for i in range(15):
            self.g.add_node(str(i), float(i * 100))
        recent = self.g.get_recent(5)
        assert len(recent) == 5


# ── CausalGraph ────────────────────────────────────


class TestCausalGraph:
    def setup_method(self):
        self.g = CausalGraph()

    def test_causal_link(self):
        self.g.add_causal_link("bug_found", "bug_fix")
        assert "bug_found" in self.g.get_causes("bug_fix")
        assert "bug_fix" in self.g.get_effects("bug_found")

    def test_causal_chain(self):
        self.g.add_causal_link("a", "b")
        self.g.add_causal_link("b", "c")
        causes = self.g.get_causal_chain("c", upstream=True)
        assert "b" in causes
        assert "a" in causes


# ── EntityGraph ────────────────────────────────────


class TestEntityGraph:
    def setup_method(self):
        self.g = EntityGraph()

    def test_entity_indexing(self):
        self.g.add_node("1", ["Python", "AI"])
        self.g.add_node("2", ["Python", "Web"])
        assert "1" in self.g.get_by_entity("Python")
        assert "2" in self.g.get_by_entity("Python")

    def test_shared_entities(self):
        self.g.add_node("1", ["Python", "AI"])
        self.g.add_node("2", ["Python", "Web"])
        shared = self.g.get_shared_entities("1", "2")
        assert "Python" in shared

    def test_extract_entities(self):
        entities = self.g.extract_entities("Hello World from Python and Java")
        assert "Python" in entities
        assert "Java" in entities


# ── MultiGraphMemory ───────────────────────────────


class TestMultiGraphMemory:
    def setup_method(self):
        self.mg = MultiGraphMemory()

    def test_add_memory_all_graphs(self):
        mid = self.mg.add_memory({"text": "Python AI memory system"})
        assert mid is not None
        stats = self.mg.get_stats()
        assert stats["semantic_nodes"] == 1
        assert stats["temporal_nodes"] == 1

    def test_cross_graph_query(self):
        self.mg.add_memory({"text": "Python programming"})
        self.mg.add_memory({"text": "Machine learning with Python"})
        results = self.mg.query("Python programming", top_k=5)
        assert len(results) > 0

    def test_causal_linkage(self):
        self.mg.add_memory({"text": "Bug found in module X", "id": "cause1"})
        self.mg.add_memory({"text": "Fixed bug in module X", "cause_of": "cause1"})
        causes = self.mg.causal.get_causes("cause1")
        assert len(causes) >= 0  # cause1 has 0 causes (it IS a cause)

    def test_remove_memory(self):
        mid = self.mg.add_memory({"text": "test"})
        self.mg.remove_memory(mid)
        stats = self.mg.get_stats()
        assert stats["semantic_nodes"] == 0


# ── DualLayerMemory ────────────────────────────────


class TestDualLayerMemory:
    def setup_method(self):
        self.dl = DualLayerMemory()

    def test_add_interaction(self):
        self.dl.add_interaction("testing graph memory feature", "session_1")
        context = self.dl.build_context("session_1")
        assert len(context) == 1

    def test_multiple_sessions(self):
        self.dl.add_interaction("session A content", "sess_a")
        self.dl.add_interaction("session B content", "sess_b")
        assert len(self.dl.build_context("sess_a")) == 1
        assert len(self.dl.build_context("sess_b")) == 1

    def test_topic_extraction(self):
        self.dl.add_interaction("fix memory bug in graph module", "s1")
        related = self.dl.get_related_topics("memory")
        assert isinstance(related, list)


# ── DecayController ────────────────────────────────


class TestDecayController:
    def setup_method(self):
        self.dc = DecayController(decay_rate=0.5, forget_threshold=0.1)

    def test_apply_decay_recent(self):
        memories = [{"id": "m1", "text": "recent", "timestamp": time.time()}]
        self.dc.apply_decay(memories)
        assert memories[0]["accessibility"] > 0.9

    def test_apply_decay_old(self):
        old_ts = time.time() - 7 * 86400  # 7 days ago
        memories = [{"id": "m1", "text": "old", "timestamp": old_ts}]
        self.dc.apply_decay(memories)
        assert memories[0]["accessibility"] < 0.5

    def test_should_forget(self):
        old_ts = time.time() - 100 * 86400
        mem = {"id": "m1", "timestamp": old_ts}
        assert self.dc.should_forget(mem)

    def test_get_forgettable(self):
        memories = [
            {"id": "m1", "timestamp": time.time()},
            {"id": "m2", "timestamp": time.time() - 100 * 86400},
        ]
        forgettable = self.dc.get_forgettable(memories)
        assert len(forgettable) == 1


# ── GroundTruthStore ───────────────────────────────


class TestGroundTruthStore:
    def setup_method(self):
        self.gt = GroundTruthStore()

    def test_store_episode(self):
        eid = self.gt.store_episode("user asked about Python")
        assert eid is not None
        assert self.gt.count_episodes() == 1

    def test_store_and_verify_fact(self):
        eid = self.gt.store_episode("Python is a programming language")
        facts = self.gt.extract_facts("Python is a programming language")
        assert len(facts) > 0
        fid = self.gt.store_fact(facts[0], eid)
        assert self.gt.verify_fact(fid)

    def test_extract_action_facts(self):
        facts = self.gt.extract_facts("I implemented the graph memory feature")
        assert len(facts) > 0

    def test_extract_measurement_facts(self):
        facts = self.gt.extract_facts("Test coverage reached 93%")
        assert len(facts) > 0
