"""
NeocorticalStore — slow, long-term memory with concept abstraction.

Simulates the neocortex: gradual consolidation, semantic abstraction,
concept graph connections, and forgetting curve application.
"""

import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4


@dataclass
class Concept:
    """An abstract concept extracted from multiple memories.

    Attributes:
        concept_id: Unique concept identifier.
        name: Concept name.
        description: Human-readable description.
        source_memory_ids: Memory IDs that contributed to this concept.
        keywords: Key terms defining this concept.
        confidence: Confidence score (0.0-1.0).
        created_at: Creation timestamp.
        last_reinforced: Last reinforcement timestamp.
    """

    concept_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    source_memory_ids: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    confidence: float = 0.5
    created_at: float = field(default_factory=time.time)
    last_reinforced: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "description": self.description,
            "source_memory_ids": self.source_memory_ids,
            "keywords": self.keywords,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "last_reinforced": self.last_reinforced,
        }


class NeocorticalStore:
    """Slow, long-term memory store with concept abstraction.

    Simulates neocortical function:
    - Consolidates multiple memories into abstract concepts
    - Applies Ebbinghaus forgetting curve for retention
    - Builds semantic connections between concepts
    - Persistent long-term storage

    Usage::

        store = NeocorticalStore()
        concepts = store.consolidate(memories)
        results = store.retrieve("concept")
    """

    # Ebbinghaus forgetting curve parameters
    # Retention R = e^(-t/S) where S is relative strength
    DEFAULT_STRENGTH = 7.0  # Default retention strength (days half-life)

    def __init__(self, capacity: int = 100000):
        self._capacity = capacity
        self._store: Dict[str, Any] = {}  # memory_id -> Memory/concept
        self._concepts: Dict[str, Concept] = {}
        self._connections: Dict[str, Set[str]] = {}  # concept_id -> related concept_ids

    def consolidate(self, memories: List[Any]) -> List[str]:
        """Consolidate multiple memories into concepts.

        Groups memories by keyword similarity, extracts common concepts,
        and stores in neocortical store.

        Args:
            memories: List of Memory objects to consolidate.

        Returns:
            List of consolidated memory IDs.
        """
        if not memories:
            return []

        ids = []
        # Group by memory type
        groups: Dict[str, List] = {}
        for mem in memories:
            mtype = getattr(mem, "memory_type", "episodic")
            groups.setdefault(mtype, []).append(mem)

        for mtype, group in groups.items():
            # Extract concepts from each group
            concepts = self.abstract_concepts(group)
            for concept in concepts:
                existing = self._find_similar_concept(concept)
                if existing:
                    self._reinforce_concept(existing, concept)
                else:
                    self._concepts[concept.concept_id] = concept

            # Store consolidated memory references
            for mem in group:
                mid = getattr(mem, "memory_id", str(uuid4()))
                self._store[mid] = mem
                ids.append(mid)

        return ids

    def retrieve(self, query: str, limit: int = 10) -> List[Any]:
        """Retrieve memories and concepts matching a query.

        Searches both stored memories and abstract concepts.

        Args:
            query: Search query string.
            limit: Maximum results.

        Returns:
            List of Memory/concept dicts.
        """
        query_lower = query.lower()
        results = []

        # Search stored memories
        for mem in self._store.values():
            content = getattr(mem, "content", "")
            if query_lower in content.lower():
                results.append(mem)

        # Search concepts
        for concept in self._concepts.values():
            if query_lower in concept.name.lower() or \
               query_lower in concept.description.lower():
                results.append(concept)

        return results[:limit]

    def abstract_concepts(self, memories: List[Any]) -> List[Concept]:
        """Extract abstract concepts from a group of related memories.

        Uses keyword frequency analysis to identify common themes.

        Args:
            memories: List of Memory objects to analyze.

        Returns:
            List of extracted Concept objects.
        """
        if not memories:
            return []

        # Extract keywords from all memories
        all_keywords: List[str] = []
        for mem in memories:
            content = getattr(mem, "content", "")
            keywords = self._extract_keywords(content)
            all_keywords.extend(keywords)

        if not all_keywords:
            return []

        # Find common keywords (occurring in 50%+ of memories)
        threshold = max(1, len(memories) * 0.5)
        freq = Counter(all_keywords)
        common_keywords = [kw for kw, count in freq.items() if count >= threshold]

        if common_keywords:
            name = " - ".join(common_keywords[:3])
            description = f"Concept from {len(memories)} memories: {', '.join(common_keywords[:5])}"
            concept = Concept(
                name=name,
                description=description,
                source_memory_ids=[getattr(m, "memory_id", "") for m in memories],
                keywords=common_keywords,
                confidence=min(1.0, 0.3 + len(memories) * 0.1),
            )
            return [concept]
        return []

    def apply_forgetting_curve(self, memory_id: str) -> float:
        """Apply Ebbinghaus forgetting curve to estimate retention.

        R = e^(-t/S) where t is age in days, S is retention strength.

        Args:
            memory_id: The memory ID.

        Returns:
            Retention probability (0.0-1.0).
        """
        mem = self._store.get(memory_id)
        if mem is None:
            return 0.0

        age_seconds = getattr(mem, "age_seconds", 0) or (time.time() - getattr(mem, "created_at", time.time()))
        days_elapsed = age_seconds / 86400.0

        if days_elapsed <= 0:
            return 1.0

        # Higher importance = stronger retention (longer half-life)
        importance = getattr(mem, "importance", 0.5)
        strength = self.DEFAULT_STRENGTH * (1.0 + importance)

        retention = math.exp(-days_elapsed / strength)
        return max(0.0, min(1.0, retention))

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get a concept by ID."""
        return self._concepts.get(concept_id)

    def list_concepts(self) -> List[Concept]:
        """List all abstracted concepts."""
        return list(self._concepts.values())

    def get_connections(self, concept_id: str) -> List[str]:
        """Get related concept IDs."""
        return list(self._connections.get(concept_id, set()))

    def connect(self, concept_id_a: str, concept_id_b: str) -> None:
        """Create a connection between two concepts."""
        self._connections.setdefault(concept_id_a, set()).add(concept_id_b)
        self._connections.setdefault(concept_id_b, set()).add(concept_id_a)

    def size(self) -> int:
        """Number of stored memories."""
        return len(self._store)

    def concept_count(self) -> int:
        """Number of abstracted concepts."""
        return len(self._concepts)

    def clear(self) -> None:
        """Clear all stored data."""
        self._store.clear()
        self._concepts.clear()
        self._connections.clear()

    # -- Internal ----------------------------------------------------------------

    _STOP_WORDS: Set[str] = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "in", "on", "at", "to", "for", "of", "with", "by", "from",
        "and", "or", "but", "not", "if", "so", "as", "it", "its",
    }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text."""
        if not text:
            return []
        words = re.findall(r"[a-zA-Z_]{3,}", text.lower())
        return [w for w in words if w not in self._STOP_WORDS]

    def _find_similar_concept(self, concept: Concept) -> Optional[Concept]:
        """Find an existing concept similar to the given one."""
        new_kw = set(concept.keywords)
        for existing in self._concepts.values():
            overlap = len(new_kw & set(existing.keywords))
            if overlap >= 2:  # At least 2 shared keywords
                return existing
        return None

    def _reinforce_concept(self, existing: Concept, new_concept: Concept) -> None:
        """Reinforce an existing concept with new data."""
        existing.source_memory_ids.extend(new_concept.source_memory_ids)
        existing.keywords = list(set(existing.keywords + new_concept.keywords))
        existing.confidence = min(1.0, existing.confidence + 0.1)
        existing.last_reinforced = time.time()
