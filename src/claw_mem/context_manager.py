#!/usr/bin/env python3
"""
ClawMem Context Manager - The High-Level Interface for neoclaw.

This module provides a clean API for Friday (neoclaw) to interact with 
the Attention OS, handling initialization, updates, and context assembly.
"""

import os
from pathlib import Path
from typing import List, Optional
from .attention_index import AttentionIndex
from .context_assembler import ContextAssembler
from .atomic_writer import AtomicWriter
import logging

logger = logging.getLogger(__name__)


class ClawMemContextManager:
    """
    Manages the interaction between neoclaw and the claw-mem Attention OS.
    """

    def __init__(self, memory_root: str, core_rules: Optional[List[str]] = None):
        self.index = AttentionIndex(memory_root)
        self.assembler = ContextAssembler(self.index, core_rules)
        self._initialized = False

    def initialize(self) -> None:
        """
        Loads all Markdown files into the in-memory Attention Index 
        and applies decay logic.
        """
        logger.info("Initializing ClawMem Context Manager...")
        self.index.build_index()
        self.index.apply_decay(0.9)  # Apply natural forgetting
        self._initialized = True
        logger.info("ClawMem Context Manager initialized.")

    def get_context(self, max_tokens: int = 4000, top_k: int = 3) -> str:
        """
        Retrieves the dynamically assembled context for the LLM.
        """
        if not self._initialized:
            raise RuntimeError("ClawMemContextManager not initialized. Call initialize() first.")
        
        return self.assembler.assemble_context(max_tokens, top_k)

    def boost_node(self, node_id: str, amount: float = 0.1) -> bool:
        """
        Manually boosts the attention score of a specific node.
        """
        if node_id not in self.index.nodes:
            logger.warning(f"Node {node_id} not found in index. Skipping boost.")
            return False
        self.index.update_node_score(node_id, self.index.nodes[node_id].score + amount)
        return True

    def save_changes(self) -> None:
        """
        Persists all in-memory score changes back to Markdown files.
        """
        self.index.sync_to_disk()
