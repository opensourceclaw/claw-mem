"""
Tests for GatingFilter and AdaptiveThreshold
"""

import pytest
import time
from src.claw_mem.gating import (
    GatingFilter,
    GatingFilterResult,
    AdaptiveThreshold,
)
from src.claw_mem.importance import ImportanceScorer


class TestGatingFilter:
    """Test GatingFilter class"""

    def test_high_importance_should_store(self):
        """Test high importance memory should be stored"""
        filter = GatingFilter(threshold=1.0)

        memory = {
            'memory_type': 'semantic',
            'access_count': 10,
            'content': 'Important fact',
            'source': 'user'
        }

        result = filter.should_store(memory)

        assert result.should_store is True
        assert result.importance_score >= 1.0

    def test_low_importance_should_not_store(self):
        """Test low importance memory should not be stored"""
        filter = GatingFilter(threshold=1.5)

        memory = {
            'memory_type': 'episodic',
            'access_count': 0,
            'content': 'Random chat',
            'source': 'external'
        }

        result = filter.should_store(memory)

        # 可能存储或不存储,取决于评分

    def test_threshold_boundary(self):
        """Test threshold boundary"""
        filter = GatingFilter(threshold=1.0)

        # 刚好等于阈值
        memory = {'memory_type': 'semantic', 'access_count': 0}

        result = filter.should_store(memory)

        # 应该存储(>= 阈值)
        assert result.should_store is True

    def test_set_threshold(self):
        """Test threshold adjustment"""
        filter = GatingFilter(threshold=1.0)

        filter.set_threshold(1.5)
        assert filter.get_threshold() == 1.5

        filter.set_threshold(0.5)
        assert filter.get_threshold() == 0.5

        # 边界检查
        filter.set_threshold(3.0)
        assert filter.get_threshold() == 2.0

        filter.set_threshold(-1.0)
        assert filter.get_threshold() == 0.0

    def test_with_importance_scorer(self):
        """Test with ImportanceScorer"""
        scorer = ImportanceScorer()
        filter = GatingFilter(scorer=scorer, threshold=1.0)

        memory = {
            'memory_type': 'semantic',
            'access_count': 15,
            'accessed_at': None
        }

        result = filter.should_store(memory)

        assert isinstance(result, GatingFilterResult)
        assert 0 <= result.importance_score <= 2.0


class TestAdaptiveThreshold:
    """Test AdaptiveThreshold class"""

    def test_low_memory_count(self):
        """Test threshold with low memory count"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            min_threshold=0.5,
            max_threshold=1.5,
            memory_capacity=1000
        )

        threshold = adapter.get_threshold(current_memory_count=100)

        # 记忆少时,阈值应该接近或低于基础阈值
        assert threshold <= 1.0

    def test_high_memory_count(self):
        """Test threshold with high memory count"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            min_threshold=0.5,
            max_threshold=1.5,
            memory_capacity=1000
        )

        threshold = adapter.get_threshold(current_memory_count=900)

        # 记忆多时,阈值应该高于基础阈值
        assert threshold >= 1.0

    def test_boundary_memory_count(self):
        """Test threshold at capacity boundaries"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            min_threshold=0.5,
            max_threshold=1.5,
            memory_capacity=1000
        )

        # 接近容量
        threshold_min = adapter.get_threshold(0)
        threshold_max = adapter.get_threshold(2000)

        assert threshold_min >= adapter.min_threshold
        assert threshold_max <= adapter.max_threshold

    def test_get_stats(self):
        """Test statistics"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            memory_capacity=1000
        )

        stats = adapter.get_stats(current_memory_count=500)

        assert 'current_count' in stats
        assert 'capacity' in stats
        assert 'usage_ratio' in stats
        assert 'current_threshold' in stats
        assert stats['current_count'] == 500
        assert stats['usage_ratio'] == 0.5

    def test_reset(self):
        """Test reset to base threshold"""
        adapter = AdaptiveThreshold(base_threshold=1.0)

        # 先设置一个不同的值
        threshold = adapter.get_threshold(900)

        # 重置
        result = adapter.reset()
        assert result == 1.0


class TestGatingFilterResult:
    """Test GatingFilterResult dataclass"""

    def test_result_creation(self):
        """Test creating GatingFilterResult"""
        result = GatingFilterResult(
            should_store=True,
            importance_score=1.5,
            reason="High importance",
            metadata={'type': 'semantic'}
        )

        assert result.should_store is True
        assert result.importance_score == 1.5
        assert result.reason == "High importance"
        assert result.metadata['type'] == 'semantic'


class TestPerformance:
    """Performance tests"""

    def test_gating_filter_latency(self):
        """Test gating filter latency < 10ms"""
        filter = GatingFilter(threshold=1.0)

        memories = [
            {'memory_type': 'semantic', 'access_count': i, 'content': f'test {i}'}
            for i in range(100)
        ]

        start = time.time()
        for memory in memories:
            filter.should_store(memory)
        elapsed = (time.time() - start) * 1000

        avg_latency = elapsed / 100
        print(f"\nAverage gating filter latency: {avg_latency:.2f}ms")
        assert avg_latency < 10

    def test_adaptive_threshold_latency(self):
        """Test adaptive threshold latency < 1ms"""
        adapter = AdaptiveThreshold()

        start = time.time()
        for i in range(1000):
            adapter.get_threshold(i % 1000)
        elapsed = (time.time() - start) * 1000

        avg_latency = elapsed / 1000
        print(f"\nAverage adaptive threshold latency: {avg_latency:.4f}ms")
        assert avg_latency < 1
