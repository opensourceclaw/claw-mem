"""Tests for SemanticMergeScheduler (F1 · v4.7.0)."""

import tempfile
from unittest.mock import MagicMock, patch

import pytest

from claw_mem.llm_provider import LLMProvider
from claw_mem.merge.semantic_merger import SemanticMergeScheduler
from claw_mem.memory_manager import MemoryManager


# ── mock helpers ──────────────────────────────────────────────────────

class _MockLLMProvider:
    """Returns preset merged text for each pair."""

    def __init__(self, merged_text: str = "MERGED_CONTENT"):
        self._merged = merged_text
        self.calls: list = []

    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        self.calls.append((prompt, system, max_tokens))
        return self._merged

    def health_check(self) -> bool:
        return True


class _MockEmbeddingService:
    """Returns simple fixed-dim vectors. The test controls similarity via vector content."""

    def __init__(self, vectors: dict = None):
        # string → vector mapping; unknown strings get [1.0] * 16
        self._vecs = vectors or {}
        self._default_dim = 16

    def encode(self, texts, batch_size=32):
        from typing import List as _List
        return [
            self._vecs.get(t, [1.0] * self._default_dim)
            for t in texts
        ]

    def encode_single(self, text):
        return self._vecs.get(text, [1.0] * self._default_dim)


def _make_manager(workspace_dir: str) -> MemoryManager:
    return MemoryManager(
        workspace=workspace_dir,
        enable_graph=False,
        enable_decay=False,
        enable_ground_truth=False,
    )


def _store_semantic(manager: MemoryManager, content: str, tags=None, metadata=None) -> str:
    record = {
        "content": content,
        "tags": tags or [],
        "metadata": metadata or {},
    }
    manager.store(**record, memory_type="semantic", update_index=True)
    # Read back to get auto-assigned ID
    memories = manager.semantic.get_all()
    return memories[-1].get("id", "")


# ── tests ─────────────────────────────────────────────────────────────

class TestFindMergeCandidates:
    """find_merge_candidates() tests."""

    def test_empty_store(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            candidates = scheduler.find_merge_candidates()
            assert candidates == []

    def test_single_memory_no_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "The sky is blue.")
            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            candidates = scheduler.find_merge_candidates()
            assert candidates == []

    def test_identical_memories_merge_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Python was created by Guido van Rossum.")
            _store_semantic(mgr, "Python was created by Guido van Rossum.")

            # Same text → same mock embedding → cosine = 1.0
            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            candidates = scheduler.find_merge_candidates()
            assert len(candidates) == 1
            sim = candidates[0][2]
            assert sim > 0.99  # essentially identical

    def test_dissimilar_memories_no_candidate(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "aaaa aaaa aaaa aaaa")
            _store_semantic(mgr, "zzzz zzzz zzzz zzzz")

            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService({
                "aaaa aaaa aaaa aaaa": [1.0] * 16,
                "zzzz zzzz zzzz zzzz": [-1.0] * 16,  # orthogonal → cos ≈ -1
            })
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            candidates = scheduler.find_merge_candidates()
            assert candidates == []

    def test_deprecated_memories_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Memory A content.", metadata={"deprecated": "true"})
            _store_semantic(mgr, "Memory A content.")  # similar but not deprecated

            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            candidates = scheduler.find_merge_candidates()
            # Only 1 active memory, so no pairs
            assert candidates == []

    def test_multiple_candidates_sorted_by_similarity(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "text A")
            _store_semantic(mgr, "text B")
            _store_semantic(mgr, "text C")

            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService({
                "text A": [1.0, 0.0, 0.0],
                "text B": [0.9, 0.0, 0.0],  # ≈0.99 with A
                "text C": [0.6, 0.0, 0.0],  # ≈0.8 with A, lower with B
            })
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            candidates = scheduler.find_merge_candidates()
            assert len(candidates) >= 1
            # Highest similarity pair should be first
            assert candidates[0][2] >= candidates[-1][2]


class TestMergePair:
    """merge_pair() tests."""

    def test_merge_stores_new_memory(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Python is a language.")
            _store_semantic(mgr, "Python is a programming language created by Guido.")

            mock_llm = _MockLLMProvider("Python is a programming language created by Guido van Rossum.")
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb)

            all_m = mgr.semantic.get_all()
            mem1, mem2 = all_m[0], all_m[1]
            result = scheduler.merge_pair(mem1, mem2, similarity=0.8)
            assert result is not None

            # Check merged memory content is stored
            all_m = mgr.semantic.get_all()
            contents = [m["content"] for m in all_m]
            assert any("Guido van Rossum" in c for c in contents)
            assert any("merged_from" in str(m.get("metadata", {})) for m in all_m)


class TestShouldRun:
    """should_run() tests."""

    def test_below_interval(self):
        mock_llm = _MockLLMProvider()
        scheduler = SemanticMergeScheduler(None, mock_llm, merge_interval=100)
        assert not scheduler.should_run(50)
        assert not scheduler.should_run(99)

    def test_at_interval(self):
        mock_llm = _MockLLMProvider()
        scheduler = SemanticMergeScheduler(None, mock_llm, merge_interval=100)
        assert scheduler.should_run(100)

    def test_multiple_of_interval(self):
        mock_llm = _MockLLMProvider()
        scheduler = SemanticMergeScheduler(None, mock_llm, merge_interval=100)
        assert scheduler.should_run(200)
        assert scheduler.should_run(300)


class TestRunMergeCycle:
    """run_merge_cycle() integration tests."""

    def test_empty_store_returns_stats(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            mock_llm = _MockLLMProvider()
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb)
            stats = scheduler.run_merge_cycle()
            assert stats["candidates_found"] == 0
            assert stats["merged_count"] == 0
            assert stats["errors"] == 0
            assert "duration_ms" in stats

    def test_cycle_merges_candidates(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "The capital of France is Paris.")
            _store_semantic(mgr, "The capital of France is Paris.")

            mock_llm = _MockLLMProvider("The capital of France is Paris.")
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            stats = scheduler.run_merge_cycle()
            assert stats["candidates_found"] == 1
            assert stats["merged_count"] == 1

    def test_llm_failure_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Memory one.")
            _store_semantic(mgr, "Memory one again.")

            class _FailingLLM:
                def generate(self, *args, **kwargs):
                    return ""  # LLM returns empty = failure

            mock_llm = _FailingLLM()
            mock_emb = _MockEmbeddingService()
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            stats = scheduler.run_merge_cycle()
            # Should not throw; just skip the failed merge
            assert stats["merged_count"] == 0

    def test_deprecated_mems_not_remerged(self):
        with tempfile.TemporaryDirectory() as d:
            mgr = _make_manager(d)
            _store_semantic(mgr, "Dep A content.", metadata={"deprecated": "true"})
            _store_semantic(mgr, "Active B content.")

            mock_llm = _MockLLMProvider("Merged.")
            mock_emb = _MockEmbeddingService({
                "Dep A content.": [1.0] * 16,
                "Active B content.": [1.0] * 16,
            })
            scheduler = SemanticMergeScheduler(mgr, mock_llm, mock_emb,
                                               med_sim_threshold=0.65)
            stats = scheduler.run_merge_cycle()
            # deprecated memories are filtered out → only 1 active → no pairs
            assert stats["candidates_found"] == 0
