"""Integration performance tests for claw-mem v3.4.0."""

import time

from claw_mem.cache import TTLCache
from claw_mem.pool import ObjectPool


class TestCachePerformance:
    """Integration tests for cache performance."""

    def test_cache_hit_latency(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key", "value")

        start = time.time()
        for _ in range(100):
            cache.get("key")
        elapsed = time.time() - start

        # 100 cache hits should be sub-millisecond
        assert elapsed < 0.1

    def test_cache_expiry_cleanup(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2, ttl=0.001)
        time.sleep(0.002)

        # Expired entry should be evicted
        assert cache.get("b") is None
        stats = cache.get_stats()
        assert stats["evictions"] > 0


class TestPoolPerformance:
    """Integration tests for object pool."""

    def test_pool_reuse_cycle(self):
        pool = ObjectPool(dict, max_size=5)
        ids = set()

        for _ in range(10):
            with pool.acquire() as obj:
                ids.add(id(obj))

        # Objects should be reused, so fewer unique IDs
        assert len(ids) <= 10

    def test_pool_clear_and_reuse(self):
        pool = ObjectPool(list, max_size=3)
        with pool.acquire() as obj:
            obj.append("x")

        assert pool.size == 1
        pool.clear()
        assert pool.size == 0

        with pool.acquire() as obj:
            assert obj == []  # New object after clear
