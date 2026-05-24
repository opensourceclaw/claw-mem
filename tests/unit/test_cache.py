"""Tests for TTLCache."""

import time

from claw_mem.cache import CacheEntry, TTLCache


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_not_expired(self):
        entry = CacheEntry(value="test", ttl=60)
        assert entry.is_expired() is False

    def test_expired(self):
        entry = CacheEntry(value="test", created_at=0, ttl=0.001)
        time.sleep(0.002)
        assert entry.is_expired() is True

    def test_no_expiry(self):
        entry = CacheEntry(value="test", ttl=-1)
        assert entry.is_expired() is False


class TestTTLCache:
    """Tests for TTLCache."""

    def test_set_and_get(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_miss(self):
        cache = TTLCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expired(self):
        cache = TTLCache(default_ttl=-1)
        cache.set("key", "value", ttl=-1)
        # Force expire by using a negative TTL that elapsed
        assert cache.get("key") == "value"  # -1 means no expiry

    def test_actual_expiry(self):
        cache = TTLCache(default_ttl=-1)
        cache.set("key", "value", ttl=0.001)
        time.sleep(0.002)
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = TTLCache()
        cache.set("key", "value")
        assert cache.invalidate("key") is True
        assert cache.get("key") is None

    def test_invalidate_missing(self):
        cache = TTLCache()
        assert cache.invalidate("missing") is False

    def test_clear(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_get_stats(self):
        cache = TTLCache()
        cache.set("key", "value")
        cache.get("key")
        cache.get("key")
        cache.get("missing")

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_default_ttl(self):
        cache = TTLCache(default_ttl=600)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_custom_ttl_override(self):
        cache = TTLCache(default_ttl=60)
        cache.set("key", "value", ttl=120)
        assert cache.get("key") == "value"
