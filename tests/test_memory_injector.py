"""Tests for MemoryInjector + InjectorResult (F1 · v4.9.0)."""

import tempfile
from unittest.mock import MagicMock

import pytest

from claw_mem.context.confidence_gate import ConfidenceGate
from claw_mem.context.memory_injector import (
    InjectorResult,
    MemoryInjector,
    _jaccard_similarity,
)


# ── helpers ───────────────────────────────────────────────────────────

def _make_gate(keep_all: bool = True):
    """Return a ConfidenceGate that either keeps everything or drops nothing."""
    if keep_all:
        gate = MagicMock(spec=ConfidenceGate)
        gate.filter.side_effect = lambda memories: memories
        return gate
    else:
        gate = ConfidenceGate(low_threshold=0.9)
        return gate


def _make_manager(workspace_dir: str):
    from claw_mem.memory_manager import MemoryManager
    return MemoryManager(
        workspace=workspace_dir,
        enable_graph=False,
        enable_decay=False,
        enable_ground_truth=False,
        enable_merge=False,
        enable_conflict_detect=False,
        enable_tiered_decay=False,
    )


def _memory(content, score=0.8, mem_id=None, created_at=None):
    import uuid
    return {
        "id": mem_id or str(uuid.uuid4()),
        "content": content,
        "score": score,
        "created_at": created_at,
    }


def _store_semantic(manager, content, tags=None, metadata=None):
    record = {"content": content, "tags": tags or [], "metadata": metadata or {}}
    manager.store(**record, memory_type="semantic", update_index=True)
    memories = manager.semantic.get_all()
    return memories[-1].get("id", "")


# ── Jaccard similarity ────────────────────────────────────────────────

class TestJaccardSimilarity:
    def test_identical(self):
        assert _jaccard_similarity("hello world", "hello world") == 1.0

    def test_disjoint(self):
        assert _jaccard_similarity("hello world", "foo bar baz") == 0.0

    def test_partial_overlap(self):
        sim = _jaccard_similarity("hello world foo", "hello world bar")
        # tokens: {hello, world, foo} ∩ {hello, world, bar} = {hello, world}
        # union: {hello, world, foo, bar} → 2/4 = 0.5
        assert sim == pytest.approx(0.5)

    def test_empty_string(self):
        assert _jaccard_similarity("", "hello") == 0.0
        assert _jaccard_similarity("hello", "") == 0.0
        assert _jaccard_similarity("", "") == 0.0

    def test_cjk_characters(self):
        # "你好世界" → {"你","好","世","界"} ; "你好" → {"你","好"}
        sim = _jaccard_similarity("你好世界", "你好")
        assert sim == pytest.approx(0.5)  # 2/4

    def test_mixed_cjk_and_ascii(self):
        sim = _jaccard_similarity("hello 世界", "hello 你好")
        # {hello, 世, 界} ∩ {hello, 你, 好} = {hello} → 1/5
        assert sim == pytest.approx(1.0 / 5.0)

    def test_case_insensitive(self):
        assert _jaccard_similarity("Hello World", "hello world") == 1.0


# ── InjectorResult ────────────────────────────────────────────────────

class TestInjectorResult:
    def test_defaults(self):
        r = InjectorResult(
            refined_memories=[], total_candidates=10, total_removed=2,
            total_tokens=500, max_allowed=2000,
        )
        assert r.passed == 0
        assert r.total_candidates == 10
        assert r.total_removed == 2

    def test_with_memories(self):
        r = InjectorResult(
            refined_memories=[_memory("a"), _memory("b")],
            total_candidates=5, total_removed=3, total_tokens=100,
            max_allowed=2000, budget_exceeded=False, diversity_removed=2,
            threshold_removed=1,
        )
        assert r.passed == 2
        assert r.diversity_removed == 2
        assert r.threshold_removed == 1
        assert not r.budget_exceeded


# ── MemoryInjector ────────────────────────────────────────────────────

class TestRefinePipeline:
    def test_empty_input(self):
        injector = MemoryInjector(confidence_gate=_make_gate())
        result = injector.refine([])
        assert result.refined_memories == []
        assert result.total_candidates == 0
        assert result.total_removed == 0

    def test_single_memory_passes_through(self):
        injector = MemoryInjector(confidence_gate=_make_gate())
        mem = _memory("hello world", score=0.8)
        result = injector.refine([mem])
        assert len(result.refined_memories) == 1
        assert result.total_candidates == 1
        assert result.total_removed == 0

    def test_stages_metadata(self):
        injector = MemoryInjector(confidence_gate=_make_gate())
        result = injector.refine([_memory("hello", score=0.8)])
        stages = result.metadata.get("stages", [])
        stage_names = [s["name"] for s in stages]
        assert stage_names == [
            "confidence_gate", "relevance_threshold",
            "diversity_dedup", "sort", "token_budget",
        ]

    def test_confidence_gate_skipped_when_disabled(self):
        injector = MemoryInjector(confidence_gate=_make_gate(), enable_confidence_gate=False)
        result = injector.refine([_memory("hello")])
        stage = result.metadata["stages"][0]
        assert stage["name"] == "confidence_gate"
        assert stage.get("skipped") is True


class TestRelevanceThreshold:
    def test_drops_below_threshold(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), relevance_threshold=0.5,
        )
        result = injector.refine([
            _memory("high", score=0.9),
            _memory("low", score=0.1),
        ])
        assert result.threshold_removed == 1
        contents = [m["content"] for m in result.refined_memories]
        assert "high" in contents
        assert "low" not in contents

    def test_keeps_no_score(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), relevance_threshold=0.5,
        )
        result = injector.refine([_memory("unknown", score=None)])
        assert result.threshold_removed == 0
        assert len(result.refined_memories) == 1


class TestDiversityDedup:
    def test_dedup_near_identical(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), diversity_threshold=0.5,
        )
        result = injector.refine([
            _memory("the quick brown fox jumps over the lazy dog", score=0.8),
            _memory("the quick brown fox jumps over the lazy dog", score=0.7),
        ])
        assert result.diversity_removed == 1
        assert len(result.refined_memories) == 1

    def test_keeps_different(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), diversity_threshold=0.8,
        )
        result = injector.refine([
            _memory("apple banana cherry", score=0.9),
            _memory("dog cat mouse", score=0.8),
        ])
        assert result.diversity_removed == 0
        assert len(result.refined_memories) == 2

    def test_single_memory_no_dedup(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), diversity_threshold=0.5,
        )
        result = injector.refine([_memory("unique content")])
        assert result.diversity_removed == 0


class TestTokenBudget:
    def test_budget_exceeded(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), max_tokens=5,
        )
        # "hello world and more text here" → ~12 chars / 4 ≈ 3 tokens, fits but can't fit 4 items
        result = injector.refine([
            _memory("hello world and more text here", score=0.9),
            _memory("hello world and more text here", score=0.8),
            _memory("hello world and more text here", score=0.7),
            _memory("hello world and more text here", score=0.6),
        ])
        assert result.budget_exceeded
        assert len(result.refined_memories) < 4

    def test_single_item_always_kept(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), max_tokens=1,
        )
        result = injector.refine([
            _memory("a long piece of text that exceeds budget", score=0.9),
        ])
        assert len(result.refined_memories) == 1  # Single item always kept

    def test_total_tokens_estimated(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), max_tokens=1000,
        )
        result = injector.refine([
            _memory("hello world", score=0.9),
        ])
        assert result.total_tokens > 0


class TestRecencySort:
    def test_recency_sorting(self):
        """High-score second item should sort before low-score first."""
        injector = MemoryInjector(
            confidence_gate=_make_gate(),
            recency_weight=0.0,  # disable recency to test pure relevance
            relevance_weight=1.0,
        )
        result = injector.refine([
            _memory("item a", score=0.3),
            _memory("item b", score=0.9),
            _memory("item c", score=0.5),
        ])
        scores = [m["score"] for m in result.refined_memories]
        assert scores == [0.9, 0.5, 0.3]  # descending by score due to relevance_weight=1.0


class TestLocalJaccardCjk:
    """Integration-style tests for Jaccard on CJK content (no manager needed)."""

    def test_chinese_near_duplicate(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), diversity_threshold=0.3,
        )
        result = injector.refine([
            _memory("今天天气很好 适合出去玩", score=0.8),
            _memory("今天天气很好 适合出去走走", score=0.7),
        ])
        # Many overlapping tokens → should dedup
        assert result.diversity_removed == 1
        assert len(result.refined_memories) == 1

    def test_chinese_different_topics(self):
        injector = MemoryInjector(
            confidence_gate=_make_gate(), diversity_threshold=0.5,
        )
        result = injector.refine([
            _memory("Python是一门编程语言", score=0.8),
            _memory("今天天气很好 适合出去玩", score=0.7),
        ])
        assert result.diversity_removed == 0
        assert len(result.refined_memories) == 2
