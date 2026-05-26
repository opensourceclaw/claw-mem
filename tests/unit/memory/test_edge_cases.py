"""Edge case hardening tests for claw-mem v4.5.0 cross-agent memory."""

import threading
import time
import tempfile
import os
import pytest

from claw_mem.memory.pool import MemoryPool
from claw_mem.memory.sync import CrossAgentSync
from claw_mem.memory.agnostic import AgentAgnosticMemory, MemoryRecord


class TestConcurrentOperations:
    """Test thread-safety for concurrent store/query."""

    def test_concurrent_store_and_query(self):
        pool = MemoryPool()
        errors = []

        def writer(n):
            try:
                for i in range(n):
                    pool.store(MemoryRecord(
                        id=f"r{i}", agent_id="a1",
                        memory_type="episodic", content=f"c{i}",
                        tags=["bench"], timestamp=time.time(),
                    ))
            except Exception as e:
                errors.append(str(e))

        def reader(n):
            try:
                for _ in range(n):
                    pool.query({"agent_id": "a1"})
            except Exception as e:
                errors.append(str(e))

        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=writer, args=(50,)))
            threads.append(threading.Thread(target=reader, args=(50,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"


class TestPIIFilteringEdges:
    """Edge cases for PII filtering."""

    def test_empty_content(self):
        with pytest.raises(ValueError):
            AgentAgnosticMemory.to_shared_format({"content": ""}, "a1")

    def test_whitespace_content(self):
        with pytest.raises(ValueError):
            AgentAgnosticMemory.to_shared_format({"content": "   "}, "a1")

    def test_unicode_edge_cases(self):
        record = AgentAgnosticMemory.to_shared_format(
            {"content": "你好世界 emojis 🎉🚀💥 mixed 内容"}, "a1",
        )
        assert record.content is not None
        assert len(record.content) > 0

    def test_no_pii_in_clean_content(self):
        record = AgentAgnosticMemory.to_shared_format(
            {"content": "The weather is nice today"}, "a1",
        )
        assert record.content == "The weather is nice today"

    def test_multiple_phones_filtered(self):
        record = AgentAgnosticMemory.to_shared_format(
            {"content": "Call 555-123-4567 or 555-987-6543"}, "a1",
        )
        assert "555-" not in record.content
        assert "[PHONE]" in record.content


class TestFilePersistence:
    """File-backed persistence edge cases."""

    def test_corrupted_file_recovery(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
            f.write(b"not valid json {{{")
        try:
            pool = MemoryPool(storage_path=path)
            pool.store(MemoryRecord(
                id="r1", agent_id="a1", memory_type="episodic",
                content="recovered", tags=[], timestamp=100.0,
            ))
            results = pool.query({})
            assert len(results) == 1
        finally:
            os.remove(path)

    def test_concurrent_writes(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            pool = MemoryPool(storage_path=path)
            errors = []

            def writer(n):
                try:
                    for i in range(n):
                        pool.store(MemoryRecord(
                            id=f"cw{i}", agent_id="a1",
                            memory_type="episodic", content=f"c{i}",
                            tags=[], timestamp=time.time(),
                        ))
                except Exception as e:
                    errors.append(str(e))

            threads = [threading.Thread(target=writer, args=(30,)) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0
        finally:
            os.remove(path)


class TestSyncEdges:
    """CrossAgentSync edge cases."""

    def test_conflict_none_with_no_common_tags(self):
        sync = CrossAgentSync()
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="Hello", tags=["work"], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a2", memory_type="episodic",
                          content="World", tags=["home"], timestamp=200.0)
        assert sync.detect_conflict(r1, r2) is None

    def test_conflict_same_content_no_conflict(self):
        sync = CrossAgentSync()
        r1 = MemoryRecord(id="r1", agent_id="a1", memory_type="episodic",
                          content="Same", tags=["work"], timestamp=100.0)
        r2 = MemoryRecord(id="r2", agent_id="a2", memory_type="episodic",
                          content="Same", tags=["work"], timestamp=200.0)
        assert sync.detect_conflict(r1, r2) is None
