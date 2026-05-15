"""MultiGraphMemory — MAGMA: Multi-Angle Graph Memory Architecture."""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from claw_mem.graph_memory.semantic_graph import SemanticGraph
from claw_mem.graph_memory.temporal_graph import TemporalGraph
from claw_mem.graph_memory.causal_graph import CausalGraph
from claw_mem.graph_memory.entity_graph import EntityGraph

logger = logging.getLogger(__name__)


class MultiGraphMemory:
    """Four-angle orthogonal graph memory (MAGMA architecture)."""

    def __init__(self):
        self.semantic = SemanticGraph()
        self.temporal = TemporalGraph()
        self.causal = CausalGraph()
        self.entity = EntityGraph()

    def add_memory(self, memory: Dict) -> str:
        """Add a memory to all four graph angles.

        Expected keys: text, timestamp (optional), entities (optional),
                       cause_of (optional), effect_of (optional)
        """
        mid = memory.get("id", str(uuid.uuid4()))
        text = memory.get("text", memory.get("content", ""))
        ts = memory.get("timestamp", time.time())
        entities = memory.get("entities", [])
        cause_of = memory.get("cause_of")
        effect_of = memory.get("effect_of")

        if not entities:
            entities = self.entity.extract_entities(text)

        self.semantic.add_node(mid, text)
        self.temporal.add_node(mid, ts)
        self.causal.add_node(mid)
        self.entity.add_node(mid, entities)

        if cause_of:
            self.causal.add_causal_link(cause_of, mid)
        if effect_of:
            self.causal.add_causal_link(mid, effect_of)

        logger.debug("Memory %s added to all 4 graphs", mid[:8])
        return mid

    def query(
        self,
        query: str,
        top_k: int = 10,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict]:
        """Cross-graph fused query."""
        if weights is None:
            weights = {"semantic": 0.5, "temporal": 0.3, "entity": 0.2}

        result_scores: Dict[str, float] = {}

        # Semantic
        for r in self.semantic.query(query, top_k):
            result_scores[r["id"]] = (
                result_scores.get(r["id"], 0) + r["score"] * weights["semantic"]
            )

        # Temporal (recent)
        for nid in self.temporal.get_recent(top_k):
            result_scores[nid] = result_scores.get(nid, 0) + 0.3 * weights["temporal"]

        # Entity
        entities = self.entity.extract_entities(query)
        for entity in entities:
            for nid in self.entity.get_by_entity(entity):
                result_scores[nid] = result_scores.get(nid, 0) + 0.5 * weights["entity"]

        sorted_results = sorted(result_scores.items(), key=lambda x: x[1], reverse=True)
        return [{"id": rid, "score": round(s, 4)} for rid, s in sorted_results[:top_k]]

    def remove_memory(self, memory_id: str) -> None:
        """Remove a memory from all graphs (best effort)."""
        for graph in [self.semantic, self.temporal, self.causal, self.entity]:
            if hasattr(graph, "_nodes"):
                graph._nodes.pop(memory_id, None)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "semantic_nodes": self.semantic.count(),
            "temporal_nodes": self.temporal.count(),
            "causal_nodes": self.causal.count(),
            "entity_nodes": self.entity.count(),
        }
