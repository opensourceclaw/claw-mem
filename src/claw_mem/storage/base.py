# Copyright 2026 Peter Cheng
"""Base classes for storage components (v3.0.0-rc.5)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryRecord:
    """A memory record in storage."""

    id: str
    text: str
    memory_type: str  # episodic, semantic, procedural
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)


class BaseStorage(ABC):
    """Abstract base class for all storage backends."""

    @abstractmethod
    def store(self, record: MemoryRecord) -> str:
        """Store a memory record. Returns record ID."""
        ...

    @abstractmethod
    def retrieve(self, id: str) -> Optional[MemoryRecord]:
        """Retrieve a memory by ID."""
        ...

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete a memory by ID."""
        ...

    @abstractmethod
    def list_all(self, memory_type: Optional[str] = None, limit: int = 100) -> List[MemoryRecord]:
        """List all memories, optionally filtered by type."""
        ...

    def count(self, memory_type: Optional[str] = None) -> int:
        """Count memories."""
        return len(self.list_all(memory_type=memory_type, limit=10**9))
