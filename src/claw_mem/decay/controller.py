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
DecayController - Forgetting controller for graph edge decay.

Manages the lifelong weight calculation, edge classification, and
cleanup of expired edges in the MultiGraphMemory.
"""

import time
import threading
from typing import Dict, List, Tuple

from claw_mem.graph.multi_graph import MultiGraphMemory, SubGraphType
from claw_mem.decay.functions import (
    calculate_weight,
    DecayConfig,
)


class DecayController:
    """Forgetting controller for edge-level decay.

    Responsibilities:
      - Compute decayed edge weights.
      - Classify edges into strength tiers.
      - Decide which edges should be removed.
      - Execute cleanup on the associated MultiGraphMemory.
    """

    def __init__(self, graph: MultiGraphMemory,
                 config: DecayConfig = None):
        self._graph = graph
        self._config = config or DecayConfig.default()
        self._lock = threading.Lock()
        self._last_decay_time: float = 0.0
        self._decay_count: int = 0

    # ── Weight computation ─────────────────────────────────────────

    def calculate_single_weight(self, initial: float, days: float,
                                category: str) -> float:
        """Calculate a single edge weight after decay."""
        return calculate_weight(initial, days, category)

    def get_decay_weight(self, source: str, target: str,
                         edge_type: str, created_at: float) -> float:
        """Compute decayed weight for a specific edge."""
        current_weight = 1.0
        for g in self._graph._graphs.values():
            w = g.edge_weights.get((source, target))
            if w is not None:
                current_weight = w
                break
        days_elapsed = (time.time() - created_at) / 86400.0
        category = self._edge_type_to_category(edge_type)
        return calculate_weight(current_weight, days_elapsed, category)

    def _edge_type_to_category(self, edge_type: str) -> str:
        mapping = {
            "next": "temporal",
            "derived_from": "causal",
            "synthesized_from": "causal",
            "related_to": "semantic",
            "has_concept": "entity",
        }
        return mapping.get(edge_type, "semantic")

    def compute_all_decays(self) -> Dict[Tuple[str, str], float]:
        """Compute decay weights for all edges.

        Returns:
            {(source, target): new_weight} for edges that decayed.
        """
        updates = {}
        now = time.time()

        with self._lock:
            for sg_type, subgraph in self._graph._graphs.items():
                category = {
                    SubGraphType.TEMPORAL: "temporal",
                    SubGraphType.CAUSAL: "causal",
                    SubGraphType.SEMANTIC: "semantic",
                    SubGraphType.ENTITY: "entity",
                }.get(sg_type, "semantic")

                for (s, t), weight in subgraph.edge_weights.items():
                    node = self._graph.get_node(s)
                    if node is not None and hasattr(node, 'created_at') and node.created_at:
                        created_at = node.created_at
                        if not isinstance(created_at, (int, float)):
                            created_at = created_at.timestamp()
                    else:
                        created_at = now
                    days_elapsed = (now - created_at) / 86400.0
                    new_weight = calculate_weight(
                        weight, days_elapsed, category
                    )
                    if new_weight < weight:
                        updates[(s, t)] = max(0.0, min(1.0, new_weight))

        return updates

    # ── Edge classification ───────────────────────────────────────

    def classify_edges(self) -> Dict[str, List[Tuple[str, str, float]]]:
        """Classify all edges by strength tier.

        Returns:
            {"strong": [...], "medium": [...], "weak": [...], "expired": [...]}
        """
        classified = {"strong": [], "medium": [], "weak": [], "expired": []}

        for sg_type, subgraph in self._graph._graphs.items():
            for (s, t), weight in subgraph.edge_weights.items():
                entry = (s, t, weight)
                if weight > self._config.strong_threshold:
                    classified["strong"].append(entry)
                elif weight > self._config.archive_threshold:
                    classified["medium"].append(entry)
                elif weight > self._config.expire_threshold:
                    classified["weak"].append(entry)
                else:
                    classified["expired"].append(entry)

        return classified

    # ── Cleanup ───────────────────────────────────────────────────

    def should_remove_edge(self, source: str, target: str,
                           weight: float) -> bool:
        """Decide whether an edge should be removed."""
        if weight <= self._config.purge_threshold:
            return True
        if weight <= self._config.expire_threshold:
            if self._config.protect_critical:
                node = self._graph.get_node(source)
                if node and getattr(
                    node, 'metadata', {}
                ).get('critical', False):
                    return False
            return True
        return False

    def cleanup_expired(self) -> List[Tuple[str, str]]:
        """Remove expired edges from the graph.

        Returns:
            List of removed (source, target) pairs.
        """
        removed: List[Tuple[str, str]] = []
        with self._lock:
            for sg_type in list(SubGraphType):
                subgraph = self._graph._graphs[sg_type]
                expired = [
                    (s, t) for (s, t), w in subgraph.edge_weights.items()
                    if self.should_remove_edge(s, t, w)
                ]
                removed.extend(expired)

            if removed:
                for (s, t) in removed:
                    for g in self._graph._graphs.values():
                        if g.has_edge(s, t):
                            del g.edge_weights[(s, t)]
                            g.adjacency[s] = [
                                (n, w) for n, w in g.adjacency.get(s, [])
                                if n != t
                            ]
                            g.reverse_adjacency[t] = [
                                (n, w) for n, w in g.reverse_adjacency.get(t, [])
                                if n != s
                            ]
                for g in self._graph._graphs.values():
                    g.edge_count = len(g.edge_weights)

        self._decay_count += 1
        self._last_decay_time = time.time()
        return removed

    # ── Stats ─────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        classified = self.classify_edges()
        total = sum(len(v) for v in classified.values())
        return {
            "total_edges": total,
            "strong_edges": len(classified["strong"]),
            "medium_edges": len(classified["medium"]),
            "weak_edges": len(classified["weak"]),
            "expired_edges": len(classified["expired"]),
            "decay_count": self._decay_count,
            "last_decay_time": self._last_decay_time,
            "config": {
                "purge_threshold": self._config.purge_threshold,
                "expire_threshold": self._config.expire_threshold,
                "decay_interval_hours": self._config.decay_interval_hours,
            },
        }
