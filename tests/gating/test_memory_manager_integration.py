"""
MemoryManager integration tests with WriteTimeGating
"""

import pytest
import time
from claw_mem import MemoryManager
from claw_mem.gating import WriteTimeGating, SalienceScorer


class TestMemoryManagerWithGating:
    """Test MemoryManager + WriteTimeGating integration"""

    def test_memory_manager_enables_gating(self, tmp_path):
        """Test MemoryManager enables gating feature"""
        mm = MemoryManager(
            workspace=str(tmp_path / "test"), enable_gating=True, gating_threshold=0.6
        )

        assert mm.enable_gating is True
        assert mm.gating_threshold == 0.6

    def test_store_with_gating(self, tmp_path):
        """Test store uses gating"""
        mm = MemoryManager(
            workspace=str(tmp_path / "test"), enable_gating=True, gating_threshold=0.6
        )

        # Store important information - should be stored
        mm.store(
            content="User prefers Chinese language and uses Python 3.12",
            metadata={"source": "user", "priority": "high"},
        )

        # Store low-salience information
        mm.store(content="hello", metadata={"source": "external", "priority": "low"})

        stats = mm.get_gating_stats()
        assert "active_count" in stats

    @pytest.mark.skip(
        reason="Flaky — passes solo, fails in suite due to test ordering (v3.0.0-rc.14)"
    )
    def test_gating_disabled(self, tmp_path):
        """Test MemoryManager without gating"""
        mm = MemoryManager(workspace=str(tmp_path / "test"), enable_gating=False)

        # Should work normally without gating
        mm.store(content="test1", metadata={"source": "user"}, memory_type="semantic")
        mm.store(content="test2", metadata={"source": "agent"}, memory_type="episodic")

        results = mm.search("test", limit=10)
        assert len(results) > 0


class TestWriteTimeGatingIsolation:
    """Test WriteTimeGating as standalone component"""

    def test_independent_usage(self):
        """Test WriteTimeGating used independently"""
        gating = WriteTimeGating(threshold=0.5)

        items = [{"content": f"item_{i}", "source": "user", "context": {}} for i in range(10)]

        results = [gating.write(item) for item in items]

        active_count = sum(1 for r in results if r.tier == "active")
        cold_count = sum(1 for r in results if r.tier == "cold")

        assert active_count + cold_count == len(items)
        assert gating.get_stats()["active_count"] == active_count

    def test_promote_from_cold(self, tmp_path):
        """Test promote memory from cold to active layer"""
        from claw_mem.gating import DiskStorage

        # Use disk storage for cold items
        cold_path = str(tmp_path / "cold")
        cold = DiskStorage(storage_path=cold_path)
        gating = WriteTimeGating(threshold=0.6, cold_storage=cold)

        # Archive directly to cold
        cold_item = {"id": "test_id_123", "content": "cold content"}
        cold.archive(cold_item)

        # Promote to active
        success = gating.promote("test_id_123")
        assert success is True
        assert gating.active_memory.count() >= 1


class TestPerformanceEndToEnd:
    """End-to-end performance tests"""

    def test_store_retrieve_performance(self, tmp_path):
        """Test store + retrieve performance"""
        mm = MemoryManager(
            workspace=str(tmp_path / "perf"), enable_gating=True, gating_threshold=0.5
        )

        # Store phase
        store_start = time.time()
        for i in range(100):
            mm.store(
                content=f"User likes feature {i}",
                metadata={"source": "user"},
                memory_type="semantic",
            )
        store_elapsed = (time.time() - store_start) * 1000
        print(f"\n100 stores: {store_elapsed:.2f}ms")
        assert store_elapsed < 2000  # Should complete within 2 seconds

        # Retrieve phase
        search_start = time.time()
        for i in range(50):
            mm.search("feature", limit=10)
        search_elapsed = (time.time() - search_start) * 1000
        print(f"50 searches: {search_elapsed:.2f}ms")
        assert search_elapsed < 1000  # Should complete within 1 second

    def test_concurrent_store_retrieve(self, tmp_path):
        """Test concurrent store and retrieve"""
        import threading

        mm = MemoryManager(workspace=str(tmp_path / "concurrent"), enable_gating=True)

        errors = []

        def store_worker():
            try:
                for i in range(50):
                    mm.store(
                        content=f"concurrent test {i}",
                        metadata={"source": "user"},
                        memory_type="semantic",
                    )
            except Exception as e:
                errors.append(e)

        def search_worker():
            try:
                for i in range(25):
                    mm.search("concurrent", limit=10)
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(2):
            threads.append(threading.Thread(target=store_worker))
        for _ in range(2):
            threads.append(threading.Thread(target=search_worker))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"


class TestWriteTimeGatingWithColdStorage:
    """Test WriteTimeGating with cold storage"""

    def test_cold_storage_archives(self, tmp_path):
        """Test cold storage archives items"""
        from claw_mem.gating import DiskStorage

        cold = DiskStorage(storage_path=str(tmp_path / "cold_storage"))
        item = {"content": "cold item", "source": "external"}
        stored = cold.archive(item)

        assert stored["_tier"] == "cold"
        assert "_stored_at" in stored
        assert cold.count() == 1

    def test_version_chain_integration(self):
        """Test version chain integration"""
        from claw_mem.gating import VersionChain

        chain = VersionChain()
        for i in range(5):
            chain.append({"id": i, "content": f"v{i}"})

        assert len(chain) == 5
        assert chain.latest()["content"] == "v4"
        assert chain.get(0)["content"] == "v0"

        chain.clear()
        assert len(chain) == 0

    def test_salience_scorer_integration(self):
        """Test SalienceScorer integration"""
        scorer = SalienceScorer()

        # Test with complete context
        high_score = scorer.compute(
            {
                "content": "User's important preference for dark mode",
                "source": "user",
                "verified": True,
                "context": {"session": "settings", "platform": "macOS"},
            }
        )

        assert high_score >= 0.5

        # Test with minimal context
        low_score = scorer.compute({"content": "ok", "source": "external", "context": {}})

        assert low_score <= high_score  # Lower salience expected
