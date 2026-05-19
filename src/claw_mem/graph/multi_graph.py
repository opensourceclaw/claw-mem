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
MultiGraphMemory - Four orthogonal subgraph index layer.

Organizes memory nodes into four independent graph views:
  - SEMANTIC: Similarity-based relationships
  - TEMPORAL: Time-based event sequences
  - CAUSAL: Cause-effect derivations
  - ENTITY: Entity co-occurrence

Built on top of existing graph module's Node/Edge primitives.
"""

from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Dict, List, Optional, Set, Tuple

from claw_mem.graph.edges import EdgeType
from claw_mem.graph.nodes import Node, NodeType, create_node


class SubGraphType(Enum):
    """Four orthogonal subgraph dimensions."""

    SEMANTIC = "semantic"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    ENTITY = "entity"


@dataclass
class GraphEdge:
    """Lightweight edge record for subgraph internal indexing."""

    source_id: str
    target_id: str
    weight: float
    edge_type: str
    created_at: float

    def to_dict(self) -> dict:
        return {
            "s": self.source_id,
            "t": self.target_id,
            "w": round(self.weight, 4),
            "e": self.edge_type,
            "c": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GraphEdge":
        return cls(
            source_id=d["s"],
            target_id=d["t"],
            weight=d.get("w", 1.0),
            edge_type=d.get("e", ""),
            created_at=d.get("c", 0.0),
        )


@dataclass
class SubGraph:
    """A single subgraph implemented as adjacency list + reverse adjacency.

    Supports both directed and undirected edges:
      - adjacency: forward lookup (node_id → [(neighbor_id, weight), ...])
      - reverse_adjacency: backward lookup (for directed edges)
      - edge_weights: O(1) weight/existence check via (source, target) key
    """

    name: SubGraphType
    adjacency: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)
    reverse_adjacency: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)
    edge_weights: Dict[Tuple[str, str], float] = field(default_factory=dict)
    nodes: Set[str] = field(default_factory=set)
    edge_count: int = 0

    def add_node(self, node_id: str) -> None:
        """Register a node into this subgraph (idempotent)."""
        if node_id not in self.nodes:
            self.nodes.add(node_id)
            self.adjacency.setdefault(node_id, [])
            self.reverse_adjacency.setdefault(node_id, [])

    def add_edge(
        self, source: str, target: str, weight: float = 1.0, directed: bool = True
    ) -> None:
        """Add an edge to this subgraph.

        Args:
            source: Source node ID.
            target: Target node ID.
            weight: Edge weight (0.0 ~ 1.0, default 1.0).
            directed: If True, add reverse adjacency entry.
        """
        self.add_node(source)
        self.add_node(target)
        self.adjacency[source].append((target, weight))
        if directed:
            self.reverse_adjacency[target].append((source, weight))
        else:
            self.adjacency[target].append((source, weight))
            self.edge_weights[(target, source)] = weight  # bidirectional lookup
        self.edge_weights[(source, target)] = weight
        self.edge_count += 1

    def get_neighbors(self, node_id: str, max_depth: int = 1) -> Dict[str, float]:
        """BFS traversal to find neighbors up to max_depth.

        Args:
            node_id: Starting node.
            max_depth: Maximum traversal depth (1 = direct neighbors only).

        Returns:
            {neighbor_id: accumulated_path_weight}
        """
        if node_id not in self.nodes:
            return {}

        visited: Dict[str, float] = {}
        queue: List[Tuple[str, float]] = [(node_id, 1.0)]

        for _ in range(max_depth + 1):
            if not queue:
                break
            next_queue: List[Tuple[str, float]] = []
            for current, path_weight in queue:
                for neighbor, weight in self.adjacency.get(current, []):
                    if neighbor == node_id:
                        continue
                    new_weight = path_weight * weight
                    if neighbor not in visited or new_weight > visited[neighbor]:
                        visited[neighbor] = new_weight
                        next_queue.append((neighbor, new_weight))
            queue = next_queue

        return visited

    def get_edges_from(self, node_id: str) -> List[Tuple[str, float]]:
        """Get all outgoing edges from a node."""
        return self.adjacency.get(node_id, [])

    def get_edges_to(self, node_id: str) -> List[Tuple[str, float]]:
        """Get all incoming edges to a node."""
        return self.reverse_adjacency.get(node_id, [])

    def has_edge(self, source: str, target: str) -> bool:
        """Check if an edge exists in O(1)."""
        return (source, target) in self.edge_weights

    def update_weight(self, source: str, target: str, weight: float) -> bool:
        """Update edge weight. Returns True if edge existed."""
        key = (source, target)
        if key in self.edge_weights:
            self.edge_weights[key] = weight
            # Update in adjacency lists too
            for i, (n, _) in enumerate(self.adjacency.get(source, [])):
                if n == target:
                    self.adjacency[source][i] = (n, weight)
                    break
            for i, (n, _) in enumerate(self.reverse_adjacency.get(target, [])):
                if n == source:
                    self.reverse_adjacency[target][i] = (n, weight)
                    break
            return True
        return False

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        edges = []
        for (s, t), w in self.edge_weights.items():
            edges.append(
                GraphEdge(
                    source_id=s,
                    target_id=t,
                    weight=w,
                    edge_type=self.name.value,
                    created_at=0.0,
                ).to_dict()
            )
        return {
            "name": self.name.value,
            "edge_count": self.edge_count,
            "node_count": len(self.nodes),
            "edges": edges,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SubGraph":
        """Deserialize from dictionary."""
        g = cls(name=SubGraphType(d["name"]))
        for e in d.get("edges", []):
            edge = GraphEdge.from_dict(e)
            directed = g.name != SubGraphType.SEMANTIC
            g.add_edge(edge.source_id, edge.target_id, edge.weight, directed=directed)
        return g

    @property
    def memory_estimate(self) -> int:
        """Estimated memory footprint in bytes."""
        return len(self.nodes) * 100 + self.edge_count * 80


# ── Edge type → Subgraph routing ──────────────────────────────────────

EDGE_TO_SUBGRAPH: Dict[EdgeType, SubGraphType] = {
    EdgeType.NEXT: SubGraphType.TEMPORAL,
    EdgeType.DERIVED_FROM: SubGraphType.CAUSAL,
    EdgeType.SYNTHESIZED_FROM: SubGraphType.CAUSAL,
    EdgeType.RELATED_TO: SubGraphType.SEMANTIC,
    EdgeType.HAS_CONCEPT: SubGraphType.ENTITY,
}

# Expansion weights for multi-graph search
SUBGRAPH_EXPANSION_WEIGHT: Dict[SubGraphType, float] = {
    SubGraphType.SEMANTIC: 0.8,
    SubGraphType.TEMPORAL: 0.6,
    SubGraphType.CAUSAL: 0.5,
    SubGraphType.ENTITY: 0.3,
}


class MultiGraphMemory:
    """Four orthogonal subgraph index layer.

    Manages four independent graph views over the same set of memory nodes.
    A single pair of nodes can have edges in multiple subgraphs simultaneously.

    Thread-safe: all public methods acquire the internal lock.
    """

    def __init__(self):
        self._graphs: Dict[SubGraphType, SubGraph] = {
            SubGraphType.SEMANTIC: SubGraph(SubGraphType.SEMANTIC),
            SubGraphType.TEMPORAL: SubGraph(SubGraphType.TEMPORAL),
            SubGraphType.CAUSAL: SubGraph(SubGraphType.CAUSAL),
            SubGraphType.ENTITY: SubGraph(SubGraphType.ENTITY),
        }
        self._node_index: Dict[str, Node] = {}
        self._lock = Lock()

    # ── Node management ───────────────────────────────────────────────

    def add_node(self, memory_id: str, content: str, node_type: NodeType, **metadata) -> None:
        """Register a memory node in the graph (idempotent).

        Args:
            memory_id: Unique memory identifier.
            content: Memory text content.
            node_type: Node type (EPISODE / FACT / REFLECTION / CONCEPT).
            **metadata: Extra metadata passed to node constructor.
        """
        with self._lock:
            if memory_id in self._node_index:
                return
            node = create_node(node_type, content, id=memory_id, **metadata)
            self._node_index[memory_id] = node
            for g in self._graphs.values():
                g.add_node(memory_id)

    def get_node(self, memory_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self._node_index.get(memory_id)

    def node_count(self) -> int:
        """Total number of registered nodes."""
        with self._lock:
            return len(self._node_index)

    # ── Edge management (with auto-routing) ───────────────────────────

    def add_edge(
        self, source_id: str, target_id: str, edge_type: EdgeType, weight: float = 1.0
    ) -> None:
        """Add an edge, automatically routed to the correct subgraph.

        Mapping:
            NEXT              → TEMPORAL
            DERIVED_FROM      → CAUSAL
            SYNTHESIZED_FROM  → CAUSAL
            RELATED_TO        → SEMANTIC
            HAS_CONCEPT       → ENTITY

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            edge_type: Type of edge.
            weight: Initial weight (default 1.0).
        """
        subgraph = EDGE_TO_SUBGRAPH.get(edge_type)
        if subgraph is None:
            raise ValueError(f"Unknown edge type: {edge_type}")

        directed = edge_type != EdgeType.RELATED_TO
        with self._lock:
            self._graphs[subgraph].add_edge(source_id, target_id, weight, directed=directed)

    def has_edge(self, source_id: str, target_id: str) -> bool:
        """Check if any edge exists between two nodes (in any subgraph)."""
        with self._lock:
            for g in self._graphs.values():
                if g.has_edge(source_id, target_id):
                    return True
        return False

    # ── Retrieval ─────────────────────────────────────────────────────

    def get_related(self, memory_id: str, subgraph: SubGraphType, limit: int = 10) -> List[str]:
        """Get related node IDs from a specific subgraph.

        Args:
            memory_id: Source node ID.
            subgraph: Target subgraph.
            limit: Maximum number of results.

        Returns:
            Related node IDs ordered by descending weight.
        """
        with self._lock:
            neighbors = self._graphs[subgraph].get_neighbors(memory_id)
        sorted_n = sorted(neighbors.items(), key=lambda x: x[1], reverse=True)
        return [nid for nid, _ in sorted_n[:limit]]

    def get_expanded_nodes(
        self,
        node_ids: List[str],
        subgraphs: Optional[List[SubGraphType]] = None,
        max_depth: int = 1,
        max_expansion: int = 50,
    ) -> Dict[str, float]:
        """Expand from seed nodes through specified subgraphs.

        Args:
            node_ids: Seed node IDs.
            subgraphs: Subgraphs to traverse (default: all).
            max_depth: Maximum BFS depth per subgraph.
            max_expansion: Maximum number of expanded nodes to return.

        Returns:
            {node_id: aggregated_weight} sorted by weight descending.
        """
        if subgraphs is None:
            subgraphs = list(SubGraphType)

        all_nodes: Dict[str, float] = {}
        for nid in node_ids:
            all_nodes[nid] = 1.0

        with self._lock:
            for sg in subgraphs:
                for seed in node_ids:
                    neighbors = self._graphs[sg].get_neighbors(seed, max_depth=max_depth)
                    for nid, weight in neighbors.items():
                        if nid not in all_nodes:
                            all_nodes[nid] = weight
                        else:
                            all_nodes[nid] += weight

        expanded = sorted(all_nodes.items(), key=lambda x: x[1], reverse=True)
        return dict(expanded[:max_expansion])

    def multi_graph_search(self, sem_nodes: List[str], k: int = 10) -> List[Tuple[str, float]]:
        """Multi-subgraph joint retrieval.

        Strategy:
          1. Seed nodes from semantic search get weight 1.0.
          2. Expand through all four subgraphs with configured weights.
          3. Aggregate and rank by combined score.

        Args:
            sem_nodes: Seed node IDs from semantic retrieval.
            k: Number of results to return.

        Returns:
            [(node_id, combined_score), ...] ordered by descending score.
        """
        candidates: Dict[str, float] = {}

        # Phase 1: seed nodes
        for nid in sem_nodes:
            candidates[nid] = 1.0

        # Phase 2: multi-subgraph expansion
        with self._lock:
            for sg, ew in SUBGRAPH_EXPANSION_WEIGHT.items():
                neighbors: Dict[str, float] = {}
                for seed in sem_nodes:
                    more = self._graphs[sg].get_neighbors(seed, max_depth=1)
                    for nid, w in more.items():
                        neighbors[nid] = max(neighbors.get(nid, 0), w)

                for nid, w in neighbors.items():
                    score = w * ew
                    if nid not in candidates:
                        candidates[nid] = score
                    else:
                        candidates[nid] += score

        sorted_c = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        return sorted_c[:k]

    # ── Decay integration ─────────────────────────────────────────────

    def apply_decay(self, edge_weights: Dict[Tuple[str, str], float]) -> int:
        """Batch update edge weights after decay calculation.

        Args:
            edge_weights: {(source_id, target_id): new_weight}.

        Returns:
            Number of edges successfully updated.
        """
        updated = 0
        with self._lock:
            for (s, t), weight in edge_weights.items():
                for g in self._graphs.values():
                    if g.update_weight(s, t, weight):
                        updated += 1
        return updated

    def remove_expired_edges(self, threshold: float = 0.05) -> int:
        """Remove edges with weight below threshold.

        Args:
            threshold: Minimum weight to keep (default 0.05).

        Returns:
            Number of edges removed.
        """
        removed = 0
        with self._lock:
            for g in self._graphs.values():
                expired = [(s, t) for (s, t), w in g.edge_weights.items() if w < threshold]
                for s, t in expired:
                    del g.edge_weights[(s, t)]
                    g.adjacency[s] = [(n, w) for n, w in g.adjacency[s] if n != t]
                    g.reverse_adjacency[t] = [(n, w) for n, w in g.reverse_adjacency[t] if n != s]
                    removed += 1
                g.edge_count = len(g.edge_weights)
        return removed

    # ── Statistics ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get per-subgraph statistics."""
        with self._lock:
            return {
                "total_nodes": len(self._node_index),
                "subgraphs": {
                    g.name.value: {
                        "nodes": len(g.nodes),
                        "edges": g.edge_count,
                        "memory_bytes": g.memory_estimate,
                    }
                    for g in self._graphs.values()
                },
            }

    # ── Persistence ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dictionary."""
        with self._lock:
            return {
                "nodes": {nid: node.to_dict() for nid, node in self._node_index.items()},
                "subgraphs": {g.name.value: g.to_dict() for g in self._graphs.values()},
            }

    @classmethod
    def from_dict(cls, d: dict) -> "MultiGraphMemory":
        """Deserialize from dictionary."""
        mg = cls()
        for nid, nd in d.get("nodes", {}).items():
            mg._node_index[nid] = Node.from_dict(nd)
        for name, sd in d.get("subgraphs", {}).items():
            sg_type = SubGraphType(name)
            mg._graphs[sg_type] = SubGraph.from_dict(sd)
        return mg
