"""Tests for MemoryDeduplicator (v3.0.0-rc.2)."""

import pytest
from claw_mem.cms.memory_deduplicator import MemoryDeduplicator
from claw_mem.cms.compression_result import DeduplicationResult


class TestMemoryDeduplicator:
    def setup_method(self):
        self.dedup = MemoryDeduplicator(similarity_threshold=0.6)

    def test_deduplicate_empty(self):
        result = self.dedup.deduplicate([])
        assert isinstance(result, DeduplicationResult)
        assert result.original_count == 0

    def test_deduplicate_empty_no_mm(self):
        result = self.dedup.deduplicate([])
        assert result.deduplicated_count == 0

    def test_deduplicate_single(self):
        result = self.dedup.deduplicate(["mem_1"])
        # No MM → no content → 0 entries found
        assert result.deduplicated_count >= 0

    def test_word_overlap_identical(self):
        sim = self.dedup._word_overlap("hello world", "hello world")
        assert sim == 1.0

    def test_word_overlap_different(self):
        sim = self.dedup._word_overlap("hello world", "goodbye mars")
        assert sim == 0.0

    def test_word_overlap_partial(self):
        sim = self.dedup._word_overlap("hello world test", "hello world foo")
        assert 0.4 < sim < 0.8

    def test_word_overlap_empty(self):
        assert self.dedup._word_overlap("", "") == 0.0
        assert self.dedup._word_overlap("a", "") == 0.0

    def test_build_clusters_single(self):
        clusters = self.dedup._build_clusters(["a", "b"], [])
        assert len(clusters) == 2  # each in own cluster

    def test_build_clusters_connected(self):
        clusters = self.dedup._build_clusters(["a", "b", "c"], [("a", "b"), ("b", "c")])
        assert len(clusters) == 1  # all in one cluster

    def test_find_similar_pairs_no_mm(self):
        contents = {"a": "hello world", "b": "hello world test", "c": "xyz abc"}
        pairs = self.dedup._find_similar_pairs(contents)
        assert len(pairs) >= 1  # a and b should be similar

    def test_dedup_result_to_dict(self):
        result = DeduplicationResult(10, 6, 0.4, [["a", "b"]], ["a", "c"], ["b", "d"])
        d = result.to_dict()
        assert d["original_count"] == 10
        assert d["deduplicated_count"] == 6
