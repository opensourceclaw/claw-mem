#!/usr/bin/env python3
"""
Attention Node - The basic unit of the Attention OS.

Each node represents a piece of context (a message, a summary, or a rule)
with an associated attention score that determines its visibility to the Agent.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class AttentionNode:
    """
    Represents a single context unit in the Weighted DAG.
    
    Attributes:
        node_id: Unique identifier (usually from Markdown Frontmatter).
        content_path: Path to the .md file storing the actual content.
        score: Current attention weight (0.0 - 1.0).
        parents: List of parent node IDs (defines the DAG topology).
        last_updated: Timestamp of the last score update.
        type: Type of node (e.g., 'message', 'summary', 'rule', 'core').
    """
    node_id: str
    content_path: str
    score: float = 0.5  # Default mid-level attention
    parents: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    type: str = "message"  # 'message', 'summary', 'rule', 'core'

    def to_dict(self) -> dict:
        """Serialize node for storage or debugging."""
        return {
            "node_id": self.node_id,
            "content_path": self.content_path,
            "score": self.score,
            "parents": self.parents,
            "last_updated": self.last_updated.isoformat(),
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttentionNode":
        """Deserialize node from a dictionary."""
        return cls(
            node_id=data["node_id"],
            content_path=data["content_path"],
            score=data.get("score", 0.5),
            parents=data.get("parents", []),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            type=data.get("type", "message"),
        )
