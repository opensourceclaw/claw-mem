"""Tests for CompressionSpectrum Engram sync (v2.18.0)."""

import pytest
from claw_mem.compression.spectrum import CompressionSpectrum
from claw_mem.retrieval.engram import EngramIndex


class MockMM:
    """Minimal mock for MemoryManager to test Engram sync."""
    def __init__(self):
        self._engram = EngramIndex(ngram_size=3)

    @property
    def engram(self):
        return self._engram


class TestCompressionEngramSync:
    """Tests that compressed content is synced to EngramIndex."""

    def setup_method(self):
        self.mm = MockMM()
        self.cs = CompressionSpectrum(self.mm,
                                      access_threshold=3,
                                      apply_threshold=2,
                                      verify_threshold=1)

    def test_sync_to_engram_direct(self):
        self.cs._sync_to_engram("test_id", "Some skill content")
        results = self.mm.engram.lookup("Some skill content")
        assert len(results) >= 1
        assert results[0][0] == "test_id"

    def test_sync_to_engram_multiple(self):
        self.cs._sync_to_engram("id1", "[Skill] Install Redis cache")
        self.cs._sync_to_engram("id2", "[Rule] IF cache needed THEN use Redis")
        results = self.mm.engram.lookup("Redis cache")
        assert len(results) >= 1
        results2 = self.mm.engram.lookup("cache needed")
        assert len(results2) >= 1

    def test_sync_no_mm_no_error(self):
        cs = CompressionSpectrum()  # no MM
        cs._sync_to_engram("id", "content")
        # Should not raise

    def test_sync_to_engram_skill_like_compressed(self):
        """Simulate what _compress_to_skill would do."""
        body = "[Skill] Setup Redis\n  1. pip install redis\n  2. configure pool"
        self.cs._sync_to_engram("skill_abc", body)
        results = self.mm.engram.lookup("Setup Redis")
        assert len(results) >= 1

    def test_sync_to_engram_rule_like_compressed(self):
        body = "[Rule] IF User needs cache THEN install Redis"
        self.cs._sync_to_engram("rule_xyz", body)
        results = self.mm.engram.lookup("cache install Redis")
        assert len(results) >= 1

    def test_sync_to_engram_principle_like_compressed(self):
        body = "[Principle] Prioritize mature open-source components"
        self.cs._sync_to_engram("prin_def", body)
        results = self.mm.engram.lookup("mature open-source")
        assert len(results) >= 1

    def test_sync_does_not_affect_existing_entries(self):
        self.cs._sync_to_engram("a", "content A")
        self.cs._sync_to_engram("b", "content B")
        # Both should be searchable
        r_a = self.mm.engram.lookup("content A")
        r_b = self.mm.engram.lookup("content B")
        assert len(r_a) >= 1
        assert len(r_b) >= 1
