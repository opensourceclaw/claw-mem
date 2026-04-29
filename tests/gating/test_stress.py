"""压力测试"""

import pytest
import time
import threading
import gc
import tracemalloc
from claw_mem import MemoryManager


class TestStress:
    """压力测试"""

    def test_large_scale_writes(self):
        """测试大规模写入 (10,000 次)"""
        manager = MemoryManager(enable_gating=True)

        start = time.time()

        for i in range(10000):
            manager.gating.write({
                'content': f'记忆内容_{i}' * 10,
                'source': 'user' if i % 3 == 0 else 'agent',
                'context': {'index': i, 'batch': 'stress_test'}
            })

        elapsed = time.time() - start

        # 10,000 次写入应该在 10 秒内完成
        assert elapsed < 10, f"10,000 writes took {elapsed:.2f}s (> 10s)"

        # 平均延迟应该 < 1ms
        avg_latency = elapsed / 10000 * 1000
        assert avg_latency < 1, f"Average latency {avg_latency:.2f}ms (> 1ms)"

        print(f"\n✅ 10,000 writes in {elapsed:.2f}s")
        print(f"✅ Average latency: {avg_latency:.3f}ms")

    def test_memory_leak(self):
        """测试内存泄漏"""
        tracemalloc.start()

        manager = MemoryManager(enable_gating=True)

        # 第一次写入
        for i in range(1000):
            manager.gating.write({
                'content': f'test_{i}',
                'source': 'user',
                'context': {}
            })

        gc.collect()
        snapshot1 = tracemalloc.take_snapshot()

        # 第二次写入
        for i in range(1000):
            manager.gating.write({
                'content': f'test_{i}',
                'source': 'user',
                'context': {}
            })

        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()

        # 检查内存增长
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        # 内存增长应该 < 5MB
        total_growth = sum(stat.size_diff for stat in top_stats)
        assert total_growth < 5 * 1024 * 1024, f"Memory growth {total_growth / 1024 / 1024:.2f}MB (> 5MB)"

        tracemalloc.stop()
        print(f"\n✅ No significant memory leak detected")

    def test_concurrent_stress(self):
        """测试并发压力"""
        manager = MemoryManager(enable_gating=True)
        results = []
        errors = []

        def write_batch(thread_id):
            try:
                for i in range(100):
                    result = manager.gating.write({
                        'content': f'线程{thread_id}_记忆{i}',
                        'source': 'user',
                        'context': {'thread': thread_id}
                    })
                    results.append(result)
            except Exception as e:
                errors.append(e)

        start = time.time()

        threads = [threading.Thread(target=write_batch, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        elapsed = time.time() - start

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 2000, f"Expected 2000 results, got {len(results)}"

        # 20 线程 × 100 写入应该在 5 秒内完成
        assert elapsed < 5, f"Concurrent writes took {elapsed:.2f}s (> 5s)"

        print(f"\n✅ 20 threads × 100 writes in {elapsed:.2f}s")
        print(f"✅ No errors, all 2000 writes succeeded")

    def test_mixed_operations(self):
        """测试混合操作(写入 + 检索)"""
        manager = MemoryManager(enable_gating=True)

        # 写入
        for i in range(1000):
            manager.gating.write({
                'content': f'Python技术_{i}',
                'source': 'user',
                'context': {'topic': '技术'}
            })

        # 统计
        stats = manager.get_gating_stats()
        print(f"\nStats: {stats}")
        total = stats['active_count'] + stats['cold_count']
        print(f"Total: {total}")
        assert total == 1000, f"Expected 1000, got {total}"

        print(f"✅ Mixed operations: 1000 writes + stats")
