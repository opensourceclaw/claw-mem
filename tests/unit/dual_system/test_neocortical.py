"""Tests for claw_mem.dual_system.neocortical.NeocorticalStore."""
import pytest
from claw_mem.dual_system import NeocorticalStore, Memory


@pytest.fixture
def store():
    return NeocorticalStore()


class TestNeocorticalStore:
    def test_consolidate_empty(self, store):
        ids = store.consolidate([])
        assert ids == []

    def test_consolidate_extracts_concepts(self, store):
        memories = [
            Memory(content="database query optimization using indexes"),
            Memory(content="optimize slow database query performance"),
            Memory(content="index optimization for faster queries"),
        ]
        ids = store.consolidate(memories)
        assert len(ids) == 3
        assert store.concept_count() >= 1
        assert store.size() == 3

    def test_abstract_concepts(self, store):
        memories = [
            Memory(content="fix bug in authentication module"),
            Memory(content="authentication bug found in login flow"),
            Memory(content="refactor authentication code"),
        ]
        concepts = store.abstract_concepts(memories)
        assert len(concepts) >= 1
        assert "authentication" in concepts[0].keywords or len(concepts[0].keywords) > 0

    def test_abstract_concepts_empty(self, store):
        assert store.abstract_concepts([]) == []

    def test_retrieve_finds_memories(self, store):
        store.consolidate([Memory(content="deploy to production server")])
        results = store.retrieve("deploy")
        assert len(results) >= 1

    def test_retrieve_finds_concepts(self, store):
        store.consolidate([Memory(content="test driven development"), Memory(content="unit testing is important")])
        results = store.retrieve("test")
        assert len(results) >= 1

    def test_retrieve_limits(self, store):
        for i in range(10):
            store.consolidate([Memory(content=f"memory {i}")])
        results = store.retrieve("memory", limit=3)
        assert len(results) <= 3

    def test_apply_forgetting_curve_fresh(self, store):
        m = Memory(content="fresh", importance=0.8, created_at=__import__('time').time())
        store._store["fresh-id"] = m
        retention = store.apply_forgetting_curve("fresh-id")
        assert retention == pytest.approx(1.0)

    def test_apply_forgetting_curve_old(self, store):
        m = Memory(content="old", importance=0.5, created_at=__import__('time').time() - 86400 * 30)
        store._store["old-id"] = m
        retention = store.apply_forgetting_curve("old-id")
        assert 0.0 <= retention < 1.0

    def test_apply_forgetting_curve_nonexistent(self, store):
        assert store.apply_forgetting_curve("no-such") == 0.0

    def test_get_concept(self, store):
        memories = [Memory(content="concept test one"), Memory(content="concept test two")]
        store.consolidate(memories)
        concepts = store.list_concepts()
        if concepts:
            found = store.get_concept(concepts[0].concept_id)
            assert found is not None

    def test_connect_concepts(self, store):
        store.connect("c1", "c2")
        assert "c2" in store.get_connections("c1")
        assert "c1" in store.get_connections("c2")

    def test_clear(self, store):
        store.consolidate([Memory(content="test")])
        store.clear()
        assert store.size() == 0
        assert store.concept_count() == 0
