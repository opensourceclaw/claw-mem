"""
AgentAgnosticMemory — cross-agent memory format for claw-mem v4.0.

Provides standardized memory records, format conversion between
local and shared representations, PII filtering, and query filters
for cross-agent memory sharing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re
import uuid
import time


@dataclass
class MemoryRecord:
    """Standardized memory record for cross-agent sharing.

    Attributes:
        id: Unique record identifier.
        agent_id: The agent that created the memory.
        memory_type: "episodic" / "semantic" / "procedural" / "shared".
        content: Memory content string.
        tags: Categorization tags.
        timestamp: Unix timestamp when created.
        confidence: Confidence score (0.0–1.0).
        source: "local" or "shared".
    """

    id: str
    agent_id: str
    memory_type: str
    content: str
    tags: List[str]
    timestamp: float
    confidence: float = 1.0
    source: str = "local"


# PII patterns for auto-filtering before cross-agent sharing
_PII_PATTERNS = [
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL]"),
    (re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b"), "[SSN]"),
    (re.compile(r"(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\w\-]+", re.IGNORECASE), "[API_KEY]"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "[API_KEY]"),
]


class AgentAgnosticMemory:
    """Static utilities for cross-agent memory format conversion.

    Example:
        >>> record = AgentAgnosticMemory.to_shared_format(
        ...     {"content": "hello", "tags": ["greeting"]},
        ...     agent_id="agent1",
        ... )
        >>> local = AgentAgnosticMemory.from_shared_format(record)
        >>> filt = AgentAgnosticMemory.create_filter(agent_id="agent1")
    """

    @staticmethod
    def to_shared_format(
        memory: Dict[str, Any], agent_id: str
    ) -> MemoryRecord:
        """Convert a local memory dict to shared MemoryRecord format.

        Args:
            memory: Dictionary with memory data (content, tags, etc.).
            agent_id: ID of the agent that created the memory.

        Returns:
            Standardized MemoryRecord.
        """
        content = str(memory.get("content", ""))
        if not content.strip():
            raise ValueError("Content is required for MemoryRecord")

        # Strip PII before sharing
        clean_content = AgentAgnosticMemory._strip_pii(content)

        return MemoryRecord(
            id=memory.get("id", str(uuid.uuid4())),
            agent_id=agent_id,
            memory_type=memory.get("memory_type", "shared"),
            content=clean_content,
            tags=list(memory.get("tags", [])),
            timestamp=memory.get("timestamp", time.time()),
            confidence=memory.get("confidence", 1.0),
            source="shared",
        )

    @staticmethod
    def from_shared_format(record: MemoryRecord) -> Dict[str, Any]:
        """Convert a shared MemoryRecord back to local format.

        Args:
            record: The shared MemoryRecord.

        Returns:
            Dictionary in local memory format.
        """
        return {
            "id": record.id,
            "content": record.content,
            "memory_type": record.memory_type,
            "tags": record.tags,
            "timestamp": record.timestamp,
            "confidence": record.confidence,
            "agent_id": record.agent_id,
            "source": record.source,
        }

    @staticmethod
    def create_filter(
        agent_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        since: Optional[float] = None,
        until: Optional[float] = None,
        min_confidence: float = 0.0,
    ) -> Dict[str, Any]:
        """Create a filter dict for querying MemoryPool.

        Args:
            agent_id: Filter by agent ID.
            memory_type: Filter by memory type.
            tags: Filter by tags (any match).
            since: Filter records after timestamp.
            until: Filter records before timestamp.
            min_confidence: Minimum confidence threshold.

        Returns:
            Filter dictionary for MemoryPool.query().
        """
        filt: Dict[str, Any] = {}
        if agent_id is not None:
            filt["agent_id"] = agent_id
        if memory_type is not None:
            filt["memory_type"] = memory_type
        if tags is not None:
            filt["tags"] = tags
        if since is not None:
            filt["since"] = since
        if until is not None:
            filt["until"] = until
        if min_confidence > 0.0:
            filt["min_confidence"] = min_confidence
        return filt

    @staticmethod
    def _strip_pii(content: str) -> str:
        """Strip known PII patterns from content.

        Args:
            content: Original content string.

        Returns:
            Content with PII patterns replaced by placeholders.
        """
        for pattern, replacement in _PII_PATTERNS:
            content = pattern.sub(replacement, content)
        return content
