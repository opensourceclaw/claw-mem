"""Tests for QueryCache (v2.19.0) — v3.2.0: cache module removed, API differs from retrieval."""

import time
import pytest

pytestmark = pytest.mark.skip(reason="v3.2.0: cache/query_cache module deleted (replaced by retrieval/query_cache with different API)")


class TestQueryCache:
    """Tests for QueryCache LRU + TTL."""

    def setup_method(self):
        self.cache = QueryCache(max_size=10, ttl_seconds=60)

    def test_set_and_get(self):
        self.cache.set("q1", ["id1", "id2"])
        results = self.cache.get("q1")
        assert results == ["id1", "id2"]

    def test_get_miss(self):
        assert self.cache.get("nonexistent") is None

    def test_get_ttl_expired(self):
        ttl_cache = QueryCache(max_size=10, ttl_seconds=0)
        ttl_cache.set("q", ["a"])
        assert ttl_cache.get("q") is None

    def test_hit_rate_initial(self):
        assert self.cache.hit_rate == 0.0

    def test_hit_rate_after_hits(self):
        self.cache.set("q", ["x"])
        self.cache.get("q")
        self.cache.get("q")
        assert self.cache.hit_rate == 1.0

    def test_hit_rate_after_miss(self):
        self.cache.set("q", ["x"])
        self.cache.get("q")
        self.cache.get("missing")
        assert 0.4 < self.cache.hit_rate < 0.6  # 1 hit, 1 miss = 0.5

    def test_lru_eviction(self):
        small = QueryCache(max_size=2)
        small.set("a", ["1"])
        small.set("b", ["2"])
        small.set("c", ["3"])  # evicts "a"
        assert small.get("a") is None
        assert small.get("b") == ["2"]
        assert small.get("c") == ["3"]

    def test_clear(self):
        self.cache.set("q", ["x"])
        self.cache.clear()
        assert self.cache.get("q") is None
        assert self.cache.hit_rate == 0.0

    def test_size(self):
        assert self.cache.size == 0
        self.cache.set("a", ["1"])
        self.cache.set("b", ["2"])
        assert self.cache.size == 2

    def test_stats(self):
        self.cache.set("q", ["id"])
        s = self.cache.stats()
        assert "size" in s
        assert "hits" in s
        assert "misses" in s
        assert "hit_rate" in s
        assert s["size"] == 1
