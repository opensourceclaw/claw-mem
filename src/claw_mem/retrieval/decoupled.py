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
DecoupledRetriever - Unified retrieval pipeline (v2.15.0).

Pipeline: Query → EngramIndex.lookup() → SpreadingActivation.activate()
         → Multi-Factor Ranking → Top-K Results

Target: search() < 5ms.
"""

import time
from typing import Dict, List, Optional

from claw_mem.graph.multi_graph import MultiGraphMemory


class DecoupledRetriever:
    """Unified retrieval pipeline.

    Combines EngramIndex (O(1) lookup) + SpreadingActivation (graph
    expansion) + multi-factor ranking into a single search interface.
    """

    def __init__(self, engram, spreader, graph: Optional[MultiGraphMemory] = None):
        self._engram = engram
        self._spreader = spreader
        self._graph = graph

    def search(self, query: str, top_k: int = 10,
               intent: str = 'general') -> List[Dict]:
        """Execute full retrieval pipeline.

        Args:
            query: User query string.
            top_k: Number of results.
            intent: Search intent (temporal/causal/semantic/entity/general).

        Returns:
            [{"id": str, "content": str, "score": float, "type": str}, ...]
        """
        # Phase 1: Engram O(1) lookup → seed nodes
        seed_results = self._engram.lookup(query, top_k=min(top_k * 2, 20))
        if not seed_results:
            return []

        seed_scores = {mid: score for mid, score in seed_results}

        # Phase 2: Spreading activation
        activations: Dict[str, float] = {}
        if self._graph is not None and self._spreader is not None:
            activations = self._spreader.activate(seed_scores, intent=intent)
        else:
            activations = dict(seed_scores)

        # Phase 3: Multi-factor ranking
        return self._rank(activations, top_k)

    def _rank(self, activations: Dict[str, float],
              top_k: int) -> List[Dict]:
        """Multi-factor ranking.

        Factors:
          1. Activation score (50%)
          2. Temporal freshness (30%)
          3. Content type weight (20%)
        """
        now = time.time()
        scored = []

        for node_id, activation in activations.items():
            content = ''
            node_type_str = ''
            created_at = now

            if self._graph:
                node = self._graph.get_node(node_id)
                if node:
                    content = getattr(node, 'content', '')
                    node_type_str = str(getattr(node, 'type', ''))
                    created_at = getattr(node, 'created_at', now)
                    if hasattr(created_at, 'timestamp'):
                        created_at = created_at.timestamp()
                    elif not isinstance(created_at, (int, float)):
                        created_at = now

            # Freshness
            age_days = max(0, (now - created_at) / 86400.0)
            freshness = max(0.1, 1.0 - age_days / 90.0)

            # Type weight
            type_weights = {
                'NodeType.FACT': 1.0, 'fact': 1.0,
                'NodeType.EPISODE': 0.8, 'episode': 0.8,
                'NodeType.REFLECTION': 0.6, 'reflection': 0.6,
                'NodeType.CONCEPT': 0.5, 'concept': 0.5,
            }
            type_w = type_weights.get(node_type_str, 0.5)

            score = activation * 0.5 + freshness * 0.3 + type_w * 0.2

            scored.append({
                "id": node_id,
                "content": content[:500] if content else f"[node:{node_id}]",
                "score": round(score, 4),
                "type": node_type_str,
                "source": "engram_spreading",
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
