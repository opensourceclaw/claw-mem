# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for proactive compression (v3.2.2)."""

import os
import pytest
import tempfile
import shutil
from pathlib import Path

from claw_mem.proactive_compression import (
    ProactiveCompressionChecker,
    ProactiveCompressionConfig,
)
from claw_mem.memory_manager import MemoryManager


@pytest.fixture(autouse=True)
def _silent():
    """Suppress log output during tests."""
    os.environ["CLAW_MEM_SILENT"] = "1"
    yield
    os.environ.pop("CLAW_MEM_SILENT", None)


@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp()
    workspace = Path(temp_dir)
    (workspace / "memory").mkdir()
    yield workspace
    shutil.rmtree(temp_dir)


def _make_memory(content, tags=None, metadata=None):
    """Helper to build a minimal working-memory dict."""
    return {
        "id": f"id_{content[:8]}",
        "content": content,
        "type": "episodic",
        "tags": tags or [],
        "metadata": metadata or {},
        "timestamp": "2026-05-21T00:00:00",
        "session_id": "test_session",
    }


# ── Unit tests for ProactiveCompressionChecker ──────────────────

class TestProactiveCompressionChecker:

    def test_below_threshold_no_compress(self, temp_workspace):
        """Compression should NOT trigger when utilization is below threshold."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=False,
        )
        mm.start_session("test_session")

        # Directly populate working_memory — well below 70% of 100
        mm.working_memory = [_make_memory(f"item {i}") for i in range(10)]

        config = ProactiveCompressionConfig(
            proactive_threshold=0.7,
            max_working_memory=100,
            cooldown_stores=1,
        )
        checker = ProactiveCompressionChecker(mm, config)

        result = checker.check_and_compress()
        assert result is None  # 10/100 = 10% < 70%

    def test_above_threshold_triggers_compression(self, temp_workspace):
        """Compression SHOULD trigger when utilization exceeds threshold."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=False,
        )
        mm.start_session("test_session")

        # Populate above threshold: 15/20 = 75% > 70%
        mm.working_memory = [_make_memory(f"item {i}") for i in range(15)]

        config = ProactiveCompressionConfig(
            proactive_threshold=0.7,
            max_working_memory=20,
            min_memories_to_compress=5,
            cooldown_stores=1,
        )
        checker = ProactiveCompressionChecker(mm, config)

        result = checker.check_and_compress()
        assert result is not None
        assert result["total"] == 15
        assert result["compressed"] > 0
        assert result["utilization_before"] >= 0.7
        # After compression, working_memory should have shrunk
        assert len(mm.working_memory) < 15

    def test_critical_content_preserved(self, temp_workspace):
        """Critical items (TODO/conclusion/important tag) should be preserved."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=False,
        )
        mm.start_session("test_session")

        # Build working_memory: 2 critical + 13 normal = 15 total (75% of 20)
        items = [
            _make_memory("TODO: implement login flow", tags=["important"]),
            _make_memory("结论：使用 Redis 作为缓存方案"),
        ]
        items += [_make_memory(f"normal log line {i}") for i in range(13)]
        mm.working_memory = items

        config = ProactiveCompressionConfig(
            proactive_threshold=0.7,
            max_working_memory=20,
            min_memories_to_compress=5,
            cooldown_stores=1,
        )
        checker = ProactiveCompressionChecker(mm, config)

        result = checker.check_and_compress()
        assert result is not None

        # Critical items should still be in working_memory
        contents = [m.get("content", "") for m in mm.working_memory]
        assert any("TODO: implement login flow" in c for c in contents), \
            "Critical TODO should be preserved"
        assert any("Redis 作为缓存方案" in c for c in contents), \
            "Critical conclusion should be preserved"

    def test_cooldown_prevents_rapid_recompression(self, temp_workspace):
        """After a compression, cooldown period should prevent re-triggering."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=False,
        )
        mm.start_session("test_session")

        # Fill above threshold
        mm.working_memory = [_make_memory(f"item {i}") for i in range(15)]

        config = ProactiveCompressionConfig(
            proactive_threshold=0.7,
            max_working_memory=20,
            min_memories_to_compress=5,
            cooldown_stores=5,
        )
        checker = ProactiveCompressionChecker(mm, config)

        # First call: not in cooldown yet, store_count goes to 1, but 1 < 5 → cooldown
        # Actually cooldown_stores=5 means we need 5 calls before allowing compression.
        # Let me simplify: the first 4 calls skip (1,2,3,4 < 5), the 5th triggers.
        # But after compression, store_count resets to 0, so next call: 1 < 5 → skip.

        # Call 1-4: all skip due to cooldown
        for _ in range(4):
            assert checker.check_and_compress() is None

        # Call 5: cooldown passed, compression triggers
        result1 = checker.check_and_compress()
        assert result1 is not None  # triggered

        # Call 6: cooldown active again (1 < 5)
        result2 = checker.check_and_compress()
        assert result2 is None

    def test_working_memory_reduced_after_compression(self, temp_workspace):
        """After compression, working_memory size should decrease significantly."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=False,
        )
        mm.start_session("test_session")

        mm.working_memory = [_make_memory(f"normal item {i}") for i in range(15)]

        config = ProactiveCompressionConfig(
            proactive_threshold=0.7,
            max_working_memory=20,
            min_memories_to_compress=5,
            cooldown_stores=1,
        )
        checker = ProactiveCompressionChecker(mm, config)

        before = len(mm.working_memory)
        checker.check_and_compress()
        after = len(mm.working_memory)

        assert after < before, f"Expected working_memory to shrink, but {before} -> {after}"
        # Keep at most 5 recent + 1 compression note + 1 archived entry = 7
        assert after <= 7, \
            f"Expected significant reduction to ≤7, but got {after}"


# ── Integration test with MemoryManager.store() ─────────────────

class TestProactiveCompressionIntegration:

    def test_store_auto_triggers_compression(self, temp_workspace):
        """store() should automatically trigger compression at threshold."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=True,
            proactive_threshold=0.7,
            max_working_memory=20,
        )
        mm.start_session("test_session")

        # Override config for fast triggering
        mm._proactive_compressor = ProactiveCompressionChecker(
            mm,
            ProactiveCompressionConfig(
                proactive_threshold=0.7,
                max_working_memory=20,
                min_memories_to_compress=5,
                cooldown_stores=1,
            ),
        )

        # Store enough to exceed threshold
        for i in range(15):
            mm.store(f"item {i}", memory_type="episodic")

        # store() calls check_and_compress() internally on every write.
        # At ~item 13 (14/20 = 70%) compression triggers and reduces wm.
        # Final working_memory should be noticeably less than 15.
        final = len(mm.working_memory)
        assert final < 15, f"Expected auto-compression, but working_memory={final}"

    def test_compression_preserves_recent_items(self, temp_workspace):
        """After auto-compression via store(), the most recent items are kept."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=True,
            proactive_threshold=0.7,
            max_working_memory=20,
        )
        mm.start_session("test_session")

        mm._proactive_compressor = ProactiveCompressionChecker(
            mm,
            ProactiveCompressionConfig(
                proactive_threshold=0.7,
                max_working_memory=20,
                min_memories_to_compress=5,
                cooldown_stores=1,
            ),
        )

        for i in range(15):
            mm.store(f"item {i}", memory_type="episodic")

        # After auto-compression: last 5 + compression note + archived entry
        contents = [m.get("content", "") for m in mm.working_memory]
        # Most recent item should be in the kept set
        ordered = [c for c in contents if c.startswith("item")]
        assert any("14" in c for c in ordered), \
            "Most recent item (14) should be preserved"
        # Oldest items (0-9) should have been compressed away
        assert not any(c == "item 0" for c in contents), \
            "Old item 0 should have been compressed"
        assert len(ordered) < 15, \
            f"Expected fewer than 15 original items, got {len(ordered)}"


class TestProactiveCompressionDisabled:

    def test_no_compression_when_disabled(self, temp_workspace):
        """When enable_proactive_compression=False, no compression happens."""
        mm = MemoryManager(
            str(temp_workspace),
            enable_proactive_compression=False,
            proactive_threshold=0.7,
            max_working_memory=20,
        )
        mm.start_session("test_session")

        for i in range(30):
            mm.store(f"overflow item {i}", memory_type="episodic")

        # All 30 items should remain — no compression
        assert len(mm.working_memory) == 30
