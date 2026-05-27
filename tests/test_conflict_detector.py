"""Tests for ConflictDetector (F3 · v4.7.0)."""

import tempfile

import pytest

from claw_mem.merge.conflict_detector import (
    ConflictDetector,
    ConflictReport,
    ConflictResolution,
    _extract_entities,
    _extract_attributes,
)
from claw_mem.memory_manager import MemoryManager


# ── mock helpers ──────────────────────────────────────────────────────

class _MockLLMProvider:
    """Configurable LLM for testing conflict detection."""

    def __init__(self, responses: list = None):
        self.responses = responses or ["YES", "A"]
        self._idx = 0
        self.calls: list = []

    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        self.calls.append(prompt)
        resp = self.responses[self._idx % len(self.responses)]
        self._idx += 1
        return resp


class _MockEmbeddingService:
    def __init__(self, vectors: dict = None):
        self._vecs = vectors or {}
        self._default_dim = 16

    def encode(self, texts, batch_size=32):
        return [self._vecs.get(t, [1.0] * self._default_dim) for t in texts]


def _make_manager(workspace_dir: str) -> MemoryManager:
    return MemoryManager(
        workspace=workspace_dir,
        enable_graph=False,
        enable_decay=False,
        enable_ground_truth=False,
    )


def _store_semantic(manager: MemoryManager, content: str, metadata=None) -> str:
    record = {"content": content, "tags": [], "metadata": metadata or {}}
    manager.store(**record, memory_type="semantic", update_index=True)
    return manager.semantic.get_all()[-1].get("id", "")


# ── unit tests for helpers ────────────────────────────────────────────

class TestEntityExtraction:
    """Tests for _extract_entities and _extract_attributes helpers."""

    def test_extract_capitalized_names(self):
        entities = _extract_entities("Alice met Bob in Shanghai.")
        assert "alice" in entities
        assert "bob" in entities
        assert "shanghai" in entities

    def test_extract_mentions(self):
        entities = _extract_entities("Hey @Peter, check this out.")
        assert "peter" in entities

    def test_extract_key_value(self):
        entities = _extract_entities("city: Beijing company: AcmeCorp age: 30")
        assert "beijing" in entities
        assert "acmecorp" in entities

    def test_extract_attributes(self):
        attrs = _extract_attributes("location: Beijing, age: 30, status: active")
        assert attrs["location"] == "Beijing"
        assert attrs["age"] == "30"
        assert attrs["status"] == "active"

    def test_no_duplicates(self):
        entities = _extract_entities("Alice Bob")  # pattern matches compound names
        assert len(entities) == 1  # "alice bob" matched as one compound
        entities2 = _extract_entities("Alice x Bob")  # non-capital word breaks the compound
        assert len(entities2) == 2


class TestDataTypes:
    """ConflictReport and ConflictResolution dataclass tests."""

    def test_conflict_report_defaults(self):
        cr = ConflictReport(
            conflict_type="entity",
            memory_id_a="id1",
            memory_id_b="id2",
            content_a="a",
            content_b="b",
        )
        assert cr.conflict_type == "entity"
        assert not cr.resolved
        assert cr.resolution is None

    def test_conflict_report_to_dict(self):
        cr = ConflictReport("entity", "id1", "id2", "a", "b",
                           similarity=0.85, resolved=True,
                           resolution=ConflictResolution(action="keep_a",
                                                         winner_id="id1",
                                                         reasoning="More specific"))
        d = cr.to_dict()
        assert d["conflict_type"] == "entity"
        assert d["similarity"] == 0.85
        assert d["resolved"] is True
        assert d["resolution"]["action"] == "keep_a"

    def test_conflict_resolution_defaults(self):
        r = ConflictResolution(action="merge")
        assert r.action == "merge"
        assert r.winner_id == ""
        assert r.merged_content == ""


# ── detector integration tests ────────────────────────────────────────

class TestConflictDetector:
    """Integration tests for ConflictDetector."""

    def test_empty_store_no_conflicts(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            mock_llm = _MockLLMProvider()
            detector = ConflictDetector(mgr, mock_llm)

            conflicts = detector.detect_conflicts()
            assert conflicts == []

    def test_single_memory_no_conflicts(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Only one memory.")
            mock_llm = _MockLLMProvider()
            detector = ConflictDetector(mgr, mock_llm)

            conflicts = detector.detect_conflicts()
            assert conflicts == []

    def test_entity_attribute_conflict(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "John location: New York age: 30")
            _store_semantic(mgr, "John location: Boston age: 30")
            mock_llm = _MockLLMProvider()
            detector = ConflictDetector(mgr, mock_llm)

            conflicts = detector.detect_conflicts()
            entity_conflicts = [c for c in conflicts if c.conflict_type == "entity"]
            assert len(entity_conflicts) >= 1
            assert "location" in entity_conflicts[0].description.lower()

    def test_semantic_conflict_with_high_similarity(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Python is easy to learn.")
            _store_semantic(mgr, "Python is difficult to master.")

            mock_llm = _MockLLMProvider(["YES", "A"])
            mock_emb = _MockEmbeddingService({
                "Python is easy to learn.": [1.0] * 16,
                "Python is difficult to master.": [0.95] * 16,
            })
            detector = ConflictDetector(mgr, mock_llm, mock_emb, sim_threshold=0.7)

            conflicts = detector.detect_conflicts()
            sem_conflicts = [c for c in conflicts if c.conflict_type == "semantic"]
            assert len(sem_conflicts) >= 1

    def test_no_semantic_conflict_below_threshold(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Python programming.")
            _store_semantic(mgr, "Italian cuisine.")

            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService({
                "Python programming.": [1.0] * 16,
                "Italian cuisine.": [-1.0] * 16,
            })
            detector = ConflictDetector(mgr, mock_llm, mock_emb, sim_threshold=0.7)

            conflicts = detector.detect_conflicts()
            sem_conflicts = [c for c in conflicts if c.conflict_type == "semantic"]
            assert sem_conflicts == []

    def test_deprecated_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "A fact about X.", metadata={"deprecated": "true"})
            _store_semantic(mgr, "Another fact about X.")
            mock_llm = _MockLLMProvider()
            detector = ConflictDetector(mgr, mock_llm)

            conflicts = detector.detect_conflicts()
            # Only 1 active memory → can't form pairs
            assert len(conflicts) == 0


class TestResolveConflict:
    """Conflict resolution tests."""

    def test_resolve_keep_a(self):
        cr = ConflictReport("entity", "id_a", "id_b",
                           "Alice is 30.", "Alice is 25.",
                           description="age mismatch")
        mock_llm = _MockLLMProvider(["A"])
        detector = ConflictDetector(None, mock_llm)

        resolution = detector.resolve_conflict(cr)
        assert resolution.action == "keep_a"
        assert resolution.winner_id == "id_a"

    def test_resolve_keep_b(self):
        cr = ConflictReport("entity", "id_a", "id_b",
                           "Alice is 30.", "Alice is 25.")
        mock_llm = _MockLLMProvider(["B"])
        detector = ConflictDetector(None, mock_llm)

        resolution = detector.resolve_conflict(cr)
        assert resolution.action == "keep_b"
        assert resolution.winner_id == "id_b"

    def test_resolve_merge_default(self):
        cr = ConflictReport("entity", "id_a", "id_b",
                           "Alice is 30.", "Alice is 25.")
        mock_llm = _MockLLMProvider(["X"])  # not A or B → merge
        detector = ConflictDetector(None, mock_llm)

        resolution = detector.resolve_conflict(cr)
        assert resolution.action == "merge"


class TestRunCycle:
    """run_cycle() integration tests."""

    def test_cycle_returns_stats(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "John location: New York")
            _store_semantic(mgr, "John location: Boston")
            mock_llm = _MockLLMProvider(["A"])
            detector = ConflictDetector(mgr, mock_llm)

            stats = detector.run_cycle()
            assert "conflicts_detected" in stats
            assert "conflicts_resolved" in stats
            assert "by_type" in stats
            assert "duration_ms" in stats
            assert stats["conflicts_detected"] >= 0

    def test_history_tracking(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "John location: New York")
            _store_semantic(mgr, "John location: Boston")
            mock_llm = _MockLLMProvider(["A"])
            detector = ConflictDetector(mgr, mock_llm)

            detector.run_cycle()
            history = detector.get_history()
            assert len(history) >= 1

            detector.clear_history()
            assert detector.get_history() == []

    def test_detector_repr(self):
        detector = ConflictDetector(None, None, sim_threshold=0.75)
        assert "0.75" in repr(detector)
