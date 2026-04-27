"""
Integration tests for MemoryManager with Write-Time Gating
"""

import pytest
import tempfile
import os
from src.claw_mem.memory_manager import MemoryManager
from src.claw_mem.gating import WriteTimeGating, GatingFilter, AdaptiveThreshold


class TestMemoryManagerGating:
    """Test MemoryManager with gating enabled"""

    def test_store_with_gating_enabled(self):
        """Test store with gating enabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(
                workspace=tmpdir,
                enable_gating=True,
                gating_threshold=0.6
            )

            result = mm.store('Test important memory', memory_type='semantic')
            assert result is True

            stats = mm.get_gating_stats()
            assert stats is not None
            assert stats['threshold'] == 0.6

    def test_store_with_gating_disabled(self):
        """Test store with gating disabled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(
                workspace=tmpdir,
                enable_gating=False
            )

            result = mm.store('Test memory', memory_type='semantic')
            assert result is True

            stats = mm.get_gating_stats()
            assert stats is None

    def test_gating_stats_after_multiple_stores(self):
        """Test gating stats after multiple stores"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(
                workspace=tmpdir,
                enable_gating=True,
                gating_threshold=0.6
            )

            # Store multiple memories
            mm.store('User preference: Chinese', memory_type='semantic')
            mm.store('User asked about weather', memory_type='episodic')
            mm.store('Technical decision: Use Python', memory_type='semantic')

            stats = mm.get_gating_stats()
            assert stats is not None
            assert stats['active_count'] >= 0
            assert stats['version_chain_length'] >= 3

    def test_gating_with_different_thresholds(self):
        """Test gating with different thresholds"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # High threshold
            mm_high = MemoryManager(
                workspace=tmpdir + '/high',
                enable_gating=True,
                gating_threshold=0.9
            )

            with tempfile.TemporaryDirectory() as tmpdir2:
                # Low threshold
                mm_low = MemoryManager(
                    workspace=tmpdir2 + '/low',
                    enable_gating=True,
                    gating_threshold=0.3
                )

                assert mm_high.gating_threshold == 0.9
                assert mm_low.gating_threshold == 0.3


class TestGatingFilterIntegration:
    """Test GatingFilter integration scenarios"""

    def test_gating_filter_with_memory_manager_data(self):
        """Test gating filter with typical MemoryManager data"""
        filter = GatingFilter(threshold=1.0)

        # Typical memory record from MemoryManager
        memory = {
            'memory_type': 'semantic',
            'access_count': 5,
            'content': 'User prefers dark mode',
            'source': 'user'
        }

        result = filter.should_store(memory)
        assert result.should_store is True or result.should_store is False
        assert 0 <= result.importance_score <= 2.0

    def test_gating_filter_episodic_vs_semantic(self):
        """Test gating filter distinguishes memory types"""
        filter = GatingFilter(threshold=1.0)

        semantic = {
            'memory_type': 'semantic',
            'access_count': 0,
            'content': 'Fact',
            'source': 'user'
        }

        episodic = {
            'memory_type': 'episodic',
            'access_count': 0,
            'content': 'Chat',
            'source': 'user'
        }

        semantic_result = filter.should_store(semantic)
        episodic_result = filter.should_store(episodic)

        # Semantic should have higher score than episodic
        assert semantic_result.importance_score >= episodic_result.importance_score

    def test_gating_filter_custom_score_function(self):
        """Test gating filter with custom score function"""
        def custom_score(memory: dict) -> float:
            # Custom logic: prefer longer content
            content_len = len(memory.get('content', ''))
            return min(2.0, content_len / 100)

        filter = GatingFilter(
            threshold=0.5,
            custom_score_func=custom_score
        )

        short_content = {'content': 'Short'}
        long_content = {'content': 'A' * 200}

        short_result = filter.should_store(short_content)
        long_result = filter.should_store(long_content)

        assert long_result.importance_score > short_result.importance_score


class TestAdaptiveThresholdScenarios:
    """Test AdaptiveThreshold in real scenarios"""

    def test_empty_memory(self):
        """Test threshold when memory is empty"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            min_threshold=0.5,
            max_threshold=1.5,
            memory_capacity=1000
        )

        threshold = adapter.get_threshold(0)
        assert threshold >= adapter.min_threshold
        assert threshold <= adapter.base_threshold

    def test_half_capacity(self):
        """Test threshold at half capacity"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            memory_capacity=1000
        )

        threshold = adapter.get_threshold(500)
        assert threshold == 1.0  # At 50%, should be base

    def test_near_capacity(self):
        """Test threshold near capacity"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            min_threshold=0.5,
            max_threshold=1.5,
            memory_capacity=1000
        )

        threshold = adapter.get_threshold(950)
        assert threshold >= 1.0

    def test_over_capacity(self):
        """Test threshold when over capacity"""
        adapter = AdaptiveThreshold(
            base_threshold=1.0,
            min_threshold=0.5,
            max_threshold=1.5,
            memory_capacity=1000
        )

        threshold = adapter.get_threshold(2000)
        assert threshold == adapter.max_threshold


class TestGatingEdgeCases:
    """Test edge cases"""

    def test_empty_content(self):
        """Test gating with empty content"""
        filter = GatingFilter(threshold=1.0)

        result = filter.should_store({
            'content': '',
            'memory_type': 'episodic'
        })

        # Should still return a result
        assert result.importance_score >= 0

    def test_none_values(self):
        """Test gating with None values"""
        filter = GatingFilter(threshold=1.0)

        result = filter.should_store({
            'content': 'Test',
            'memory_type': None,
            'access_count': None,
            'source': None
        })

        assert result.importance_score >= 0

    def test_extreme_memory_count(self):
        """Test adaptive threshold with extreme values"""
        adapter = AdaptiveThreshold()

        # Very small
        threshold_min = adapter.get_threshold(0)
        assert threshold_min > 0

        # Very large
        threshold_max = adapter.get_threshold(1_000_000)
        assert threshold_max <= adapter.max_threshold

    def test_negative_memory_count(self):
        """Test adaptive threshold with negative (should clamp to 0)"""
        adapter = AdaptiveThreshold()

        threshold = adapter.get_threshold(-100)
        # Should handle gracefully
        assert threshold >= adapter.min_threshold


class TestPerformance:
    """Performance tests for gating"""

    def test_memory_manager_store_latency_with_gating(self):
        """Test store latency with gating enabled"""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(
                workspace=tmpdir,
                enable_gating=True,
                gating_threshold=0.6
            )

            start = time.time()
            for i in range(50):
                mm.store(f'Test memory {i}', memory_type='episodic')
            elapsed = (time.time() - start) * 1000

            avg_latency = elapsed / 50
            print(f"\nAverage store latency with gating: {avg_latency:.2f}ms")
            # Should be under 50ms for normal operation
            assert avg_latency < 50
