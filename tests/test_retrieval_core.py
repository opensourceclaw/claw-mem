# Copyright 2026 Peter Cheng
"""Tests for consolidated retrieval layer."""

import pytest


class TestKeywordRetriever:
    @pytest.fixture
    def retriever(self):
        from claw_mem.retrieval.keyword import KeywordRetriever
        return KeywordRetriever()

    def test_init(self, retriever):
        assert retriever is not None
        assert retriever.scorer is not None

    def test_empty_query(self, retriever):
        from unittest.mock import MagicMock
        ep = MagicMock()
        ep.get_recent.return_value = []
        sem = MagicMock()
        sem.get_all.return_value = []
        proc = MagicMock()
        proc.get_all.return_value = []
        results = retriever.search("", ep, sem, proc)
        assert isinstance(results, list)

    def test_keyword_match(self, retriever):
        from unittest.mock import MagicMock
        ep = MagicMock()
        ep.get_recent.return_value = [{"content": "Python is great", "id": "1"}]
        sem = MagicMock()
        sem.get_all.return_value = []
        proc = MagicMock()
        proc.get_all.return_value = []
        results = retriever.search("Python", ep, sem, proc)
        assert len(results) > 0
        assert results[0]["content"] == "Python is great"

    def test_returns_normalized_fields(self, retriever):
        from unittest.mock import MagicMock
        ep = MagicMock()
        ep.get_recent.return_value = [{"content": "test", "id": "abc"}]
        sem = MagicMock()
        sem.get_all.return_value = []
        proc = MagicMock()
        proc.get_all.return_value = []
        results = retriever.search("test", ep, sem, proc)
        assert results[0]["content"] == "test"
        assert results[0]["metadata"] == {}
        assert results[0]["tags"] == []
        assert results[0]["memory_type"] is not None

    def test_limit_respected(self, retriever):
        from unittest.mock import MagicMock
        mems = [{"content": f"test{i}", "id": str(i)} for i in range(20)]
        ep = MagicMock()
        ep.get_recent.return_value = mems
        sem = MagicMock()
        sem.get_all.return_value = []
        proc = MagicMock()
        proc.get_all.return_value = []
        results = retriever.search("test", ep, sem, proc, limit=5)
        assert len(results) <= 5


class TestTieredRetriever:
    def test_import(self):
        from claw_mem.retrieval.tiered import TieredRetriever
        assert TieredRetriever is not None

    def test_import_aliased(self):
        from claw_mem.retrieval.tiered import MemoryLayer, MemoryResult
        assert MemoryLayer is not None
        assert MemoryResult is not None


class TestSmartRetriever:
    def test_imports(self):
        from claw_mem.retrieval.smart import (
            SmartRetriever, HeuristicRetriever,
            EnhancedSmartRetriever, DecoupledRetriever
        )
        assert SmartRetriever is not None

    def test_heuristic_import(self):
        from claw_mem.retrieval.smart import HeuristicConfig
        assert HeuristicConfig is not None


class TestRetrievalInit:
    def test_consolidated_exports(self):
        from claw_mem.retrieval import (
            KeywordRetriever, SmartRetriever, TieredRetriever
        )
        assert KeywordRetriever is not None
        assert SmartRetriever is not None
        assert TieredRetriever is not None

    def test_legacy_exports(self):
        from claw_mem.retrieval import BM25Retriever, HybridSearcher
        assert BM25Retriever is not None
        assert HybridSearcher is not None

    def test_infrastructure_exports(self):
        from claw_mem.retrieval import QueryCache, SynonymExpander, SearchStats
        assert QueryCache is not None
        assert SynonymExpander is not None
        assert SearchStats is not None
