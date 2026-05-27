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
Graph Reasoner (v4.10.0)

Multi-hop reasoning over knowledge triplets. Maintains an independent
adjacency list compatible with ConceptMediatedGraph nodes but not
tightly coupled.

Supports:
- Path finding (BFS shortest + DFS all paths, cycle-aware)
- Related node discovery
- Node importance scoring (frequency centrality + connectivity)
"""

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class PathResult:
    """Result of a path-finding query between two nodes.

    Attributes:
        path: Ordered list of (node, predicate, node) tuples.
        length: Number of edges in the path.
        confidence: Aggregate confidence along the path.
    """
    path: List[Tuple[str, str, str]]
    length: int
    confidence: float = 1.0

    def __repr__(self) -> str:
        if not self.path:
            return "PathResult(empty)"
        steps = " → ".join(f"{s} -{p}-> {o}" for s, p, o in self.path)
        return f"PathResult({steps}, len={self.length}, c={self.confidence:.2f})"


class GraphReasoner:
    """Multi-hop reasoner over a knowledge graph of (S, P, O) triplets.

    Builds a directed adjacency list. Compatible with nodes from
    ConceptMediatedGraph via add_triplet() bridge.

    Usage:
        gr = GraphReasoner()
        gr.add_triplet("张三", "负责", "电商项目")
        gr.add_triplet("李四", "是...的上司", "张三")
        paths = gr.find_paths("李四", "电商项目")
        related = gr.find_related("张三")
        importance = gr.node_importance()
    """

    def __init__(self):
        # Adjacency: {node_id -> [(predicate, target_node_id, confidence)]}
        self._graph: Dict[str, List[Tuple[str, str, float]]] = {}
        # Reverse adjacency for in-degree computation
        self._reverse: Dict[str, List[Tuple[str, str, float]]] = {}

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalize a node name to a canonical id."""
        return name.strip().lower()

    # ── Graph Construction ──────────────────────────────────────────────

    def add_triplet(self, subj: str, pred: str, obj: str, confidence: float = 0.8):
        """Add a single triplet edge to the graph.

        Args:
            subj: Subject entity name.
            pred: Predicate / relationship.
            obj: Object entity name.
            confidence: Edge confidence (0.0-1.0).
        """
        s = self._normalize(subj)
        o = self._normalize(obj)
        self._graph.setdefault(s, []).append((pred, o, confidence))
        self._reverse.setdefault(o, []).append((pred, s, confidence))
        # Ensure all nodes appear as keys even if they have no outgoing edges
        self._graph.setdefault(o, [])
        self._reverse.setdefault(s, [])

    def add_triplets(self, triplets: List) -> None:
        """Batch-add triplets from a list of Triplet objects.

        Args:
            triplets: List of Triplet objects with subject, predicate, object,
                      and confidence attributes.
        """
        for t in triplets:
            self.add_triplet(t.subject, t.predicate, t.object, t.confidence)

    # ── Path Finding ────────────────────────────────────────────────────

    def find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 3,
    ) -> List[PathResult]:
        """Find paths from source to target.

        Uses BFS for shortest path first, then DFS for additional paths
        up to max_depth. Avoids cycles.

        Args:
            source: Starting node name.
            target: Target node name.
            max_depth: Maximum path length in edges (default 3).

        Returns:
            List of PathResult ordered by length (shortest first).
        """
        s = self._normalize(source)
        t = self._normalize(target)

        if s not in self._graph or t not in self._graph:
            return []

        results: List[PathResult] = []

        # BFS for shortest path
        shortest = self._bfs_shortest(s, t, max_depth)
        if shortest:
            results.append(shortest)

        # DFS for additional paths (skip the BFS-found path)
        bfs_key = None
        if shortest:
            bfs_key = tuple((h, p, r) for h, p, r in shortest.path)

        dfs_paths = self._dfs_all(s, t, max_depth)
        for path in dfs_paths:
            pk = tuple((h, p, r) for h, p, r in path)
            if pk != bfs_key:
                length = len(path)
                conf = self._path_confidence(path)
                results.append(PathResult(path=path, length=length, confidence=conf))

        return results

    def _bfs_shortest(
        self, source: str, target: str, max_depth: int
    ) -> Optional[PathResult]:
        """BFS to find the shortest path. Returns None if unreachable."""
        queue = deque([(source, [])])
        visited = {source}

        while queue:
            node, path_so_far = queue.popleft()
            if len(path_so_far) >= max_depth:
                continue

            for pred, neighbor, conf in self._graph.get(node, []):
                new_path = path_so_far + [(node, pred, neighbor, conf)]
                if neighbor == target:
                    steps = [(s, p, o) for s, p, o, _c in new_path]
                    total_conf = self._compute_confidence(
                        new_path
                    )
                    return PathResult(
                        path=steps,
                        length=len(steps),
                        confidence=total_conf,
                    )
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))

        return None

    def _dfs_all(
        self, source: str, target: str, max_depth: int
    ) -> List[List[Tuple[str, str, str]]]:
        """DFS to find all paths up to max_depth, avoiding cycles."""
        result = []
        stack = [(source, [], {source})]

        while stack:
            node, path, visited = stack.pop()
            if len(path) >= max_depth:
                continue

            for pred, neighbor, _conf in self._graph.get(node, []):
                if neighbor in visited:
                    continue
                new_path = path + [(node, pred, neighbor)]
                if neighbor == target:
                    result.append(new_path)
                else:
                    new_visited = visited | {neighbor}
                    stack.append((neighbor, new_path, new_visited))

        return result

    def _path_confidence(self, path: List[Tuple[str, str, str]]) -> float:
        """Compute aggregate confidence for a path using edge confidence values."""
        if not path:
            return 0.0
        confs = []
        for s, _p, o in path:
            for _pred, neighbor, c in self._graph.get(s, []):
                if neighbor == o:
                    confs.append(c)
                    break
            else:
                confs.append(0.5)  # fallback if edge not found
        return self._compute_confidence_confs(confs)

    @staticmethod
    def _compute_confidence(
        path_with_conf: List[Tuple[str, str, str, float]]
    ) -> float:
        """Product of edge confidences, with length penalty."""
        if not path_with_conf:
            return 0.0
        product = 1.0
        for _, _, _, c in path_with_conf:
            product *= c
        return round(product, 4)

    @staticmethod
    def _compute_confidence_confs(confs: List[float]) -> float:
        """Product of confidence values with length penalty."""
        if not confs:
            return 0.0
        product = 1.0
        for c in confs:
            product *= c
        return round(product, 4)

    # ── Related Nodes ───────────────────────────────────────────────────

    def find_related(self, source: str, max_depth: int = 2) -> List[str]:
        """Find all nodes reachable from source within max_depth hops.

        Args:
            source: Starting node name.
            max_depth: Maximum hops from source (default 2).

        Returns:
            List of reachable node names.
        """
        s = self._normalize(source)
        if s not in self._graph:
            return []

        visited = {s}
        frontier = {s}
        related = []

        for _ in range(max_depth):
            next_frontier = set()
            for node in frontier:
                for _, neighbor, _ in self._graph.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        related.append(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier
            if not frontier:
                break

        return related

    # ── Node Importance ─────────────────────────────────────────────────

    def node_importance(self) -> Dict[str, float]:
        """Compute normalized node importance scores (0.0-1.0).

        Based on frequency centrality (in-degree + out-degree),
        normalized by the maximum degree in the graph.

        Returns:
            Dict mapping normalized node names to importance scores.
        """
        if not self._graph:
            return {}

        degrees = {}
        for node in self._graph:
            out_d = len(self._graph.get(node, []))
            in_d = len(self._reverse.get(node, []))
            degrees[node] = in_d + out_d

        max_deg = max(degrees.values()) if degrees else 1
        if max_deg == 0:
            return {node: 0.0 for node in self._graph}

        return {node: round(d / max_deg, 4) for node, d in degrees.items()}
