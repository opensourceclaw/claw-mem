#!/usr/bin/env python3
"""
Context Assembler - The Dynamic Prompt Builder for the Attention OS.

This module dynamically assembles the context for the LLM processor
by combining static Core Blocks with high-attention dynamic nodes.
"""

import os
from pathlib import Path
from typing import List, Optional
from .attention_index import AttentionIndex
from .attention_node import AttentionNode
import logging

logger = logging.getLogger(__name__)


class ContextAssembler:
    """
    Assembles the final context string for the LLM based on 
    current attention scores and predefined rules.
    """

    def __init__(self, index: AttentionIndex, core_block_paths: Optional[List[str]] = None):
        self.index = index
        self.core_block_paths = core_block_paths or []

    def assemble_context(self, max_tokens: int = 4000, top_k: int = 3, causal_depth: int = 1) -> str:
        """
        Assembles the final context string with Causal Link Retrieval.
        
        Args:
            max_tokens: Maximum token budget for the context.
            top_k: Number of high-attention seed nodes to start from.
            causal_depth: How many levels of parent nodes to include.
        """
        context_parts = []

        # 1. Inject Core Blocks (Highest Priority)
        for path in self.core_block_paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                context_parts.append(f"### 🛡️ Core Rule: {Path(path).stem}\n{content}\n")

        # 2. Inject Causal Chains from Top-K Nodes
        seed_nodes = self.index.get_top_k_nodes(top_k)
        included_ids = set()
        content_parts = []

        for seed in seed_nodes:
            chain = self.index.get_causal_chain(seed.node_id, causal_depth)
            for node in chain:
                if node.node_id not in included_ids:
                    if os.path.exists(node.content_path):
                        with open(node.content_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        content_parts.append(f"### 🧠 Context Node (Score: {node.score:.2f})\n{content}\n")
                        included_ids.add(node.node_id)

        final_context = "\n---\n".join(context_parts + content_parts)
        
        # 3. Token Truncation (Estimate: 1 token ≈ 4 chars)
        max_length = max_tokens * 4 - 50  # Reserve 50 chars for safety
        if len(final_context) > max_length:
            # Truncate at the end of the last word/sentence to preserve context
            final_context = final_context[:max_length]
            last_space = final_context.rfind(" ")
            if last_space != -1:
                final_context = final_context[:last_space] + "..."

        return final_context

    def add_core_block(self, path: str) -> None:
        """Adds a new static rule to the context assembly."""
        if os.path.exists(path):
            self.core_block_paths.append(path)
            logger.info(f"Added core block: {path}")
        else:
            logger.error(f"Core block not found: {path}")
