"""Tests for MultiStrategyRetriever module (P0-1 Stage 2)"""

import time
import pytest
from claw_mem.retrieval.query_understanding import QueryUnderstanding, QueryIntent, ExpandedQuery
from claw_mem.retrieval.multi_strategy_retriever import (
    MultiStrategyRetriever,
    ConceptGraphTraverser,
    TemporalDecayWeighter,
    Candidate,
    RetrievalResult,
)

# Sample memory pool
SAMPLE_MEMORIES = [
    {
        "id": "mem-1",
        "content": "Python performance optimization with caching",
        "timestamp": "2025-05-10T10:00:00",
        "tags": ["python", "performance"],
        "memory_type": "semantic",
    },
    {
        "id": "mem-2",
        "content": "claw-mem memory system architecture design",
        "timestamp": "2025-05-12T10:00:00",
        "tags": ["architecture", "memory"],
        "memory_type": "semantic",
    },
    {
        "id": "mem-3",
        "content": "Python is the preferred language for AI projects",
        "timestamp": "2025-05-14T10:00:00",
        "tags": ["python", "preference"],
        "memory_type": "preference",
    },
    {
        "id": "mem-4",
        "content": "Git workflow and deployment process",
        "timestamp": "2025-05-01T10:00:00",
        "tags": ["git", "deployment"],
        "memory_type": "procedural",
    },
    {
        "id": "mem-5",
        "content": "container deployment with Docker and Kubernetes",
        "timestamp": "2025-05-13T10:00:00",
        "tags": ["docker", "kubernetes", "deployment"],
        "memory_type": "procedural",
    },
]


class TestCandidate:
    def test_default_creation(self):
        c = Candidate(
            memory_id="test-1",
            content="test content",
            score=0.8,
            source_strategy="bm25",
        )
        assert c.memory_id == "test-1"
        assert c.score == 0.8
        assert c.source_strategy == "bm25"

    def test_to_dict(self):
        c = Candidate("id", "content", 0.5, "bm25", {"key": "val"})
        d = c.to_dict()
        assert d["memory_id"] == "id"
        assert d["score"] == 0.5
        assert d["source_strategy"] == "bm25"


class TestRetrievalResult:
    def test_get_top(self):
        candidates = [
            Candidate("a", "aa", 0.3, "bm25"),
            Candidate("b", "bb", 0.9, "graph"),
            Candidate("c", "cc", 0.5, "bm25"),
        ]
        rr = RetrievalResult(
            candidates=candidates,
            total_candidates=3,
            strategies_used=["bm25", "graph"],
            fusion_method="weighted_sum",
        )
        top2 = rr.get_top(2)
        assert len(top2) == 2
        assert top2[0].score == 0.9
        assert top2[1].score == 0.5


class TestConceptGraphTraverser:
    def test_default_map(self):
        ct = ConceptGraphTraverser()
        concepts = ct._concept_map
        assert "python" in concepts
        assert "code" in concepts["python"]

    def test_add_concept(self):
        ct = ConceptGraphTraverser()
        ct.add_concept("rust", ["systems", "performance"])
        assert "rust" in ct._concept_map
        assert "systems" in ct._concept_map["rust"]

    def test_traverse_with_entities(self):
        ct = ConceptGraphTraverser()
        results = ct.traverse(["python"], SAMPLE_MEMORIES, depth=2)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_traverse_no_match(self):
        ct = ConceptGraphTraverser()
        results = ct.traverse(["nonexistent_xyz"], SAMPLE_MEMORIES, depth=2)
        assert len(results) == 0

    def test_traverse_max_results(self):
        ct = ConceptGraphTraverser()
        results = ct.traverse(["python", "memory"], SAMPLE_MEMORIES, depth=2, max_results=2)
        assert len(results) <= 2

    def test_traverse_zero_depth(self):
        ct = ConceptGraphTraverser()
        results = ct.traverse(["python"], SAMPLE_MEMORIES, depth=0, max_results=10)
        assert isinstance(results, list)


class TestTemporalDecayWeighter:
    def test_default_creation(self):
        tw = TemporalDecayWeighter()
        assert tw.base_half_life > 0
        assert tw.min_weight >= 0

    def test_compute_weight_recent(self):
        tw = TemporalDecayWeighter()
        now = time.time()
        recent_ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now - 60))
        weight = tw.compute_weight(recent_ts, now)
        assert weight >= 0.9  # Very recent, high weight

    def test_compute_weight_old(self):
        tw = TemporalDecayWeighter()
        now = time.time()
        old_ts = "2024-01-01T00:00:00"
        weight = tw.compute_weight(old_ts, now)
        assert weight <= 0.5  # Very old, low weight

    def test_compute_weight_none(self):
        tw = TemporalDecayWeighter()
        weight = tw.compute_weight(None)
        assert weight == 1.0

    def test_compute_weight_invalid(self):
        tw = TemporalDecayWeighter()
        weight = tw.compute_weight("not-a-timestamp")
        assert weight == 1.0

    def test_apply_decay(self):
        tw = TemporalDecayWeighter()
        candidates = [
            Candidate("a", "content a", 1.0, "bm25", {"timestamp": "2024-01-01T00:00:00"}),
            Candidate("b", "content b", 1.0, "bm25", {"timestamp": ""}),
        ]
        result = tw.apply_decay(candidates)
        assert len(result) == 2
        assert result[0].score < 1.0  # Old memory decayed
        assert "temporal_weight" in result[0].metadata


class TestMultiStrategyRetriever:
    @pytest.fixture
    def retriever(self):
        return MultiStrategyRetriever()

    @pytest.fixture
    def query(self):
        qu = QueryUnderstanding()
        return qu.understand("Python performance optimization")

    def test_retrieve_basic(self, retriever, query):
        result = retriever.retrieve(query, SAMPLE_MEMORIES, top_k=3)
        assert isinstance(result, RetrievalResult)
        assert len(result.candidates) >= 1
        assert "bm25" in result.strategies_used
        assert result.latency_ms >= 0

    def test_retrieve_with_entities(self, retriever):
        qu = QueryUnderstanding()
        query = qu.understand("Python memory system architecture")
        result = retriever.retrieve(query, SAMPLE_MEMORIES, top_k=3)
        assert len(result.candidates) > 0

    def test_retrieve_empty_pool(self, retriever):
        qu = QueryUnderstanding()
        query = qu.understand("test query")
        result = retriever.retrieve(query, [], top_k=3)
        assert len(result.candidates) == 0

    def test_retrieve_top_k_respect(self, retriever, query):
        result = retriever.retrieve(query, SAMPLE_MEMORIES, top_k=2)
        assert len(result.candidates) <= 2

    def test_retrieve_recent_intent_boost(self, retriever):
        qu = QueryUnderstanding()
        query = qu.understand("recent Docker deployments")
        assert query.intent == QueryIntent.RECENT
        result = retriever.retrieve(query, SAMPLE_MEMORIES, top_k=3)
        assert "intent_boost" in result.strategies_used

    def test_get_top_from_result(self, retriever, query):
        result = retriever.retrieve(query, SAMPLE_MEMORIES, top_k=3)
        top1 = result.get_top(1)
        assert len(top1) == 1
        assert top1[0].score >= 0

    def test_linear_query_returns_results(self, retriever):
        qu = QueryUnderstanding()
        query = qu.understand("Docker Kubernetes containers")
        result = retriever.retrieve(query, SAMPLE_MEMORIES, top_k=5)
        assert len(result.candidates) >= 1
