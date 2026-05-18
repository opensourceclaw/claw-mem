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
Graph Storage - Concept-mediated graph storage layer

Supports:
- In-memory storage (InMemoryGraphStorage)
- File persistence (FileGraphStorage)
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
import json
import os
from datetime import datetime

from .nodes import Node, NodeType
from .edges import Edge, EdgeType


class GraphStorage:
    """Graph storage base class"""

    def save_node(self, node: Node) -> None:
        """Save node"""
        raise NotImplementedError

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node"""
        raise NotImplementedError

    def delete_node(self, node_id: str) -> bool:
        """Delete node"""
        raise NotImplementedError

    def get_all_nodes(self) -> List[Node]:
        """Get all nodes"""
        raise NotImplementedError

    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get nodes by type"""
        raise NotImplementedError

    def save_edge(self, edge: Edge) -> None:
        """Save edge"""
        raise NotImplementedError

    def get_edge(self, source_id: str, target_id: str) -> Optional[Edge]:
        """Get edge"""
        raise NotImplementedError

    def delete_edge(self, source_id: str, target_id: str) -> bool:
        """Delete edge"""
        raise NotImplementedError

    def get_all_edges(self) -> List[Edge]:
        """Get all edges"""
        raise NotImplementedError

    def get_edges_from(self, node_id: str) -> List[Edge]:
        """Get edges from node"""
        raise NotImplementedError

    def get_edges_to(self, node_id: str) -> List[Edge]:
        """Get edges to node"""
        raise NotImplementedError

    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get neighbor node IDs"""
        raise NotImplementedError

    def clear(self) -> None:
        """Clear graph"""
        raise NotImplementedError


class InMemoryGraphStorage(GraphStorage):
    """In-memory graph storage

    Suitable for small-scale graphs, data stored in memory.
    """

    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, List[Edge]] = {}  # source_id -> edges
        self._reverse_edges: Dict[str, List[Edge]] = {}  # target_id -> edges
        self._node_types: Dict[NodeType, Set[str]] = {
            NodeType.EPISODE: set(),
            NodeType.FACT: set(),
            NodeType.REFLECTION: set(),
            NodeType.CONCEPT: set(),
        }

    def save_node(self, node: Node) -> None:
        """Save node"""
        self._nodes[node.id] = node
        self._node_types[node.type].add(node.id)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node"""
        return self._nodes.get(node_id)

    def delete_node(self, node_id: str) -> bool:
        """Delete node"""
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]
        del self._nodes[node_id]
        self._node_types[node.type].discard(node_id)

        # Delete related edges
        if node_id in self._edges:
            for edge in self._edges[node_id]:
                self._reverse_edges[edge.target_id] = [
                    e for e in self._reverse_edges.get(edge.target_id, []) if e.source_id != node_id
                ]
            del self._edges[node_id]

        if node_id in self._reverse_edges:
            for edge in self._reverse_edges[node_id]:
                self._edges[edge.source_id] = [
                    e for e in self._edges.get(edge.source_id, []) if e.target_id != node_id
                ]
            del self._reverse_edges[node_id]

        return True

    def get_all_nodes(self) -> List[Node]:
        """Get all nodes"""
        return list(self._nodes.values())

    def get_nodes_by_type(self, node_type: NodeType) -> List[Node]:
        """Get nodes by type"""
        node_ids = self._node_types.get(node_type, set())
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]

    def save_edge(self, edge: Edge) -> None:
        """Save edge"""
        if edge.source_id not in self._edges:
            self._edges[edge.source_id] = []
        self._edges[edge.source_id].append(edge)

        if edge.target_id not in self._reverse_edges:
            self._reverse_edges[edge.target_id] = []
        self._reverse_edges[edge.target_id].append(edge)

    def get_edge(self, source_id: str, target_id: str) -> Optional[Edge]:
        """Get edge"""
        edges = self._edges.get(source_id, [])
        for edge in edges:
            if edge.target_id == target_id:
                return edge
        return None

    def delete_edge(self, source_id: str, target_id: str) -> bool:
        """Delete edge"""
        edges = self._edges.get(source_id, [])
        for i, edge in enumerate(edges):
            if edge.target_id == target_id:
                del edges[i]

                # Delete from reverse
                reverse = self._reverse_edges.get(target_id, [])
                self._reverse_edges[target_id] = [e for e in reverse if e.source_id != source_id]
                return True
        return False

    def get_all_edges(self) -> List[Edge]:
        """Get all edges"""
        all_edges = []
        for edges in self._edges.values():
            all_edges.extend(edges)
        return all_edges

    def get_edges_from(self, node_id: str) -> List[Edge]:
        """Get edges from node"""
        return self._edges.get(node_id, [])

    def get_edges_to(self, node_id: str) -> List[Edge]:
        """Get edges to node"""
        return self._reverse_edges.get(node_id, [])

    def get_neighbors(self, node_id: str) -> Set[str]:
        """Get neighbor node IDs"""
        neighbors = set()

        # Outgoing edges neighbors
        for edge in self._edges.get(node_id, []):
            neighbors.add(edge.target_id)

        # Incoming edges neighbors
        for edge in self._reverse_edges.get(node_id, []):
            neighbors.add(edge.source_id)

        return neighbors

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self.get_all_edges()),
            "episodes": len(self._node_types[NodeType.EPISODE]),
            "facts": len(self._node_types[NodeType.FACT]),
            "reflections": len(self._node_types[NodeType.REFLECTION]),
            "concepts": len(self._node_types[NodeType.CONCEPT]),
        }

    def clear(self) -> None:
        """Clear graph"""
        self._nodes.clear()
        self._edges.clear()
        self._reverse_edges.clear()
        for node_type in self._node_types:
            self._node_types[node_type].clear()


class FileGraphStorage(InMemoryGraphStorage):
    """File graph storage

    Supports persistence to JSON file.
    """

    def __init__(self, file_path: str = "graph.json"):
        super().__init__()
        self.file_path = file_path
        self._load()

    def _load(self) -> None:
        """Load from file"""
        if not os.path.exists(self.file_path):
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load nodes
            for node_data in data.get("nodes", []):
                node = Node.from_dict(node_data)
                self._nodes[node.id] = node
                self._node_types[node.type].add(node.id)

            # Load edges
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                self.save_edge(edge)
        except Exception as e:
            print(f"Failed to load graph from {self.file_path}: {e}")

    def save(self) -> None:
        """Save to file"""
        data = {
            "nodes": [node.to_dict() for node in self.get_all_nodes()],
            "edges": [edge.to_dict() for edge in self.get_all_edges()],
            "saved_at": datetime.now().isoformat(),
        }

        # Ensure directory exists
        dir_path = os.path.dirname(self.file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_node(self, node: Node) -> None:
        """Save node and auto-persist"""
        super().save_node(node)
        if hasattr(self, "file_path"):
            self.save()

    def save_edge(self, edge: Edge) -> None:
        """Save edge and auto-persist"""
        super().save_edge(edge)
        if hasattr(self, "file_path"):
            self.save()

    def delete_node(self, node_id: str) -> bool:
        """Delete node and auto-persist"""
        result = super().delete_node(node_id)
        if result and hasattr(self, "file_path"):
            self.save()
        return result


__all__ = [
    "GraphStorage",
    "InMemoryGraphStorage",
    "FileGraphStorage",
]
