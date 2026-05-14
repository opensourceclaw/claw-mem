"""Semantic similarity graph — edges based on text similarity."""

import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SemanticGraph:
    """Semantic similarity graph with weighted edges based on text overlap."""

    def __init__(self):
        self._nodes: Dict[str, Dict] = {}
        self._edges: Dict[str, Dict[str, float]] = defaultdict(dict)

    def add_node(self, memory_id: str, text: str) -> None:
        """Add a node with text content and compute edges to existing nodes."""
        text_norm = self._normalize(text)
        self._nodes[memory_id] = {"text": text_norm}

        for other_id, other in self._nodes.items():
            if other_id == memory_id:
                continue
            sim = self._text_similarity(text_norm, other["text"])
            if sim > 0.3:
                self._edges[memory_id][other_id] = sim
                self._edges[other_id][memory_id] = sim

    def query(self, text: str, top_k: int = 10) -> List[Dict]:
        """Find semantically similar nodes."""
        text_norm = self._normalize(text)
        scores = []
        for node_id, node in self._nodes.items():
            sim = self._text_similarity(text_norm, node["text"])
            scores.append({"id": node_id, "score": sim, "text": node["text"][:200]})
        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:top_k]

    def get_neighbors(self, node_id: str, depth: int = 1) -> List[str]:
        """Get connected node IDs up to depth levels."""
        if node_id not in self._nodes:
            return []
        visited = {node_id}
        current = [node_id]
        for _ in range(depth):
            next_level = []
            for nid in current:
                for neighbor in self._edges.get(nid, {}):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_level.append(neighbor)
            current = next_level
            if not current:
                break
        return [n for n in visited if n != node_id]

    def _normalize(self, text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff\s]", "", str(text).lower())

    def _text_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def count(self) -> int:
        return len(self._nodes)
