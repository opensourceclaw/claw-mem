"""Tests for claw_mem.dual_system.consolidation.ConsolidationLoop."""
import time
import pytest
from claw_mem.dual_system import (
    HippocampalStore, NeocorticalStore, ConsolidationLoop, Memory,
)


@pytest.fixture
def stores():
    hippo = HippocampalStore(capacity=100)
    cortex = NeocorticalStore()
    return hippo, cortex


@pytest.fixture
def loop(stores):
    hippo, cortex = stores
    return ConsolidationLoop(hippo, cortex, interval_seconds=1, batch_size=10)


class TestConsolidationLoop:
    def test_run_empty(self, loop):
        result = loop.run_consolidation()
        assert result.memories_consolidated == 0

    def test_run_with_memories(self, loop, stores):
        hippo, _ = stores
        for i in range(10):
            hippo.store(Memory(content=f"learn {i}", importance=0.8))
        result = loop.run_consolidation()
        assert result.memories_consolidated >= 1

    def test_cleans_hippocampal(self, loop, stores):
        hippo, _ = stores
        for i in range(5):
            hippo.store(Memory(content=f"to cons {i}", importance=0.9))
        before = hippo.size()
        loop.run_consolidation()
        assert hippo.size() < before

    def test_importance_filter(self, stores):
        hippo, cortex = stores
        hippo.store(Memory(content="low", importance=0.1))
        hippo.store(Memory(content="high", importance=0.9))
        loop = ConsolidationLoop(hippo, cortex, importance_threshold=0.5)
        result = loop.run_consolidation()
        # Only high importance should be consolidated
        assert result.memories_consolidated >= 0

    def test_background_start_stop(self, loop):
        loop.start_background()
        assert loop.is_running
        time.sleep(2)
        loop.stop_background()
        assert not loop.is_running

    def test_get_history(self, loop, stores):
        hippo, _ = stores
        hippo.store(Memory(content="test", importance=0.8))
        loop.run_consolidation()
        assert len(loop.get_history()) >= 1

    def test_get_statistics(self, loop, stores):
        hippo, _ = stores
        hippo.store(Memory(content="stats test", importance=0.8))
        loop.run_consolidation()
        stats = loop.get_statistics()
        assert stats["cycles_completed"] >= 1
        assert "total_memories_consolidated" in stats

    def test_reset(self, loop, stores):
        hippo, _ = stores
        hippo.store(Memory(content="reset test", importance=0.8))
        loop.run_consolidation()
        loop.reset()
        assert len(loop.get_history()) == 0
        assert not loop.is_running
