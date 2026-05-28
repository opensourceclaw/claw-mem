# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Tests for the Dreaming Engine (v4.12.0)

Covers all four phases (light, deep, REM, promote) and the full pipeline.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claw_mem.dreaming.config import DreamingConfig
from claw_mem.dreaming.light import Signal, SignalIngestor
from claw_mem.dreaming.deep import CandidateScorer, ScoredCandidate
from claw_mem.dreaming.rem import PatternExtractor, REMResult
from claw_mem.dreaming.promote import Promoter, PromotionResult
from claw_mem.dreaming.pipeline import DreamingPipeline, DreamingResult


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture
def tmp_workspace():
    """Create a temporary workspace for storage-backed tests."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def mock_mm():
    """Create a mock MemoryManager with mocked storage backends."""
    mm = MagicMock()
    mm.episodic.get_recent.return_value = []
    mm.semantic.get_all.return_value = []
    mm.procedural.store = MagicMock()
    mm.semantic.store = MagicMock()
    mm.semantic.update = MagicMock()
    mm.skill_store = MagicMock()
    return mm


@pytest.fixture
def sample_signals():
    """Create a set of sample staged signals."""
    return [
        Signal(
            memory_id="sig1",
            content="Python: async programming patterns",
            memory_type="episodic",
            recall_count=5,
            unique_queries=3,
            relevance_scores=[0.7, 0.8, 0.6],
            tags=["python", "async"],
            timestamp="2026-05-29T10:00:00",
        ),
        Signal(
            memory_id="sig2",
            content="Database optimization: indexing strategies",
            memory_type="episodic",
            recall_count=3,
            unique_queries=2,
            relevance_scores=[0.6],
            tags=["database", "optimization"],
            timestamp="2026-05-28T08:00:00",
        ),
        Signal(
            memory_id="sig3",
            content="short msg",
            memory_type="episodic",
            recall_count=1,
            unique_queries=0,
            relevance_scores=[0.3],
            tags=[],
            timestamp="2026-05-20T00:00:00",
        ),
    ]


# ═══════════════════════════════════════════════════════════════════
# Test: DreamingConfig
# ═══════════════════════════════════════════════════════════════════

class TestDreamingConfig:
    def test_default_weights_sum_to_one(self):
        config = DreamingConfig()
        assert config.validate()

    def test_custom_weights_validation(self):
        config = DreamingConfig(
            frequency_weight=0.5,
            relevance_weight=0.5,
            query_diversity_weight=0.0,
            recency_weight=0.0,
            consolidation_weight=0.0,
            conceptual_richness_weight=0.0,
        )
        assert config.validate()

    def test_invalid_weights(self):
        config = DreamingConfig(frequency_weight=0.9)
        assert not config.validate()


# ═══════════════════════════════════════════════════════════════════
# Test: SignalIngestor (Light Phase)
# ═══════════════════════════════════════════════════════════════════

class TestSignalIngestor:
    def test_ingest_empty(self, mock_mm):
        ingestor = SignalIngestor(mock_mm)
        count = ingestor.ingest()
        assert count == 0
        assert ingestor.get_staged() == []

    def test_ingest_with_memories(self, mock_mm):
        mock_mm.episodic.get_recent.return_value = [
            {"id": "m1", "content": "User likes Python", "type": "episodic",
             "tags": ["preference"], "timestamp": "2026-05-29T00:00:00"},
            {"id": "m2", "content": "Project uses FastAPI", "type": "episodic",
             "tags": ["tech"], "timestamp": "2026-05-29T01:00:00"},
        ]

        ingestor = SignalIngestor(mock_mm)
        count = ingestor.ingest()
        assert count == 2

        staged = ingestor.get_staged()
        assert len(staged) == 2
        assert staged[0]["content"] == "User likes Python"

    def test_ingest_deduplicates_semantic(self, mock_mm):
        mock_mm.episodic.get_recent.return_value = [
            {"id": "m1", "content": "User likes Python", "type": "episodic",
             "tags": [], "timestamp": ""},
        ]
        mock_mm.semantic.get_all.return_value = [
            {"content": "User likes Python"},  # exact match → dedup
        ]

        ingestor = SignalIngestor(mock_mm)
        count = ingestor.ingest()
        assert count == 0

    def test_get_staged_and_clear(self, mock_mm):
        mock_mm.episodic.get_recent.return_value = [
            {"id": "m1", "content": "Test memory", "type": "episodic",
             "tags": [], "timestamp": ""},
        ]

        ingestor = SignalIngestor(mock_mm)
        ingestor.ingest()
        assert len(ingestor.get_staged()) == 1

        ingestor.clear_staged()
        assert ingestor.get_staged() == []

    def test_ingest_respects_max_staged(self, mock_mm):
        all_memories = [
            {"id": f"m{i}", "content": f"Memory {i}", "type": "episodic",
             "tags": [], "timestamp": ""}
            for i in range(100)
        ]
        mock_mm.episodic.get_recent.side_effect = lambda limit: all_memories[:limit]

        ingestor = SignalIngestor(mock_mm, DreamingConfig(max_staged=50))
        ingestor.ingest()
        assert len(ingestor._staged) == 50


# ═══════════════════════════════════════════════════════════════════
# Test: CandidateScorer (Deep Phase)
# ═══════════════════════════════════════════════════════════════════

class TestCandidateScorer:
    def test_score_all(self, sample_signals):
        scorer = CandidateScorer()
        candidates = scorer.score_all(sample_signals)

        assert len(candidates) == 3
        # Sorted by composite descending
        assert candidates[0].composite >= candidates[1].composite >= candidates[2].composite

    def test_scores_in_range(self, sample_signals):
        scorer = CandidateScorer()
        candidates = scorer.score_all(sample_signals)

        for c in candidates:
            assert 0.0 <= c.frequency_score <= 1.0
            assert 0.0 <= c.relevance_score <= 1.0
            assert 0.0 <= c.query_diversity_score <= 1.0
            assert 0.0 <= c.recency_score <= 1.0
            assert 0.0 <= c.consolidation_score <= 1.0
            assert 0.0 <= c.conceptual_richness_score <= 1.0
            assert 0.0 <= c.composite <= 1.0

    def test_filter_by_threshold(self, sample_signals):
        scorer = CandidateScorer(DreamingConfig(score_threshold=1.0))
        candidates = scorer.score_all(sample_signals)
        passed = scorer.filter(candidates)
        assert len(passed) == 0

    def test_filter_returns_top_k(self, sample_signals):
        scorer = CandidateScorer(
            DreamingConfig(score_threshold=0.1, top_k_candidates=1)
        )
        candidates = scorer.score_all(sample_signals)
        passed = scorer.filter(candidates)
        assert len(passed) == 1

    def test_scored_candidate_to_dict(self, sample_signals):
        scorer = CandidateScorer()
        [c] = scorer.score_all([sample_signals[0]])
        d = c.to_dict()
        assert "signal" in d
        assert "composite" in d
        assert "frequency_score" in d

    def test_empty_signals(self):
        scorer = CandidateScorer()
        candidates = scorer.score_all([])
        assert len(candidates) == 0

    def test_signal_with_default_relevance(self):
        """Signal with no relevance_scores gets default 0.5."""
        sig = Signal(
            memory_id="s", content="test", relevance_scores=[],
            recall_count=1, unique_queries=0, tags=[], timestamp="",
        )
        scorer = CandidateScorer()
        [c] = scorer.score_all([sig])
        assert c.relevance_score == 0.5


# ═══════════════════════════════════════════════════════════════════
# Test: PatternExtractor (REM Phase)
# ═══════════════════════════════════════════════════════════════════

class TestPatternExtractor:
    def test_extract_from_candidates(self, sample_signals):
        scorer = CandidateScorer()
        candidates = scorer.score_all(sample_signals)

        extractor = PatternExtractor()
        result = extractor.extract(candidates)

        assert isinstance(result, REMResult)
        assert result.extracted_count == 3
        assert len(result.triplets) == 3
        assert isinstance(result.topic_summaries, dict)

    def test_extract_empty(self):
        extractor = PatternExtractor()
        result = extractor.extract([])
        assert result.extracted_count == 0
        assert result.triplets == []

    def test_rem_result_to_dict(self, sample_signals):
        scorer = CandidateScorer()
        candidates = scorer.score_all(sample_signals)
        extractor = PatternExtractor()
        result = extractor.extract(candidates)
        d = result.to_dict()
        assert "extracted_count" in d
        assert "triplets" in d
        assert "topic_summaries" in d


# ═══════════════════════════════════════════════════════════════════
# Test: Promoter (Promote Phase)
# ═══════════════════════════════════════════════════════════════════

class TestPromoter:
    def test_promote_dry_run(self, mock_mm, sample_signals):
        scorer = CandidateScorer()
        candidates = scorer.score_all(sample_signals)
        extractor = PatternExtractor()
        rem_result = extractor.extract(candidates)

        promoter = Promoter(mock_mm, dry_run=True)
        result = promoter.promote(candidates, rem_result)

        assert result.dry_run is True
        assert result.episodic_promoted == 3  # all are episodic
        # Dry run should not call storage
        mock_mm.semantic.store.assert_not_called()

    def test_promote_live(self, mock_mm, sample_signals):
        scorer = CandidateScorer()
        candidates = scorer.score_all(sample_signals)
        extractor = PatternExtractor()
        rem_result = extractor.extract(candidates)

        promoter = Promoter(mock_mm, dry_run=False)
        result = promoter.promote(candidates, rem_result)

        assert result.dry_run is False
        assert result.episodic_promoted > 0

    def test_promotion_result_to_dict(self):
        result = PromotionResult(
            episodic_promoted=3,
            semantic_reinforced=1,
            procedural_promoted=0,
            skill_stored=2,
        )
        d = result.to_dict()
        assert d["episodic_promoted"] == 3
        assert d["total"] == 4

    def test_promote_empty(self, mock_mm):
        extractor = PatternExtractor()
        rem_result = extractor.extract([])

        promoter = Promoter(mock_mm)
        result = promoter.promote([], rem_result)
        assert result.total == 0


# ═══════════════════════════════════════════════════════════════════
# Test: DreamingPipeline (End-to-End)
# ═══════════════════════════════════════════════════════════════════

class TestDreamingPipeline:
    def test_pipeline_dry_run(self, mock_mm):
        mock_mm.episodic.get_recent.return_value = [
            {"id": "m1", "content": "Python async patterns",
             "type": "episodic", "tags": ["python"], "timestamp": "2026-05-29T00:00:00"},
            {"id": "m2", "content": "Database indexing guide",
             "type": "episodic", "tags": ["db"], "timestamp": "2026-05-28T00:00:00"},
        ]

        config = DreamingConfig(dry_run=True, score_threshold=0.0)
        pipeline = DreamingPipeline(mock_mm, config=config)
        result = pipeline.run()

        assert isinstance(result, DreamingResult)
        assert result.dry_run is True
        assert result.staged >= 0
        assert result.duration_ms >= 0

    def test_pipeline_empty(self, mock_mm):
        """Pipeline on empty storage should produce zero results without error."""
        mock_mm.episodic.get_recent.return_value = []

        pipeline = DreamingPipeline(mock_mm)
        result = pipeline.run()

        assert result.staged == 0
        assert result.error is None

    def test_pipeline_last_result(self, mock_mm):
        mock_mm.episodic.get_recent.return_value = [
            {"id": "m1", "content": "Memory test",
             "type": "episodic", "tags": [], "timestamp": ""},
        ]

        config = DreamingConfig(dry_run=True, score_threshold=1.0)
        pipeline = DreamingPipeline(mock_mm, config=config)

        assert pipeline.last_result() is None
        pipeline.run()
        assert pipeline.last_result() is not None

    def test_result_to_dict(self):
        result = DreamingResult(
            staged=10, scored=10, passed=5, promoted=3,
            skills_stored=1, duration_ms=42.5, dry_run=True,
        )
        d = result.to_dict()
        assert d["staged"] == 10
        assert d["passed"] == 5
        assert d["promoted"] == 3
        assert d["dry_run"] is True
