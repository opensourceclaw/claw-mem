"""Spreading Activation — multi-graph diffusion retrieval for claw-mem v2.15.0."""

import logging
import math
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set

from claw_mem.graph_memory import (
    MultiGraphMemory,
    SemanticGraph,
    TemporalGraph,
    EntityGraph,
)

logger = logging.getLogger(__name__)


class SpreadingActivation:
    """Multi-graph diffusion activation retrieval.

    Inspired by neuroscientific models of memory retrieval:
    1. Activate seed nodes from query
    2. Spread activation through graph edges
    3. Weight and aggregate results across graphs
    4. Return top-k activated nodes
    """

    def __init__(self, graphs: Optional[MultiGraphMemory] = None):
        self.graphs = graphs or MultiGraphMemory()
        self._activation_threshold: float = 0.1
        self._decay_factor: float = 0.5

    def search(self, query: str, top_k: int = 10, depth: int = 2) -> List[Dict]:
        """Execute spreading activation search across all graphs.

        Args:
            query: Search query
            top_k: Maximum results
            depth: Activation spread depth (number of graph hops)

        Returns:
            List of activated memory nodes with scores
        """
        # Step 1: Seed activation from query
        activations: Dict[str, float] = self._seed_activation(query)

        # Step 2: Spread through graph edges
        for _ in range(depth):
            activations = self._spread(activations)

        # Step 3: Normalize and sort
        if not activations:
            return []

        max_act = max(activations.values()) or 1.0
        results = [
            {"id": nid, "activation": round(act / max_act, 4)}
            for nid, act in sorted(activations.items(), key=lambda x: x[1], reverse=True)
            if act / max_act >= self._activation_threshold
        ]
        return results[:top_k]

    def _seed_activation(self, query: str) -> Dict[str, float]:
        """Initialize activation from semantic and entity matches."""
        active: Dict[str, float] = {}

        # Semantic seed
        for r in self.graphs.semantic.query(query, top_k=10):
            active[r["id"]] = active.get(r["id"], 0) + r["score"] * 0.6

        # Entity seed
        entities = self.graphs.entity.extract_entities(query)
        for entity in entities:
            for nid in self.graphs.entity.get_by_entity(entity):
                active[nid] = active.get(nid, 0) + 0.4

        return active

    def _spread(self, activations: Dict[str, float]) -> Dict[str, float]:
        """One iteration of activation spread through graph edges."""
        new_act = defaultdict(float)

        for node_id, energy in activations.items():
            # Spread through semantic neighbors
            neighbors = self.graphs.semantic.get_neighbors(node_id, depth=1)
            spread = energy * self._decay_factor / max(1, len(neighbors))
            for nb in neighbors:
                new_act[nb] += spread

            # Spread through causal effects
            effects = self.graphs.causal.get_effects(node_id)
            for eff in effects:
                new_act[eff] += energy * self._decay_factor * 0.7

        # Merge with existing
        for nid, act in new_act.items():
            activations[nid] = activations.get(nid, 0) + act

        return activations

    def set_threshold(self, threshold: float) -> None:
        self._activation_threshold = threshold
