"""Causal dependency graph — edges based on cause-effect relations."""

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class CausalGraph:
    """Causal dependency graph tracking cause-effect relationships."""

    def __init__(self):
        self._nodes: Dict[str, Dict] = {}
        self._causes_of: Dict[str, Set[str]] = defaultdict(set)  # node → its causes
        self._effects_of: Dict[str, Set[str]] = defaultdict(set)  # node → its effects

    def add_node(self, memory_id: str) -> None:
        """Add a node to the causal graph."""
        if memory_id not in self._nodes:
            self._nodes[memory_id] = {}
            self._causes_of[memory_id] = set()
            self._effects_of[memory_id] = set()

    def add_causal_link(self, cause: str, effect: str) -> None:
        """Add a causal relation: cause → effect."""
        if cause not in self._nodes:
            self.add_node(cause)
        if effect not in self._nodes:
            self.add_node(effect)
        self._causes_of[effect].add(cause)
        self._effects_of[cause].add(effect)

    def get_causes(self, node_id: str) -> List[str]:
        """Get direct causes of a node."""
        return list(self._causes_of.get(node_id, set()))

    def get_effects(self, node_id: str) -> List[str]:
        """Get direct effects of a node."""
        return list(self._effects_of.get(node_id, set()))

    def get_causal_chain(self, node_id: str, upstream: bool = True) -> List[str]:
        """Traverse causal chain (upstream=causes, downstream=effects)."""
        result = []
        visited = {node_id}
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            neighbors = self.get_causes(current) if upstream else self.get_effects(current)
            for n in neighbors:
                if n not in visited:
                    visited.add(n)
                    result.append(n)
                    queue.append(n)
        return result

    def count(self) -> int:
        return len(self._nodes)
