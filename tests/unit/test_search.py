"""Tests for EnhancedSearch and PaginatedResult."""

from claw_mem.search import EnhancedSearch, PaginatedResult


class TestPaginatedResult:
    """Tests for PaginatedResult."""

    def test_defaults(self):
        result = PaginatedResult()
        assert result.records == []
        assert result.total == 0
        assert result.has_next is False
        assert result.has_prev is False


class TestEnhancedSearch:
    """Tests for EnhancedSearch."""

    def test_search_empty(self):
        searcher = EnhancedSearch()
        result = searcher.search("query")
        assert result.total == 0
        assert result.records == []

    def test_search_with_results_first_page(self):
        searcher = EnhancedSearch()
        results = [{"id": i} for i in range(20)]
        result = searcher.search("query", results=results, limit=10, offset=0)
        assert result.total == 20
        assert len(result.records) == 10
        assert result.page == 0
        assert result.has_next is True
        assert result.has_prev is False

    def test_search_second_page(self):
        searcher = EnhancedSearch()
        results = [{"id": i} for i in range(20)]
        result = searcher.search("query", results=results, limit=10, offset=10)
        assert result.total == 20
        assert len(result.records) == 10
        assert result.page == 1
        assert result.has_next is False
        assert result.has_prev is True

    def test_search_last_partial_page(self):
        searcher = EnhancedSearch()
        results = [{"id": i} for i in range(5)]
        result = searcher.search("query", results=results, limit=10, offset=0)
        assert result.total == 5
        assert len(result.records) == 5
        assert result.has_next is False

    def test_batch_search(self):
        searcher = EnhancedSearch()
        results = searcher.batch_search(["q1", "q2", "q3"])
        assert len(results) == 3
        assert "q1" in results
        assert results["q1"].total == 0

    def test_batch_search_empty(self):
        searcher = EnhancedSearch()
        results = searcher.batch_search([])
        assert results == {}

    def test_search_with_memory_type(self):
        searcher = EnhancedSearch()
        result = searcher.search(
            "query", memory_type="semantic"
        )
        assert result.total == 0
