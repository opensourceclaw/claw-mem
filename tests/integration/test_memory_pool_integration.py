"""Integration tests for MemoryManager + MemoryPool + CrossAgentSync."""

import pytest
import tempfile
import shutil
from pathlib import Path
from claw_mem.memory_manager import MemoryManager


class TestMemoryManagerWithPool:
    @pytest.fixture
    def memory(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)
        (workspace / "memory").mkdir()
        mm = MemoryManager(str(workspace), enable_memory_pool=True)
        yield mm
        shutil.rmtree(temp_dir)

    def test_pool_property(self, memory):
        memory.start_session("test")
        pool = memory.pool
        assert pool is not None

    def test_store_to_pool(self, memory):
        memory.start_session("test")
        memory.store("Shared memory content", memory_type="episodic", tags=["shared"])
        pool = memory.pool
        results = pool.query({})
        assert len(results) == 1
        assert results[0].content == "Shared memory content"

    def test_pool_not_enabled(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)
        (workspace / "memory").mkdir()
        mm = MemoryManager(str(workspace))
        pool = mm.pool
        assert pool is None
        shutil.rmtree(temp_dir)


class TestMemoryManagerWithSync:
    @pytest.fixture
    def memory(self):
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)
        (workspace / "memory").mkdir()
        mm = MemoryManager(
            str(workspace),
            enable_memory_pool=True,
            enable_cross_agent_sync=True,
        )
        yield mm
        shutil.rmtree(temp_dir)

    def test_sync_property(self, memory):
        sync = memory.sync
        assert sync is not None

    def test_push_and_pull(self, memory):
        from claw_mem.memory.agnostic import MemoryRecord

        memory.start_session("test")
        sync = memory.sync

        record = MemoryRecord(
            id="r1", agent_id="agent1", memory_type="episodic",
            content="sync test", tags=["test"], timestamp=1000.0,
        )
        sync.push(record, target_agents=["agent2"])
        results = sync.pull("agent1")
        assert len(results) == 1
