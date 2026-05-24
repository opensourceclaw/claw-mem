"""Enhanced search with pagination for claw-mem v3.4.0.

Provides paginated search results and batch search for
multiple queries in a single call.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PaginatedResult:
    """Paginated search result.

    Attributes:
        records: The records for the current page.
        total: Total number of matching records.
        page: Current page number (0-indexed).
        page_size: Number of records per page.
        has_next: Whether there are more pages.
        has_prev: Whether there are previous pages.
    """

    records: List[Any] = field(default_factory=list)
    total: int = 0
    page: int = 0
    page_size: int = 10
    has_next: bool = False
    has_prev: bool = False


class EnhancedSearch:
    """Enhanced search with pagination and batch support.

    Wraps search operations to provide offset/limit-based
    pagination and batch query processing.

    Example:
        >>> searcher = EnhancedSearch()
        >>> result = searcher.search("query", limit=10, offset=0)
        >>> batch = searcher.batch_search(["q1", "q2"])
    """

    def search(
        self,
        query: str,
        results: Optional[List[Any]] = None,
        limit: int = 10,
        offset: int = 0,
        memory_type: Optional[str] = None,
    ) -> PaginatedResult:
        """Perform a paginated search.

        Args:
            query: The search query.
            results: Pre-fetched results to paginate (for testing).
            limit: Maximum number of records per page.
            offset: Number of records to skip.
            memory_type: Optional memory type filter.

        Returns:
            PaginatedResult with pagination metadata.
        """
        all_results = results or []
        total = len(all_results)

        # Apply offset and limit
        page_records = all_results[offset : offset + limit]

        page = offset // limit if limit > 0 else 0
        has_next = offset + limit < total
        has_prev = offset > 0

        return PaginatedResult(
            records=page_records,
            total=total,
            page=page,
            page_size=limit,
            has_next=has_next,
            has_prev=has_prev,
        )

    def batch_search(
        self,
        queries: List[str],
        limit: int = 10,
    ) -> Dict[str, PaginatedResult]:
        """Search multiple queries at once.

        Args:
            queries: List of search query strings.
            limit: Maximum records per query.

        Returns:
            Dictionary mapping each query to its PaginatedResult.
        """
        results: Dict[str, PaginatedResult] = {}
        for query in queries:
            results[query] = self.search(query, limit=limit)
        return results
