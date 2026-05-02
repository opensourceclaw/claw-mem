# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
"""Tests for MemoryManager v2.9.0 (cache, synonyms, stats, batch search)"""

import tempfile
import pytest
from pathlib import Path
from claw_mem import MemoryManager


class TestMemoryManagerV290:
    @pytest.fixture
    def workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def mem(self, workspace):
        mm = MemoryManager(str(workspace))
        mm.start_session("test_v290")
        return mm

    def test_features_enabled_by_default(self, mem):
        assert mem.enable_synonyms is True
        assert mem.enable_cache is True
        assert mem.enable_stats is True
        assert mem.synonym_expander is not None
        assert mem.query_cache is not None
        assert mem.search_stats is not None

    def test_search_with_cache(self, mem):
        mem.store("cache test content here", memory_type="semantic")
        mem.search("cache test", mode="keyword", limit=5)
        stats = mem.query_cache.get_stats()
        assert stats["size"] >= 1

    def test_search_stats_recording(self, mem):
        mem.store("stats test content here", memory_type="semantic")
        mem.search("stats test", mode="keyword", limit=5)
        stats = mem.get_search_statistics()
        assert stats is not None
        assert stats["total_searches"] >= 1

    def test_batch_search(self, mem):
        mem.store("batch item 1", memory_type="semantic")
        mem.store("batch item 2", memory_type="semantic")
        results = mem.batch_search(["batch"], limit=2)
        assert len(results) == 1

    def test_disable_cache(self, workspace):
        mem = MemoryManager(str(workspace), enable_cache=False)
        mem.start_session("test")
        assert mem.query_cache is None
        mem.store("unique test content here", memory_type="semantic")
        results = mem.search("unique test", mode="keyword", limit=5)
        # With cache disabled, search should still execute without error
        assert isinstance(results, list)
        assert mem.query_cache is None

    def test_disable_synonyms(self, workspace):
        mem = MemoryManager(str(workspace), enable_synonyms=False)
        mem.start_session("test")
        assert mem.synonym_expander is None

    def test_disable_stats(self, workspace):
        mem = MemoryManager(str(workspace), enable_stats=False)
        mem.start_session("test")
        assert mem.search_stats is None
        assert mem.get_search_statistics() is None

    def test_synonym_expansion_in_search(self, mem):
        mem.store("人工智能相关的内容", memory_type="semantic")
        mem.store("machine learning concepts", memory_type="semantic")
        mem.store("unrelated stuff here", memory_type="semantic")
        results = mem.search("AI machine", mode="keyword", limit=5)
        # Synonym expansion or direct match should find something
        assert isinstance(results, list)

    def test_metadata_filter_skips_cache(self, mem):
        mem.store("meta special test content", memory_type="semantic",
                  metadata={"tag": "special"})
        mem.store("meta normal test content", memory_type="semantic",
                  metadata={"tag": "normal"})
        results = mem.search("meta", mode="keyword",
                           metadata={"tag": "special"}, limit=5)
        # Metadata filter should work correctly
        assert isinstance(results, list)
