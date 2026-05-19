# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SpreadingActivation - Graph-based activation spreading (v2.15.0).

From seed nodes, BFS along four-orthogonal graph edges, simulating
neuroscience-inspired spreading activation with decay and pruning.
"""

from collections import deque
from typing import Dict, List, Set, Tuple

from claw_mem.graph.multi_graph import MultiGraphMemory

# Default subgraph expansion weights
DEFAULT_EDGE_WEIGHTS: Dict[str, float] = {
    "semantic": 0.8,
    "temporal": 0.6,
    "causal": 0.5,
    "entity": 0.3,
}

# Intent → allowed subgraph types
INTENT_EDGE_MAP: Dict[str, List[str]] = {
    "temporal": ["temporal"],
    "causal": ["causal"],
    "semantic": ["semantic"],
    "entity": ["entity"],
    "general": ["semantic", "temporal", "causal", "entity"],
}


def spreading_bfs(
    seed_scores: Dict[str, float],
    graph: MultiGraphMemory,
    max_depth: int = 2,
    decay_factor: float = 0.5,
    threshold: float = 0.1,
    max_nodes: int = 100,
    edge_type_weights: Dict[str, float] = None,
) -> Dict[str, float]:
    """BFS-based spreading activation.

    Args:
        seed_scores: {node_id: initial_activation_score}.
        graph: MultiGraphMemory with edge data.
        max_depth: Maximum BFS depth (0 = seeds only).
        decay_factor: Per-hop decay multiplier.
        threshold: Minimum activation to continue spreading.
        max_nodes: Maximum total activated nodes.
        edge_type_weights: Per-subgraph expansion weights.

    Returns:
        {node_id: activation_score} including seeds.
    """
    if edge_type_weights is None:
        edge_type_weights = DEFAULT_EDGE_WEIGHTS

    activations: Dict[str, float] = dict(seed_scores)
    queue: deque = deque()
    visited: Set[Tuple[str, int]] = set()

    for nid, score in seed_scores.items():
        queue.append((nid, 0, score))
        visited.add((nid, 0))

    while queue:
        current_id, depth, current_score = queue.popleft()

        if depth >= max_depth:
            continue

        for sg_type in list(graph._graphs.keys()):
            sg = graph._graphs[sg_type]
            et_weight = edge_type_weights.get(sg_type.value, 0.5)

            # Skip edge types with zero weight
            if et_weight <= 0:
                continue

            neighbors = sg.get_edges_from(current_id)
            for neighbor_id, edge_weight in neighbors:
                # Skip expired edges
                if edge_weight < 0.1:
                    continue

                state = (neighbor_id, depth + 1)
                if state in visited:
                    continue
                visited.add(state)

                # Activation formula
                new_activation = (
                    current_score * (decay_factor ** (depth + 1)) * edge_weight * et_weight
                )

                if new_activation < threshold:
                    continue

                if neighbor_id in activations:
                    activations[neighbor_id] = max(activations[neighbor_id], new_activation)
                else:
                    activations[neighbor_id] = new_activation

                if len(activations) >= max_nodes:
                    return activations

                queue.append((neighbor_id, depth + 1, new_activation))

    return activations


class SpreadingActivation:
    """Graph-based activation spreading engine.

    Operates on MultiGraphMemory (v2.14.0), traversing the four
    orthogonal subgraphs from seed nodes with configurable decay
    and pruning.
    """

    def __init__(self, graph: MultiGraphMemory):
        self._graph = graph
        self._max_depth = 2
        self._decay_factor = 0.5
        self._threshold = 0.1
        self._max_nodes = 100
        self._edge_weights = dict(DEFAULT_EDGE_WEIGHTS)

    def configure(
        self,
        max_depth: int = None,
        decay_factor: float = None,
        threshold: float = None,
        max_nodes: int = None,
    ) -> None:
        """Reconfigure runtime parameters."""
        if max_depth is not None:
            self._max_depth = max_depth
        if decay_factor is not None:
            self._decay_factor = decay_factor
        if threshold is not None:
            self._threshold = threshold
        if max_nodes is not None:
            self._max_nodes = max_nodes

    def activate(self, seed_nodes: Dict[str, float], intent: str = "general") -> Dict[str, float]:
        """Run spreading activation from seed nodes.

        Args:
            seed_nodes: {node_id: initial_activation}.
            intent: Query intent (filters edge types).

        Returns:
            {node_id: activation_score}.
        """
        filtered = self._filter_weights(intent)
        return spreading_bfs(
            seed_scores=seed_nodes,
            graph=self._graph,
            max_depth=self._max_depth,
            decay_factor=self._decay_factor,
            threshold=self._threshold,
            max_nodes=self._max_nodes,
            edge_type_weights=filtered,
        )

    def _filter_weights(self, intent: str) -> Dict[str, float]:
        allowed = INTENT_EDGE_MAP.get(intent, INTENT_EDGE_MAP["general"])
        return {k: v for k, v in self._edge_weights.items() if k in allowed}

    def get_stats(self) -> dict:
        return {
            "max_depth": self._max_depth,
            "decay_factor": self._decay_factor,
            "threshold": self._threshold,
            "max_nodes": self._max_nodes,
            "edge_weights": self._edge_weights,
        }
