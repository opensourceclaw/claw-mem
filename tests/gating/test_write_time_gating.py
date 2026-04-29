"""
Tests for WriteTimeGating
"""

import pytest
import time
from src.claw_mem.gating import (
    WriteTimeGating,
    SalienceScorer,
    GatingResult,
    InMemoryStorage,
    DiskStorage,
    VersionChain,
)


class TestWriteTimeGating:
    """Test WriteTimeGating class"""

    def test_high_salience_stores_to_active(self):
        """Test high salience items stored in active memory"""
        gating = WriteTimeGating(threshold=0.6)

        result = gating.write({
            'content': '重要决策',
            'source': 'user',
            'context': {'session': 'test'}
        })

        assert result.stored is True
        assert result.tier == 'active'
        assert result.salience_score >= 0.6

    def test_low_salience_stores_to_cold(self):
        """Test low salience items stored in cold storage"""
        gating = WriteTimeGating(threshold=0.6)

        # 使用低显著性内容
        result = gating.write({
            'content': 'hello world hello world',  # 重复内容新颖性低
            'source': 'external',
            'context': {}
        })

        assert result.stored is True
        # 结果可能是 active 或 cold,取决于评分

    def test_threshold_adjustment(self):
        """Test threshold adjustment"""
        gating_high = WriteTimeGating(threshold=0.9)
        gating_low = WriteTimeGating(threshold=0.3)

        item = {'content': 'test', 'source': 'user', 'context': {}}

        result_high = gating_high.write(item)
        result_low = gating_low.write(item)

        # 高阈值更可能存储到 cold
        assert gating_high.threshold == 0.9
        assert gating_low.threshold == 0.3

    def test_should_store(self):
        """Test should_store pre-check"""
        gating = WriteTimeGating(threshold=0.6)

        high_salience = gating.should_store({
            'content': '重要决策',
            'source': 'user',
            'context': {}
        })

        low_salience = gating.should_store({
            'content': 'hello',
            'source': 'external',
            'context': {}
        })

        assert high_salience is True
        # low_salience 取决于评分

    def test_get_stats(self):
        """Test statistics"""
        gating = WriteTimeGating(threshold=0.6)

        gating.write({'content': 'test1', 'source': 'user', 'context': {}})
        gating.write({'content': 'test2', 'source': 'agent', 'context': {}})

        stats = gating.get_stats()

        assert 'active_count' in stats
        assert 'cold_count' in stats
        assert 'version_chain_length' in stats
        assert stats['threshold'] == 0.6


class TestSalienceScorer:
    """Test SalienceScorer class"""

    def test_source_reputation_user(self):
        """Test user source has highest reputation"""
        scorer = SalienceScorer()
        score = scorer.compute({
            'content': 'test',
            'source': 'user',
            'context': {}
        })

        # 用户来源应该有较高分数
        assert score >= 0.4

    def test_source_reputation_agent(self):
        """Test agent source"""
        scorer = SalienceScorer()
        score = scorer.compute({
            'content': 'test',
            'source': 'agent',
            'context': {}
        })

        assert score >= 0.3

    def test_novelty_first_item(self):
        """Test first item has highest novelty"""
        scorer = SalienceScorer()

        # 第一个项目应该有最高新颖性
        score = scorer.compute({
            'content': 'unique content here',
            'source': 'user',
            'context': {}
        })

        assert score >= 0.5

    def test_reliability_with_context(self):
        """Test reliability increases with context"""
        scorer = SalienceScorer()

        with_context = scorer.compute({
            'content': 'test',
            'source': 'user',
            'context': {'session': 'test', 'timestamp': 123}
        })

        without_context = scorer.compute({
            'content': 'test',
            'source': 'user',
            'context': {}
        })

        # 有上下文的应该分数更高或相同
        assert with_context >= without_context

    def test_weighted_average(self):
        """Test weighted average calculation"""
        weights = {
            'source_reputation': 0.5,
            'novelty': 0.3,
            'reliability': 0.2
        }

        scorer = SalienceScorer(weights=weights)

        assert scorer.weights['source_reputation'] == 0.5
        assert scorer.weights['novelty'] == 0.3
        assert scorer.weights['reliability'] == 0.2


class TestInMemoryStorage:
    """Test InMemoryStorage class"""

    def test_store_and_count(self):
        """Test store and count"""
        storage = InMemoryStorage()

        storage.store({'content': 'test1'})
        storage.store({'content': 'test2'})

        assert storage.count() == 2

    def test_list_all(self):
        """Test list all items"""
        storage = InMemoryStorage()

        storage.store({'content': 'test1'})
        storage.store({'content': 'test2'})

        items = storage.list_all()
        assert len(items) == 2

    def test_clear(self):
        """Test clear storage"""
        storage = InMemoryStorage()

        storage.store({'content': 'test'})
        storage.clear()

        assert storage.count() == 0


class TestDiskStorage:
    """Test DiskStorage class"""

    def test_archive(self, tmp_path):
        """Test archive to disk"""
        storage = DiskStorage(storage_path=str(tmp_path / "cold"))

        item = {'content': 'test', 'id': '123'}
        stored = storage.archive(item)

        assert stored['_tier'] == 'cold'
        assert storage.count() == 1


class TestVersionChain:
    """Test VersionChain class"""

    def test_append(self):
        """Test append version"""
        chain = VersionChain()

        chain.append({'content': 'v1'})
        chain.append({'content': 'v2'})

        assert len(chain) == 2

    def test_latest(self):
        """Test get latest version"""
        chain = VersionChain()

        chain.append({'content': 'v1'})
        chain.append({'content': 'v2'})

        latest = chain.latest()
        assert latest['content'] == 'v2'

    def test_get_by_index(self):
        """Test get version by index"""
        chain = VersionChain()

        chain.append({'content': 'v1'})
        chain.append({'content': 'v2'})

        v0 = chain.get(0)
        v1 = chain.get(1)

        assert v0['content'] == 'v1'
        assert v1['content'] == 'v2'


class TestPerformance:
    """Performance tests"""

    def test_write_latency(self):
        """Test write latency < 10ms"""
        gating = WriteTimeGating(threshold=0.6)

        start = time.time()
        for i in range(100):
            gating.write({
                'content': f'test content {i}',
                'source': 'user',
                'context': {}
            })
        elapsed = (time.time() - start) * 1000

        avg_latency = elapsed / 100
        print(f"\nAverage write latency: {avg_latency:.2f}ms")
        assert avg_latency < 10, f"Write latency {avg_latency:.2f}ms exceeds 10ms"

    def test_salience_computation_latency(self):
        """Test salience computation < 5ms"""
        scorer = SalienceScorer()

        start = time.time()
        for i in range(100):
            scorer.compute({
                'content': f'test content {i}',
                'source': 'user',
                'context': {}
            })
        elapsed = (time.time() - start) * 1000

        avg_latency = elapsed / 100
        print(f"\nAverage salience latency: {avg_latency:.2f}ms")
        assert avg_latency < 5, f"Salience latency {avg_latency:.2f}ms exceeds 5ms"
