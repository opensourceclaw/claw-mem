"""Entity association graph — edges based on shared entities."""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class EntityGraph:
    """Entity association graph linking memories through shared entities."""

    def __init__(self):
        self._nodes: Dict[str, Dict] = {}
        self._entity_index: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, memory_id: str, entities: List[str]) -> None:
        """Add a node with extracted entities."""
        self._nodes[memory_id] = {"entities": list(entities)}
        for entity in entities:
            self._entity_index[entity.lower()].add(memory_id)

    def get_by_entity(self, entity: str) -> List[str]:
        """Get all memories containing a specific entity."""
        return list(self._entity_index.get(entity.lower(), set()))

    def get_shared_entities(self, id1: str, id2: str) -> List[str]:
        """Find entities shared by two memories."""
        e1 = set(self._nodes.get(id1, {}).get("entities", []))
        e2 = set(self._nodes.get(id2, {}).get("entities", []))
        return list(e1 & e2)

    def extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text using simple heuristics."""
        entities = []
        # Capitalized words (proper nouns)
        for word in re.findall(r"[A-Z][a-z]+", str(text)):
            if len(word) > 2:
                entities.append(word)
        # Email/URL patterns
        entities.extend(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", str(text)))
        entities.extend(re.findall(r"https?://[\w./-]+", str(text)))
        return list(set(entities))

    def get_related(self, memory_id: str, limit: int = 10) -> List[Dict]:
        """Get memories sharing entities with the given memory."""
        entities = self._nodes.get(memory_id, {}).get("entities", [])
        related = defaultdict(int)
        for entity in entities:
            for related_id in self._entity_index.get(entity.lower(), set()):
                if related_id != memory_id:
                    related[related_id] += 1
        sorted_related = sorted(related.items(), key=lambda x: x[1], reverse=True)
        return [{"id": rid, "shared_count": cnt} for rid, cnt in sorted_related[:limit]]

    def count(self) -> int:
        return len(self._nodes)
