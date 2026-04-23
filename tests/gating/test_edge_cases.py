"""
边界情况测试 - WriteTimeGating
"""

import pytest
import threading
from src.claw_mem.gating import WriteTimeGating, SalienceScorer


class TestWriteTimeGatingEdgeCases:
    """WriteTimeGating 边界情况测试"""

    def test_empty_item(self):
        """测试空输入"""
        gating = WriteTimeGating()
        result = gating.write({})
        # 应该能处理空输入，不崩溃
        assert result.stored is True

    def test_none_content(self):
        """测试 None 内容"""
        gating = WriteTimeGating()
        result = gating.write({'content': None})
        assert result.stored is True

    def test_very_long_content(self):
        """测试超长内容"""
        gating = WriteTimeGating()
        long_content = "测试" * 10000  # 约 20 万字
        result = gating.write({'content': long_content})
        assert result.stored is True

    def test_special_characters(self):
        """测试特殊字符"""
        gating = WriteTimeGating()
        special = "\n\t\r\0\x00\\\"'"
        result = gating.write({'content': special})
        assert result.stored is True

    def test_unicode_content(self):
        """测试 Unicode 内容"""
        gating = WriteTimeGating()
        unicode_content = "中文🎉🚀💎\u0000\uFFFF"
        result = gating.write({'content': unicode_content})
        assert result.stored is True

    def test_extreme_salience_scores(self):
        """测试极端显著性分数"""
        gating = WriteTimeGating(threshold=0.5)

        # 极高显著性
        high_item = {
            'content': '非常重要',
            'source': 'user',
            'verified': True,
            'context': {'key': 'value'}
        }
        result = gating.write(high_item)
        assert result.tier == 'active'

        # 极低显著性
        low_item = {
            'content': '普通信息',
            'source': 'external',
            'verified': False
        }
        result = gating.write(low_item)
        assert result.stored is True

    def test_threshold_boundary(self):
        """测试阈值边界"""
        gating = WriteTimeGating(threshold=0.6)

        boundary_item = {
            'content': '边界测试',
            'source': 'agent'
        }
        result = gating.write(boundary_item)
        assert result.stored is True

    def test_concurrent_writes(self):
        """测试并发写入"""
        gating = WriteTimeGating()
        results = []

        def write_item(i):
            result = gating.write({'content': f'item_{i}', 'source': 'user'})
            results.append(result)

        threads = [threading.Thread(target=write_item, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r.stored for r in results)

    def test_all_source_types(self):
        """测试所有来源类型"""
        gating = WriteTimeGating()
        sources = ['user', 'agent', 'system', 'external']

        for source in sources:
            result = gating.write({'content': 'test', 'source': source})
            assert result.stored is True
            assert result.tier in ['active', 'cold']


class TestSalienceScorerEdgeCases:
    """SalienceScorer 边界情况测试"""

    def test_empty_content(self):
        """测试空内容"""
        scorer = SalienceScorer()
        score = scorer.compute({'content': '', 'source': 'user'})
        assert 0.0 <= score <= 1.0

    def test_unknown_source(self):
        """测试未知来源"""
        scorer = SalienceScorer()
        score = scorer.compute({'content': 'test', 'source': 'unknown'})
        assert 0.0 <= score <= 1.0

    def test_missing_fields(self):
        """测试缺失字段"""
        scorer = SalienceScorer()
        score = scorer.compute({})
        assert 0.0 <= score <= 1.0

    def test_repeated_content(self):
        """测试重复内容"""
        scorer = SalienceScorer()

        score1 = scorer.compute({'content': '重复内容', 'source': 'user'})
        score2 = scorer.compute({'content': '重复内容', 'source': 'user'})

        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0

    def test_very_long_content(self):
        """测试超长内容"""
        scorer = SalienceScorer()
        long_content = "测试" * 10000
        score = scorer.compute({'content': long_content, 'source': 'user'})
        assert 0.0 <= score <= 1.0

    def test_all_source_types(self):
        """测试所有来源类型"""
        scorer = SalienceScorer()
        sources = ['user', 'agent', 'system', 'external', 'unknown']

        for source in sources:
            score = scorer.compute({'content': 'test', 'source': source})
            assert 0.0 <= score <= 1.0, f"Source {source} failed"


class TestErrorHandling:
    """异常处理测试"""

    def test_custom_weights(self):
        """测试自定义权重"""
        weights = {
            'source_reputation': 0.5,
            'novelty': 0.3,
            'reliability': 0.2
        }
        scorer = SalienceScorer(weights=weights)
        assert scorer.weights == weights

    def test_zero_threshold(self):
        """测试零阈值"""
        gating = WriteTimeGating(threshold=0.0)
        result = gating.write({'content': 'test', 'source': 'external'})
        assert result.stored is True

    def test_full_threshold(self):
        """测试满分阈值"""
        gating = WriteTimeGating(threshold=1.0)
        result = gating.write({'content': 'test', 'source': 'user'})
        assert result.stored is True


class TestPerformance:
    """性能测试"""

    def test_write_latency(self):
        """测试写入延迟 < 10ms"""
        import time
        gating = WriteTimeGating()

        start = time.time()
        for i in range(100):
            gating.write({'content': f'test_{i}', 'source': 'user'})
        elapsed = time.time() - start

        avg_latency = elapsed / 100 * 1000
        print(f"\nAverage write latency: {avg_latency:.2f}ms")
        assert avg_latency < 10

    def test_scoring_latency(self):
        """测试评分延迟 < 5ms"""
        import time
        scorer = SalienceScorer()

        start = time.time()
        for i in range(100):
            scorer.compute({'content': f'test_{i}', 'source': 'user'})
        elapsed = time.time() - start

        avg_latency = elapsed / 100 * 1000
        print(f"\nAverage scoring latency: {avg_latency:.2f}ms")
        assert avg_latency < 5

    def test_memory_usage(self):
        """测试内存使用 < 10MB"""
        import tracemalloc
        import sys

        tracemalloc.start()

        gating = WriteTimeGating()
        for i in range(1000):
            gating.write({'content': f'test_{i}', 'source': 'user'})

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024
        print(f"\nPeak memory: {peak_mb:.2f}MB")
        assert peak_mb < 10

    def test_high_volume_writes(self):
        """测试大批量写入"""
        import time
        gating = WriteTimeGating()

        start = time.time()
        for i in range(1000):
            gating.write({'content': f'test_{i}', 'source': 'user'})
        elapsed = time.time() - start

        print(f"\n1000 writes: {elapsed*1000:.2f}ms")
        assert elapsed < 1.0  # 1000 次写入应在 1 秒内
