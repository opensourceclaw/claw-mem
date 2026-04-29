"""
Memory Manager 集成测试
"""

import pytest
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from claw_mem import MemoryManager


class TestMemoryManagerIntegration:
    """Memory Manager 集成测试"""

    def test_gating_in_memory_manager(self):
        """测试 WriteTimeGating 集成到 MemoryManager"""
        # 创建 MemoryManager,启用 gating
        manager = MemoryManager(enable_gating=True, auto_detect=False)

        # 验证 gating 启用
        assert manager.enable_gating is True
        assert manager.gating is not None
        assert manager.gating_threshold == 0.6

    def test_gating_disabled_by_default(self):
        """测试默认禁用 gating"""
        manager = MemoryManager(auto_detect=False)

        assert manager.enable_gating is False
        assert manager.gating is None

    def test_custom_gating_threshold(self):
        """测试自定义阈值"""
        manager = MemoryManager(enable_gating=True, gating_threshold=0.8, auto_detect=False)

        assert manager.gating_threshold == 0.8
        assert manager.gating.threshold == 0.8

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 不启用 gating
        manager_old = MemoryManager(enable_gating=False, auto_detect=False)

        # 启用 gating
        manager_new = MemoryManager(enable_gating=True, auto_detect=False)

        # 两者都能正常工作
        assert manager_old.store("test content", memory_type="episodic") is True
        assert manager_new.store("test content", memory_type="episodic") is True

    def test_gating_statistics(self):
        """测试 gating 统计信息"""
        manager = MemoryManager(enable_gating=True, auto_detect=False)

        # 写入一些记忆(会触发 gating 评分)
        # 注意:gating 是在 gating.write 中生效,不是 store
        # 所以我们直接测试 gating
        manager.gating.write({
            'content': '重要决策',
            'source': 'user',
            'context': {}
        })

        # 获取统计
        stats = manager.get_gating_stats()

        assert stats is not None
        assert 'active_count' in stats
        assert 'cold_count' in stats
        assert 'threshold' in stats


class TestEndToEnd:
    """端到端测试"""

    def test_full_workflow_with_gating(self):
        """测试完整工作流(启用 gating)"""
        # 1. 创建 manager
        manager = MemoryManager(enable_gating=True, gating_threshold=0.6, auto_detect=False)

        # 2. 写入记忆(通过 gating)
        high_item = {
            'content': '重要决策:使用 Python 作为主要开发语言',
            'source': 'user',
            'context': {'topic': '技术选型'},
            'verified': True
        }
        result = manager.gating.write(high_item)
        assert result.stored is True

        # 3. 写入低显著性记忆
        low_item = {
            'content': '普通日志信息',
            'source': 'system',
            'context': {}
        }
        result = manager.gating.write(low_item)
        assert result.stored is True

        # 4. 获取统计
        stats = manager.get_gating_stats()
        assert stats is not None
        assert stats['active_count'] + stats['cold_count'] == 2

    def test_concurrent_access(self):
        """测试并发访问"""
        import threading

        manager = MemoryManager(enable_gating=True, auto_detect=False)
        results = []

        def write_items(thread_id):
            for i in range(10):
                result = manager.gating.write({
                    'content': f'线程{thread_id}_记忆{i}',
                    'source': 'user',
                    'context': {'thread': thread_id}
                })
                results.append(result)

        threads = [threading.Thread(target=write_items, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 50
        assert all(r.stored for r in results)

    def test_gating_stats_after_writes(self):
        """测试写入后的统计"""
        manager = MemoryManager(enable_gating=True, auto_detect=False)

        # 写入 20 条记忆
        for i in range(20):
            manager.gating.write({
                'content': f'记忆_{i}',
                'source': 'user' if i % 2 == 0 else 'external',
                'context': {}
            })

        stats = manager.get_gating_stats()
        assert stats['active_count'] + stats['cold_count'] == 20
