"""Tests for LearningToRankReranker module (P0-1 Stage 3)"""

import pytest
from claw_mem.retrieval.query_understanding import QueryUnderstanding, QueryIntent, ExpandedQuery
from claw_mem.retrieval.multi_strategy_retriever import Candidate
from claw_mem.retrieval.learning_to_rank import (
    LearningToRankReranker,
    RankingFeatures,
    Result,
)

SAMPLE_CANDIDATES = [
    Candidate(
        "mem-1",
        "Python performance optimization with caching techniques",
        0.9,
        "bm25",
        {"timestamp": "2025-05-14T10:00:00", "access_count": 15, "tags": ["python", "performance"]},
    ),
    Candidate(
        "mem-2",
        "claw-mem architecture and memory system",
        0.7,
        "bm25",
        {"timestamp": "2025-05-10T10:00:00", "access_count": 5, "tags": ["architecture"]},
    ),
    Candidate(
        "mem-3",
        "old deployment process documentation",
        0.5,
        "graph",
        {"timestamp": "2024-01-01T00:00:00", "access_count": 2, "tags": ["deployment"]},
    ),
    Candidate(
        "mem-4",
        "AI model training pipeline with RL",
        0.6,
        "bm25",
        {"timestamp": "2025-05-13T10:00:00", "access_count": 20, "tags": ["ai", "rl"]},
    ),
]


class TestRankingFeatures:
    def test_default_creation(self):
        rf = RankingFeatures()
        assert rf.bm25_score == 0.0
        assert rf.recency_score == 0.0
        assert rf.frequency_score == 0.0
        assert rf.concept_similarity == 0.0
        assert rf.query_content_similarity == 0.0

    def test_custom_values(self):
        rf = RankingFeatures(bm25_score=0.8, recency_score=0.7)
        assert rf.bm25_score == 0.8
        assert rf.recency_score == 0.7


class TestResult:
    def test_default_creation(self):
        r = Result(memory_id="id", content="content", score=0.5, rank=1)
        assert r.memory_id == "id"
        assert r.score == 0.5
        assert r.rank == 1

    def test_to_dict(self):
        r = Result(memory_id="id", content="content", score=0.5, rank=1)
        d = r.to_dict()
        assert d["memory_id"] == "id"
        assert d["rank"] == 1
        assert "features" in d


class TestLearningToRankReranker:
    @pytest.fixture
    def reranker(self):
        return LearningToRankReranker()

    @pytest.fixture
    def query(self):
        qu = QueryUnderstanding()
        return qu.understand("Python performance AI")

    def test_default_weights(self, reranker):
        weights = reranker.get_weights()
        assert "bm25_score" in weights
        assert "recency_score" in weights
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Should sum to ~1

    def test_rerank_basic(self, reranker, query):
        results = reranker.rerank(query, SAMPLE_CANDIDATES, top_k=3)
        assert isinstance(results, list)
        assert len(results) >= 1
        assert len(results) <= 3
        assert all(isinstance(r, Result) for r in results)

    def test_rerank_sorted_by_score(self, reranker, query):
        results = reranker.rerank(query, SAMPLE_CANDIDATES, top_k=10)
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_rerank_ranks_assigned(self, reranker, query):
        results = reranker.rerank(query, SAMPLE_CANDIDATES, top_k=3)
        for r in results:
            assert r.rank >= 1

    def test_rerank_empty_candidates(self, reranker, query):
        results = reranker.rerank(query, [], top_k=3)
        assert len(results) == 0

    def test_rerank_single_candidate(self, reranker, query):
        results = reranker.rerank(query, [SAMPLE_CANDIDATES[0]], top_k=5)
        assert len(results) == 1

    def test_extract_features(self, reranker, query):
        features = reranker.extract_features(query, SAMPLE_CANDIDATES[0])
        assert isinstance(features, RankingFeatures)
        assert features.bm25_score > 0
        assert 0 <= features.recency_score <= 1
        assert 0 <= features.frequency_score <= 1

    def test_weights_customizable(self):
        custom_weights = {
            "bm25_score": 0.5,
            "recency_score": 0.3,
            "frequency_score": 0.1,
            "concept_similarity": 0.05,
            "query_content_similarity": 0.03,
            "interaction_score": 0.01,
            "length_normalization": 0.005,
            "tag_match_score": 0.005,
        }
        reranker = LearningToRankReranker(weights=custom_weights)
        assert reranker.get_weights()["bm25_score"] == 0.5

    def test_set_weights(self, reranker):
        reranker.set_weights({"bm25_score": 1.0, "recency_score": 0.0})
        assert reranker.get_weights()["bm25_score"] == 1.0

    def test_record_feedback(self, reranker, query):
        reranker.record_feedback("mem-1", "query-1", clicked=True, relevance=0.9)
        assert reranker.get_statistics()["feedback_events"] >= 1

    def test_record_multiple_feedback_triggers_learning(self, reranker):
        for i in range(12):
            reranker.record_feedback(f"mem-{i % 4}", "query-1", clicked=True, relevance=0.8)
        stats = reranker.get_statistics()
        assert stats["feedback_events"] >= 10

    def test_get_statistics(self, reranker, query):
        reranker.rerank(query, SAMPLE_CANDIDATES)
        stats = reranker.get_statistics()
        assert stats["sessions"] >= 1
        assert stats["reranked"] >= 1

    def test_rerank_result_fields(self, reranker, query):
        results = reranker.rerank(query, SAMPLE_CANDIDATES, top_k=2)
        for r in results:
            assert r.memory_id
            assert r.content
            assert 0 <= r.score <= 1
            assert r.features.bm25_score > 0
            assert r.features.recency_score >= 0

    def test_frequency_score_zero(self, reranker):
        """Access count 0 should give frequency score 0."""
        cand = Candidate(
            "test", "content", 0.5, "bm25", {"access_count": 0, "timestamp": "2025-05-14T10:00:00"}
        )
        features = reranker.extract_features(
            ExpandedQuery("test", "test", QueryIntent.FACT, []), cand
        )
        assert features.frequency_score == 0.0


class TestFeatureExtractionEdgeCases:
    @pytest.fixture
    def reranker(self):
        return LearningToRankReranker()

    def test_no_timestamp(self, reranker):
        features = reranker.extract_features(
            ExpandedQuery("test", "test", QueryIntent.FACT, []),
            Candidate("id", "content", 0.5, "bm25", {"timestamp": ""}),
        )
        assert features.recency_score >= 0

    def test_no_tags(self, reranker):
        features = reranker.extract_features(
            ExpandedQuery("test", "test", QueryIntent.FACT, ["entity1"]),
            Candidate("id", "content", 0.5, "bm25", {}),
        )
        assert features.tag_match_score >= 0

    def test_very_short_content_length_norm(self, reranker):
        features = reranker.extract_features(
            ExpandedQuery("test", "test", QueryIntent.FACT, []),
            Candidate("id", "hi", 0.5, "bm25", {}),
        )
        assert features.length_normalization < 0.5

    def test_very_long_content_length_norm(self, reranker):
        features = reranker.extract_features(
            ExpandedQuery("test", "test", QueryIntent.FACT, []),
            Candidate("id", "x " * 3000, 0.5, "bm25", {}),
        )
        assert features.length_normalization < 0.5

    def test_normal_content_length_norm(self, reranker):
        features = reranker.extract_features(
            ExpandedQuery("test", "test", QueryIntent.FACT, []),
            Candidate("id", "x " * 100, 0.5, "bm25", {}),
        )
        assert features.length_normalization > 0.5
