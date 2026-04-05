#!/usr/bin/env python3
"""
Attention Index - The In-Memory Map of the Attention OS.

This module is responsible for scanning the Markdown file system,
parsing Frontmatter, and building a high-performance in-memory index
for the Attention Engine.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from .attention_node import AttentionNode
from .atomic_writer import AtomicWriter
import logging

logger = logging.getLogger(__name__)


class AttentionIndex:
    """
    Manages the in-memory representation of the Attention DAG.
    
    Acts as the bridge between the persistent Markdown files (Disk)
    and the real-time attention scoring logic (RAM).
    """

    def __init__(self, memory_root: str):
        self.memory_root = Path(memory_root)
        self.nodes: Dict[str, AttentionNode] = {}
        self._index_built = False

    def build_index(self) -> None:
        """
        Scans the memory root and builds the in-memory index.
        This should be called once during system startup.
        """
        logger.info(f"Building Attention Index from: {self.memory_root}")
        self.nodes.clear()
        
        if not self.memory_root.exists():
            logger.warning(f"Memory root not found: {self.memory_root}")
            return

        for md_file in self.memory_root.rglob("*.md"):
            try:
                node = self._parse_md_file(md_file)
                if node:
                    self.nodes[node.node_id] = node
            except Exception as e:
                logger.error(f"Failed to parse {md_file}: {e}")

        self._index_built = True
        logger.info(f"Index built with {len(self.nodes)} nodes.")

    def _parse_md_file(self, file_path: Path) -> Optional[AttentionNode]:
        """
        Parses a single Markdown file to extract AttentionNode data.
        Expects YAML Frontmatter at the top of the file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple Frontmatter extraction (assumes --- delimiter)
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1])
                    if meta and "id" in meta:
                        return AttentionNode(
                            node_id=str(meta["id"]),
                            content_path=str(file_path),
                            score=float(meta.get("attention_score", 0.5)),
                            parents=meta.get("parents", []),
                            type=meta.get("type", "message")
                        )
        except Exception as e:
            logger.error(f"Error parsing Frontmatter in {file_path}: {e}")
        
        return None

    def get_node(self, node_id: str) -> Optional[AttentionNode]:
        """Retrieves a node by ID from the in-memory index."""
        return self.nodes.get(node_id)

    def get_top_k_nodes(self, k: int = 10) -> List[AttentionNode]:
        """
        Returns the top-K nodes sorted by attention score.
        This is the core query for the 'Working Memory' assembly.
        """
        if not self._index_built:
            return []
        
        # Sort by score descending
        sorted_nodes = sorted(
            self.nodes.values(), 
            key=lambda n: n.score, 
            reverse=True
        )
        return sorted_nodes[:k]

    def get_causal_chain(self, node_id: str, max_depth: int = 2) -> List[AttentionNode]:
        """
        Retrieves a node and its parents (causal chain) from the DAG.
        
        Args:
            node_id: The starting node ID.
            max_depth: How many levels of parents to traverse.
            
        Returns:
            A list of nodes representing the causal chain.
        """
        chain = []
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            node = self.nodes.get(current_id)
            if node:
                chain.append(node)
                # Add parents to the queue for the next level
                for parent_id in node.parents:
                    queue.append((parent_id, depth + 1))
        
        return chain

    def sync_to_disk(self) -> int:
        """
        Persists all in-memory node changes back to Markdown files atomically.
        
        Returns:
            The number of nodes successfully saved.
        """
        saved_count = 0
        for node in self.nodes.values():
            if AtomicWriter.save_node(node):
                saved_count += 1
        logger.info(f"Synced {saved_count} nodes to disk.")
        return saved_count

    def apply_decay(self, decay_factor: float = 0.9) -> None:
        """
        Applies natural decay to all nodes in the index.
        
        This simulates the "forgetting" process. Nodes that are not 
        actively reinforced will gradually fade into the background.
        
        Args:
            decay_factor: The rate of decay (e.g., 0.9 means 10% loss per cycle).
        """
        logger.info(f"Applying attention decay with factor: {decay_factor}")
        for node in self.nodes.values():
            # Ensure score doesn't drop below a minimum threshold (e.g., 0.1)
            new_score = node.score * decay_factor
            node.score = max(0.1, new_score)
            node.last_updated = __import__('datetime').datetime.now()

    def update_node_score(self, node_id: str, new_score: float) -> bool:
        """
        Updates a node's score in RAM. 
        Persistence to Disk is handled asynchronously by the Engine.
        """
        if node_id in self.nodes:
            self.nodes[node_id].score = max(0.0, min(1.0, new_score))
            self.nodes[node_id].last_updated = __import__('datetime').datetime.now()
            return True
        return False
