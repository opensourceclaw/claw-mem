# Copyright 2026 Peter Cheng
"""Base classes for retrieval components (v3.0.0-rc.5)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class SearchResult:
    """Search result from a retriever."""

    id: str
    text: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None


@dataclass
class Document:
    """Document to be indexed."""

    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""

    @abstractmethod
    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        """Search for relevant documents."""
        ...

    @abstractmethod
    def index(self, documents: List[Document]) -> None:
        """Index documents for retrieval."""
        ...

    def clear(self) -> None:
        """Clear all indexed data. Default: no-op."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics. Default: empty dict."""
        return {}
