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
Graph Edges - Concept-mediated graph edge types

Based on GAAMA paper's five edge types:
- NEXT: Episode sequence (Episode → Episode)
- DERIVED_FROM: Fact origin (Fact → Episode)
- SYNTHESIZED_FROM: Reflection origin (Reflection → Episode/Fact)
- RELATED_TO: Related relationship (between any nodes)
- HAS_CONCEPT: Concept association (Any node → Concept)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


class EdgeType(Enum):
    """Graph edge types"""

    NEXT = "NEXT"  # Episode sequence
    DERIVED_FROM = "DERIVED_FROM"  # Fact origin
    SYNTHESIZED_FROM = "SYNTHESIZED_FROM"  # Reflection origin
    RELATED_TO = "RELATED_TO"  # Related relationship
    HAS_CONCEPT = "HAS_CONCEPT"  # Concept association

    def is_directed(self) -> bool:
        """Whether this is a directed edge"""
        return self != EdgeType.RELATED_TO


@dataclass
class Edge:
    """Graph edge

    Attributes:
        source_id: Source node ID
        target_id: Target node ID
        type: Edge type
        weight: Weight (default 1.0)
        metadata: Metadata
        created_at: Creation time
    """

    source_id: str
    target_id: str
    type: EdgeType
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value,
            "weight": self.weight,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Edge":
        """Create from dictionary"""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            type=EdgeType(data["type"]),
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
            created_at=created_at,
        )


@dataclass
class NextEdge(Edge):
    """Episode sequence edge - Episode → Episode

    Represents consecutive episode relationships in a conversation.
    """

    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.NEXT, **kwargs)


@dataclass
class DerivedFromEdge(Edge):
    """Fact origin edge - Fact → Episode

    Indicates which episode a fact was extracted from.
    """

    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.DERIVED_FROM, **kwargs)


@dataclass
class SynthesizedFromEdge(Edge):
    """Reflection origin edge - Reflection → Episode/Fact

    Indicates which nodes a reflection was synthesized from.
    """

    source_node_ids: List[str] = field(default_factory=list)

    def __init__(self, source_id: str, target_id: str, source_node_ids: List[str] = None, **kwargs):
        super().__init__(source_id, target_id, EdgeType.SYNTHESIZED_FROM, **kwargs)
        self.source_node_ids = source_node_ids or []


@dataclass
class RelatedToEdge(Edge):
    """Related relationship edge - Between any nodes

    Represents a related relationship between two nodes (undirected edge).
    """

    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.RELATED_TO, **kwargs)


@dataclass
class HasConceptEdge(Edge):
    """Concept association edge - Any node → Concept

    Indicates a node is associated with a concept.
    """

    def __init__(self, source_id: str, target_id: str, **kwargs):
        super().__init__(source_id, target_id, EdgeType.HAS_CONCEPT, **kwargs)


def create_edge(edge_type: EdgeType, source_id: str, target_id: str, **kwargs) -> Edge:
    """Factory function: create edge

    Args:
        edge_type: Edge type
        source_id: Source node ID
        target_id: Target node ID
        **kwargs: Other parameters

    Returns:
        Edge: Edge instance

    Example:
        >>> edge = create_edge(EdgeType.NEXT, "ep_1", "ep_2")
    """
    if edge_type == EdgeType.NEXT:
        return NextEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.DERIVED_FROM:
        return DerivedFromEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.SYNTHESIZED_FROM:
        return SynthesizedFromEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.RELATED_TO:
        return RelatedToEdge(source_id, target_id, **kwargs)
    elif edge_type == EdgeType.HAS_CONCEPT:
        return HasConceptEdge(source_id, target_id, **kwargs)
    else:
        raise ValueError(f"Unknown edge type: {edge_type}")


__all__ = [
    "EdgeType",
    "Edge",
    "NextEdge",
    "DerivedFromEdge",
    "SynthesizedFromEdge",
    "RelatedToEdge",
    "HasConceptEdge",
    "create_edge",
]
