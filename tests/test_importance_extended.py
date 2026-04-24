"""
Extended tests for Importance Scoring

Tests importance scoring for memories.
"""

import pytest
from datetime import datetime, timedelta
from claw_mem.importance import (
    MemoryImportance,
    ImportanceScorer
)


class TestMemoryImportance:
    """Test MemoryImportance dataclass"""

    def test_initialization(self):
        """Test MemoryImportance initialization"""
        importance = MemoryImportance(
            base_score=1.0,
            type_weight=0.5,
            frequency_weight=0.3,
            recency_weight=0.2
        )

        assert importance.base_score == 1.0
        assert importance.type_weight == 0.5
        assert importance.frequency_weight == 0.3
        assert importance.recency_weight == 0.2

    def test_default_initialization(self):
        """Test MemoryImportance with defaults"""
        importance = MemoryImportance()

        assert importance.base_score == 1.0
        assert importance.type_weight == 0.0
        assert importance.frequency_weight == 0.0
        assert importance.recency_weight == 0.0
        assert importance.total_score == 1.0

    def test_calculate_total(self):
        """Test calculate_total method"""
        importance = MemoryImportance(
            base_score=1.0,
            type_weight=0.5,
            frequency_weight=0.3,
            recency_weight=0.2
        )

        total = importance.calculate_total()

        assert total == 2.0
        assert importance.total_score == 2.0

    def test_calculate_total_capped(self):
        """Test calculate_total caps at MAX_SCORE"""
        importance = MemoryImportance(
            base_score=1.0,
            type_weight=0.5,
            frequency_weight=0.3,
            recency_weight=0.5  # Would exceed 2.0
        )

        total = importance.calculate_total()

        assert total == 2.0  # Capped at MAX_SCORE


class TestImportanceScorer:
    """Test ImportanceScorer"""

    def test_initialization(self):
        """Test ImportanceScorer initialization"""
        scorer = ImportanceScorer()

        assert scorer.MAX_SCORE == 2.0
        assert scorer.TYPE_WEIGHTS['semantic'] == 0.5
        assert scorer.TYPE_WEIGHTS['procedural'] == 0.3
        assert scorer.TYPE_WEIGHTS['episodic'] == 0.0

    def test_calculate_semantic_memory(self):
        """Test calculating importance for semantic memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'semantic',
            'access_count': 15,
            'accessed_at': datetime.now() - timedelta(days=2),
            'content': 'User prefers Chinese'
        }

        importance = scorer.calculate(memory)

        assert importance.base_score == 1.0
        assert importance.type_weight == 0.5
        assert importance.frequency_weight == 0.3  # > 10 accesses
        assert importance.recency_weight == 0.2  # < 7 days
        assert importance.total_score == 2.0

    def test_calculate_procedural_memory(self):
        """Test calculating importance for procedural memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'procedural',
            'access_count': 6,
            'accessed_at': datetime.now() - timedelta(days=10),
            'content': 'How to deploy to production'
        }

        importance = scorer.calculate(memory)

        assert importance.type_weight == 0.3
        assert importance.frequency_weight == 0.2  # > 5 accesses
        assert importance.recency_weight == 0.1  # < 30 days
        assert importance.total_score == 1.6

    def test_calculate_episodic_memory(self):
        """Test calculating importance for episodic memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'episodic',
            'access_count': 1,
            'accessed_at': datetime.now() - timedelta(days=60),
            'content': 'User asked about weather today'
        }

        importance = scorer.calculate(memory)

        assert importance.type_weight == 0.0
        assert importance.frequency_weight == 0.0  # 1 access
        assert importance.recency_weight == 0.0  # > 30 days
        assert importance.total_score == 1.0

    def test_calculate_unknown_memory_type(self):
        """Test calculating importance for unknown memory type"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'unknown',
            'access_count': 0,
            'content': 'Test'
        }

        importance = scorer.calculate(memory)

        assert importance.type_weight == 0.0
        assert importance.total_score == 1.0

    def test_calculate_missing_fields(self):
        """Test calculating importance with missing fields"""
        scorer = ImportanceScorer()

        memory = {
            'content': 'Minimal memory'
        }

        importance = scorer.calculate(memory)

        assert importance.type_weight == 0.0  # defaults to episodic
        assert importance.frequency_weight == 0.0  # defaults to 0
        assert importance.recency_weight == 0.0  # no accessed_at
        assert importance.total_score == 1.0

    def test_calculate_frequency_weight_high(self):
        """Test frequency weight for high access count"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_frequency_weight(15)
        assert weight == 0.3

    def test_calculate_frequency_weight_medium(self):
        """Test frequency weight for medium access count"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_frequency_weight(6)
        assert weight == 0.2

    def test_calculate_frequency_weight_low(self):
        """Test frequency weight for low access count"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_frequency_weight(2)
        assert weight == 0.1

    def test_calculate_frequency_weight_zero(self):
        """Test frequency weight for zero access count"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_frequency_weight(0)
        assert weight == 0.0

    def test_calculate_recency_weight_recent(self):
        """Test recency weight for recent access"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_recency_weight(5)  # 5 days ago
        assert weight == 0.2

    def test_calculate_recency_weight_medium(self):
        """Test recency weight for medium recency"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_recency_weight(15)  # 15 days ago
        assert weight == 0.1

    def test_calculate_recency_weight_old(self):
        """Test recency weight for old access"""
        scorer = ImportanceScorer()

        weight = scorer._calculate_recency_weight(60)  # 60 days ago
        assert weight == 0.0

    def test_should_prioritize_high(self):
        """Test should_prioritize for high importance memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'semantic',
            'access_count': 15,
            'accessed_at': datetime.now() - timedelta(days=2)
        }

        assert scorer.should_prioritize(memory, threshold=1.5) is True

    def test_should_prioritize_low(self):
        """Test should_prioritize for low importance memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'episodic',
            'access_count': 1,
            'accessed_at': datetime.now() - timedelta(days=60)
        }

        assert scorer.should_prioritize(memory, threshold=1.5) is False

    def test_should_prioritize_custom_threshold(self):
        """Test should_prioritize with custom threshold"""
        scorer = ImportanceScorer()

        # Calculate actual score
        memory = {
            'memory_type': 'semantic',
            'access_count': 5,
            'accessed_at': datetime.now() - timedelta(days=10)
        }
        importance = scorer.calculate(memory)
        actual_score = importance.total_score

        # Test with thresholds around the actual score
        assert scorer.should_prioritize(memory, threshold=actual_score - 0.1) is True
        assert scorer.should_prioritize(memory, threshold=actual_score + 0.1) is False

    def test_should_archive_episodic(self):
        """Test should_archive for episodic memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'episodic',
            'access_count': 0,
            'accessed_at': datetime.now() - timedelta(days=365)
        }

        # Calculate actual score
        importance = scorer.calculate(memory)
        # Episodic memory with 0 access count and old access date
        # Score = 1.0 (base) + 0.0 (type) + 0.0 (frequency) + 0.0 (recency) = 1.0

        assert importance.total_score == 1.0

        # Score (1.0) < threshold (1.5) → should be archived
        assert scorer.should_archive(memory, threshold=1.5) is True

        # Score (1.0) >= threshold (0.5) → should NOT be archived
        assert scorer.should_archive(memory, threshold=0.5) is False

    def test_should_archive_very_low_priority(self):
        """Test should_archive for very low priority episodic memory"""
        scorer = ImportanceScorer()

        # Low priority episodic memory
        memory = {
            'memory_type': 'episodic',
            'access_count': 0,
            'accessed_at': datetime.now() - timedelta(days=365)
        }

        # With threshold > 1.0, it should be archived (score < threshold)
        assert scorer.should_archive(memory, threshold=1.5) is True

        # With threshold <= 1.0, it should NOT be archived (score >= threshold)
        assert scorer.should_archive(memory, threshold=1.0) is False
        assert scorer.should_archive(memory, threshold=0.5) is False

    def test_should_archive_semantic(self):
        """Test should_archive for semantic memory (should not archive)"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'semantic',
            'access_count': 0,
            'accessed_at': datetime.now() - timedelta(days=365)
        }

        # Semantic memories should not be archived
        assert scorer.should_archive(memory, threshold=0.3) is False

    def test_should_archive_high_importance(self):
        """Test should_archive for high importance memory"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'episodic',
            'access_count': 10,
            'accessed_at': datetime.now() - timedelta(days=2)
        }

        assert scorer.should_archive(memory, threshold=0.3) is False

    def test_rank_memories(self):
        """Test ranking memories by importance"""
        scorer = ImportanceScorer()

        memories = [
            {
                'memory_type': 'episodic',
                'access_count': 0,
                'accessed_at': datetime.now() - timedelta(days=60),
                'content': 'Low importance'
            },
            {
                'memory_type': 'semantic',
                'access_count': 15,
                'accessed_at': datetime.now() - timedelta(days=2),
                'content': 'High importance'
            },
            {
                'memory_type': 'procedural',
                'access_count': 5,
                'accessed_at': datetime.now() - timedelta(days=10),
                'content': 'Medium importance'
            }
        ]

        ranked = scorer.rank_memories(memories)

        assert len(ranked) == 3
        assert ranked[0]['content'] == 'High importance'
        assert ranked[1]['content'] == 'Medium importance'
        assert ranked[2]['content'] == 'Low importance'

    def test_rank_memories_empty(self):
        """Test ranking empty list"""
        scorer = ImportanceScorer()

        ranked = scorer.rank_memories([])

        assert ranked == []

    def test_get_importance_label_high(self):
        """Test getting importance label for high score"""
        scorer = ImportanceScorer()

        label = scorer.get_importance_label(1.8)
        assert label == "high"

    def test_get_importance_label_medium(self):
        """Test getting importance label for medium score"""
        scorer = ImportanceScorer()

        label = scorer.get_importance_label(1.5)
        assert label == "medium"

    def test_get_importance_label_low(self):
        """Test getting importance label for low score"""
        scorer = ImportanceScorer()

        label = scorer.get_importance_label(1.0)
        assert label == "low"

    def test_explain_score(self):
        """Test explaining score"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'semantic',
            'access_count': 15,
            'accessed_at': datetime.now() - timedelta(days=2),
            'content': 'Test memory'
        }

        explanation = scorer.explain_score(memory)

        assert "Importance score" in explanation
        assert "Base score" in explanation
        assert "Type weight" in explanation
        assert "Frequency weight" in explanation
        assert "Recency weight" in explanation
        assert "Priority" in explanation

    def test_explain_score_with_string_accessed_at(self):
        """Test explain_score with string accessed_at"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'semantic',
            'access_count': 10,
            'accessed_at': (datetime.now() - timedelta(days=5)).isoformat(),
            'content': 'Test memory'
        }

        explanation = scorer.explain_score(memory)

        assert "Importance score" in explanation
        assert "days ago" in explanation

    def test_explain_score_without_accessed_at(self):
        """Test explain_score without accessed_at"""
        scorer = ImportanceScorer()

        memory = {
            'memory_type': 'semantic',
            'access_count': 10,
            'content': 'Test memory'
        }

        explanation = scorer.explain_score(memory)

        assert "Importance score" in explanation
        # Should not show recency weight if no accessed_at
        assert "Recency weight" not in explanation

    def test_rank_memories_with_limit(self):
        """Test ranking memories and limiting results"""
        scorer = ImportanceScorer()

        memories = [
            {
                'memory_type': 'semantic',
                'access_count': 15,
                'accessed_at': datetime.now() - timedelta(days=2),
                'content': 'High 1'
            },
            {
                'memory_type': 'semantic',
                'access_count': 12,
                'accessed_at': datetime.now() - timedelta(days=3),
                'content': 'High 2'
            },
            {
                'memory_type': 'semantic',
                'access_count': 10,
                'accessed_at': datetime.now() - timedelta(days=5),
                'content': 'High 3'
            }
        ]

        ranked = scorer.rank_memories(memories)
        limited = ranked[:2]

        assert len(limited) == 2

    def test_type_weight_configuration(self):
        """Test type weight configuration"""
        scorer = ImportanceScorer()

        assert scorer.TYPE_WEIGHTS['semantic'] == 0.5
        assert scorer.TYPE_WEIGHTS['procedural'] == 0.3
        assert scorer.TYPE_WEIGHTS['episodic'] == 0.0

    def test_frequency_threshold_configuration(self):
        """Test frequency threshold configuration"""
        scorer = ImportanceScorer()

        thresholds = scorer.FREQUENCY_THRESHOLDS
        assert len(thresholds) == 3
        assert thresholds[0] == (10, 0.3)
        assert thresholds[1] == (5, 0.2)
        assert thresholds[2] == (1, 0.1)

    def test_recency_threshold_configuration(self):
        """Test recency threshold configuration"""
        scorer = ImportanceScorer()

        thresholds = scorer.RECENCY_THRESHOLDS
        assert len(thresholds) == 2
        assert thresholds[0] == (7, 0.2)
        assert thresholds[1] == (30, 0.1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
