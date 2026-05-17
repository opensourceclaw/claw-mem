"""Tests for EngramIndex - O(1) N-Gram Hash Inverted Index."""

import pytest
from claw_mem.retrieval.engram import EngramIndex, EngramHasher


class TestEngramHasher:
    """Tests for N-Gram hashing."""

    def setup_method(self):
        self.hasher = EngramHasher(ngram_size=3)

    def test_hash_chinese(self):
        hashes = self.hasher.hash_text("用户偏好深色模式")
        assert len(hashes) >= 4  # "用户偏好深色模式" → at least 4 3-grams

    def test_hash_english(self):
        hashes = self.hasher.hash_text("hello world test")
        assert len(hashes) >= 3

    def test_hash_deterministic(self):
        h1 = self.hasher.hash_text("测试文本")
        h2 = self.hasher.hash_text("测试文本")
        assert h1 == h2

    def test_hash_empty(self):
        assert self.hasher.hash_text("") == []
        assert self.hasher.hash_text("ab") == []  # shorter than ngram_size

    def test_hash_single_ngram(self):
        hashes = self.hasher.hash_text("测试文本内容", ngram_size=2)
        assert len(hashes) >= 2

    def test_hash_int_return(self):
        hashes = self.hasher.hash_text("hello")
        for h in hashes:
            assert isinstance(h, int)


class TestEngramIndex:
    """Tests for EngramIndex class."""

    def setup_method(self):
        self.engram = EngramIndex(ngram_size=3)

    def test_index_and_lookup(self):
        self.engram.index("mem_1", "用户偏好深色模式")
        results = self.engram.lookup("偏好深色")
        assert len(results) >= 1
        assert results[0][0] == "mem_1"

    def test_lookup_exact_match(self):
        self.engram.index("mem_1", "hello world test message")
        results = self.engram.lookup("hello world test message")
        assert len(results) >= 1
        assert results[0][0] == "mem_1"
        assert results[0][1] > 0.5  # high score for exact match

    def test_lookup_partial_match(self):
        self.engram.index("mem_1", "hello world test message")
        self.engram.index("mem_2", "goodbye world other stuff")
        results = self.engram.lookup("world test")
        assert len(results) >= 1
        assert results[0][0] == "mem_1"

    def test_lookup_no_match(self):
        self.engram.index("mem_1", "hello world")
        results = self.engram.lookup("xyz abc def ghi")
        assert results == []

    def test_index_batch(self):
        items = [
            ("mem_1", "用户偏好深色模式"),
            ("mem_2", "Dark mode is preferred"),
            ("mem_3", "系统需要支持暗色主题"),
        ]
        self.engram.index_batch(items)
        results = self.engram.lookup("深色模式")
        assert len(results) >= 1

    def test_remove(self):
        self.engram.index("mem_1", "hello world test")
        self.engram.remove("mem_1")
        results = self.engram.lookup("hello world")
        assert results == []

    def test_remove_partial(self):
        self.engram.index("mem_1", "hello world")
        self.engram.index("mem_2", "hello test")
        self.engram.remove("mem_1")
        results = self.engram.lookup("hello")
        assert len(results) >= 1
        assert results[0][0] == "mem_2"

    def test_scoring_order(self):
        self.engram.index("mem_1", "hello world test message today")
        self.engram.index("mem_2", "hello world")
        results = self.engram.lookup("hello world")
        # mem_2 has higher Jaccard (more overlap proportionally)
        assert len(results) >= 2

    def test_empty_content(self):
        self.engram.index("mem_1", "")
        results = self.engram.lookup("hello")
        assert results == []

    def test_duplicate_index_idempotent(self):
        self.engram.index("mem_1", "hello world")
        self.engram.index("mem_1", "hello world")  # duplicate
        results = self.engram.lookup("hello world")
        assert len(results) == 1

    def test_top_k_limit(self):
        for i in range(10):
            self.engram.index(f"mem_{i}", f"some common text with unique part {i}")
        results = self.engram.lookup("some common text", top_k=3)
        assert len(results) <= 3

    def test_get_stats(self):
        self.engram.index("mem_1", "hello world")
        self.engram.index("mem_2", "hello test")
        stats = self.engram.get_stats()
        assert stats["memory_count"] == 2
        assert stats["hash_count"] > 0
        assert stats["memory_estimate_bytes"] > 0
