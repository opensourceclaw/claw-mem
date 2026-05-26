"""Tests for claw_mem.memory.sync (CrossAgentSync)."""

import pytest
from claw_mem.memory.sync import CrossAgentSync
from claw_mem.memory.pool import MemoryPool
from claw_mem.memory.agnostic import MemoryRecord


@pytest.fixture
def pool():
    return MemoryPool()


@pytest.fixture
def sync(pool):
    return CrossAgentSync(pool=pool)


class TestCrossAgentSync:
    def test_push_to_pool(self, sync, pool):
        record = MemoryRecord(
            id="r1", agent_id="a1", memory_type="episodic",
            content="test", tags=[], timestamp=100.0,
        )
        result = sync.push(record, target_agents=["a2"])
        assert result is True
        assert pool.stats()["total_records"] == 1

    def test_pull_after_push(self, sync, pool):
        record = MemoryRecord(
            id="r1", agent_id="a1", memory_type="episodic",
            content="test", tags=[], timestamp=500.0,
        )
        sync.push(record, target_agents=["a2"])

        results = sync.pull("a1", since=0.0)
        assert len(results) == 1
        assert results[0].agent_id == "a1"

    def test_pull_since_filter(self, sync, pool):
        record = MemoryRecord(
            id="r1", agent_id="a1", memory_type="episodic",
            content="test", tags=[], timestamp=500.0,
        )
        sync.push(record, target_agents=["a2"])

        # Since after record time → no results
        results = sync.pull("a1", since=1000.0)
        assert len(results) == 0

    def test_subscribe_and_notify(self, sync):
        received = []
        sync.subscribe("a2", lambda r: received.append(r.content))

        record = MemoryRecord(
            id="r1", agent_id="a1", memory_type="episodic",
            content="hello", tags=[], timestamp=100.0,
        )
        sync.push(record, target_agents=["a2"])
        assert "hello" in received

    def test_unsubscribe(self, sync):
        sub_id = sync.subscribe("a1", lambda r: None)
        assert sync.unsubscribe(sub_id) is True

    def test_unsubscribe_nonexistent(self, sync):
        assert sync.unsubscribe("none") is False

    def test_detect_conflict_same_tags_different_content(self, sync):
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="A", tags=["work"], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a2", memory_type="episodic",
                          content="B", tags=["work"], timestamp=200.0)
        conflict = sync.detect_conflict(r1, r2)
        assert conflict is not None
        assert "Conflict" in conflict

    def test_detect_no_conflict_same_content(self, sync):
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="A", tags=["work"], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a2", memory_type="episodic",
                          content="A", tags=["work"], timestamp=200.0)
        assert sync.detect_conflict(r1, r2) is None

    def test_get_stats(self, sync, pool):
        record = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                              content="test", tags=[], timestamp=100.0)
        sync.push(record, target_agents=["a2"])
        sync.pull("a1")
        stats = sync.get_stats()
        assert stats["push_count"] >= 1
        assert stats["pull_count"] >= 1
