"""Tests for claw_mem.memory.pool (MemoryPool)."""

import pytest
import tempfile
import os
from claw_mem.memory.pool import MemoryPool
from claw_mem.memory.agnostic import MemoryRecord


@pytest.fixture
def pool():
    return MemoryPool()


@pytest.fixture
def sample_record():
    return MemoryRecord(
        id="r1", agent_id="agent1", memory_type="episodic",
        content="test content", tags=["test"], timestamp=1000.0,
    )


class TestMemoryPool:
    def test_store_and_query(self, pool, sample_record):
        pool.store(sample_record)
        results = pool.query({})
        assert len(results) == 1
        assert results[0].id == "r1"

    def test_query_by_agent(self, pool):
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="c1", tags=[], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a2", memory_type="episodic",
                          content="c2", tags=[], timestamp=200.0)
        pool.store(r1)
        pool.store(r2)
        results = pool.query({"agent_id": "a1"})
        assert len(results) == 1
        assert results[0].agent_id == "a1"

    def test_query_by_type(self, pool):
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="c1", tags=[], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a1", memory_type="semantic",
                          content="c2", tags=[], timestamp=200.0)
        pool.store(r1)
        pool.store(r2)
        results = pool.query({"memory_type": "semantic"})
        assert len(results) == 1
        assert results[0].memory_type == "semantic"

    def test_query_by_tags(self, pool):
        r = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                         content="c1", tags=["work", "urgent"], timestamp=100.0)
        pool.store(r)
        results = pool.query({"tags": ["work"]})
        assert len(results) == 1

    def test_query_by_timestamp_range(self, pool):
        r = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                         content="c1", tags=[], timestamp=500.0)
        pool.store(r)
        results = pool.query({"since": 0, "until": 100})
        assert len(results) == 0

    def test_get_agent_memories(self, pool):
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="c1", tags=[], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a1", memory_type="episodic",
                          content="c2", tags=[], timestamp=200.0)
        pool.store(r1)
        pool.store(r2)
        results = pool.get_agent_memories("a1")
        assert len(results) == 2

    def test_stats(self, pool, sample_record):
        pool.store(sample_record)
        s = pool.stats()
        assert s["total_records"] == 1
        assert s["agent_count"] == 1

    def test_stats_empty(self, pool):
        s = pool.stats()
        assert s["total_records"] == 0

    def test_cleanup(self, pool):
        old = MemoryRecord(id="old", agent_id="a1", memory_type="episodic",
                           content="old", tags=[], timestamp=0.0)
        recent = MemoryRecord(id="recent", agent_id="a1", memory_type="episodic",
                              content="new", tags=[],
                              timestamp=9999999999.0)
        pool.store(old)
        pool.store(recent)
        pool.cleanup(max_age_days=0)  # remove everything older than now
        results = pool.query({})
        assert len(results) == 1

    def test_clear(self, pool, sample_record):
        pool.store(sample_record)
        pool.clear()
        assert pool.stats()["total_records"] == 0

    def test_file_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            pool = MemoryPool(storage_path=path)
            r = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                             content="persisted", tags=["test"], timestamp=100.0)
            pool.store(r)

            # Reload
            pool2 = MemoryPool(storage_path=path)
            results = pool2.query({})
            assert len(results) == 1
            assert results[0].content == "persisted"
        finally:
            os.remove(path)
