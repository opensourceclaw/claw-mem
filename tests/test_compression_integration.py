"""Tests for MemoryManager compression integration (v2.12.0)."""

import pytest
import tempfile
from pathlib import Path
from claw_mem import MemoryManager
from claw_mem.compression.memory_compression_v2 import CompressionConfig, CompressionResult


class TestCompressionIntegration:
    @pytest.fixture
    def workspace(self):
        return Path(tempfile.mkdtemp())

    def test_compression_enabled_by_default(self):
        mm = MemoryManager("/tmp/_test_claw_mem_comp")
        assert mm.enable_compression is True
        assert mm._compression_config.enabled is True

    def test_compress_with_few_memories_returns_none(self):
        mm = MemoryManager("/tmp/_test_claw_mem_comp2")
        result = mm.compress()
        assert result is None  # No memories to compress

    def test_compress_force(self):
        mm = MemoryManager("/tmp/_test_claw_mem_comp3")
        mm.start_session("test")
        for i in range(3):
            mm.store(f"memory content {i}", memory_type="episodic")
        # Force compression
        result = mm.compress(force=True)
        assert result is not None
        assert isinstance(result, CompressionResult)

    def test_compression_config_api(self):
        mm = MemoryManager("/tmp/_test_claw_mem_comp4")
        config = mm.get_compression_config()
        assert "enabled" in config
        assert "max_memories" in config

    def test_get_compression_history(self):
        mm = MemoryManager("/tmp/_test_claw_mem_comp5")
        mm.start_session("test")
        for i in range(5):
            mm.store(f"content {i}", memory_type="episodic")
        mm.compress(force=True)
        history = mm.get_compression_history()
        assert history["compression_count"] >= 1

    def test_disable_compression(self):
        mm = MemoryManager("/tmp/_test_claw_mem_comp6", enable_compression=False)
        mm.start_session("test")
        for i in range(5):
            mm.store(f"content {i}", memory_type="episodic")
        result = mm.compress(force=True)
        assert result is None
