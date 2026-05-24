"""Type definitions for claw-mem v3.4.0."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

T = TypeVar("T")


class MemoryType(Enum):
    """Type of memory in the three-tier system."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


@dataclass(frozen=True)
class MemoryRecord:
    """Immutable memory record.

    Attributes:
        id: Unique memory identifier.
        content: Memory content.
        memory_type: Tier type (episodic/semantic/procedural).
        metadata: Additional metadata.
    """

    id: str
    content: str
    memory_type: MemoryType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    """Search result from memory query.

    Attributes:
        records: Matching memory records.
        score: Relevance score (0.0 to 1.0).
        total: Total matching records.
    """

    records: List[MemoryRecord] = field(default_factory=list)
    score: float = 0.0
    total: int = 0


class MemoryStore(Protocol):
    """Protocol for memory store implementations."""

    def store(self, record: MemoryRecord) -> str:
        """Store a memory record.

        Returns:
            The memory ID.
        """
        ...

    def search(
        self, query: str, limit: int = 10
    ) -> SearchResult:
        """Search memories by query.

        Returns:
            SearchResult with matching records.
        """
        ...

    def recall(
        self, memory_id: str
    ) -> Optional[MemoryRecord]:
        """Recall a memory by ID.

        Returns:
            MemoryRecord if found, None otherwise.
        """
        ...
