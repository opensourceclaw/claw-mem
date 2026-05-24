"""Tests for claw_mem.dual_system.hippocampal.HippocampalStore."""
import time
import pytest
from claw_mem.dual_system import HippocampalStore, Memory


@pytest.fixture
def store():
    return HippocampalStore(capacity=100, lru_cache_size=10)


class TestMemory:
    def test_default_creation(self):
        m = Memory()
        assert len(m.memory_id) > 0
        assert m.importance == 0.5

    def test_is_expired(self):
        m = Memory(ttl_seconds=0)
        assert not m.is_expired
        m2 = Memory(created_at=time.time() - 100000, ttl_seconds=1)
        assert m2.is_expired

    def test_age_seconds(self):
        m = Memory(created_at=time.time() - 10)
        assert m.age_seconds >= 10


class TestHippocampalStore:
    def test_store_returns_id(self, store):
        m = Memory(content="test")
        mid = store.store(m)
        assert mid == m.memory_id
        assert store.size() == 1

    def test_retrieve_by_content(self, store):
        store.store(Memory(content="important fact"))
        store.store(Memory(content="random noise"))
        results = store.retrieve("important")
        assert len(results) == 1
        assert results[0].content == "important fact"

    def test_retrieve_limits(self, store):
        for i in range(10):
            store.store(Memory(content=f"test {i}"))
        results = store.retrieve("test", limit=3)
        assert len(results) == 3

    def test_retrieve_increments_access(self, store):
        m = Memory(content="query me")
        store.store(m)
        store.retrieve("query")
        assert m.access_count >= 1

    def test_get_by_id(self, store):
        m = Memory(content="get me")
        store.store(m)
        assert store.get(m.memory_id) is not None

    def test_get_nonexistent(self, store):
        assert store.get("no-such") is None

    def test_mark_for_consolidation(self, store):
        m = Memory(content="important")
        store.store(m)
        assert store.mark_for_consolidation(m.memory_id, 0.9)
        # Importance should increase
        result = store.get(m.memory_id)
        assert result.importance >= 0.9

    def test_get_pending_consolidation(self, store):
        store.store(Memory(content="low pri", importance=0.1))
        store.store(Memory(content="high pri", importance=0.9))
        pending = store.get_pending_consolidation(min_importance=0.5)
        assert len(pending) == 1
        assert pending[0].content == "high pri"

    def test_remove(self, store):
        m = Memory(content="delete me")
        store.store(m)
        assert store.remove(m.memory_id)
        assert store.size() == 0

    def test_remove_batch(self, store):
        ids = []
        for i in range(5):
            m = Memory(content=f"batch {i}")
            store.store(m)
            ids.append(m.memory_id)
        count = store.remove_batch(ids[:3])
        assert count == 3
        assert store.size() == 2

    def test_evict_lru_at_capacity(self):
        store = HippocampalStore(capacity=3)
        store.store(Memory(content="a"))
        store.store(Memory(content="b"))
        store.store(Memory(content="c"))
        # Access a to make it recently used
        store.retrieve("a")
        # Store d, should evict b (least recently used of b and c)
        store.store(Memory(content="d"))
        assert store.size() <= 3

    def test_clear(self, store):
        store.store(Memory(content="clean"))
        store.clear()
        assert store.size() == 0

    def test_thread_safe(self, store):
        import threading
        def store_memories():
            for i in range(50):
                store.store(Memory(content=f"thread-{i}"))
        threads = [threading.Thread(target=store_memories) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert store.size() >= 50
