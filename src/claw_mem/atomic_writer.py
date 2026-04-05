#!/usr/bin/env python3
"""
Atomic Writer - Ensures data integrity for Markdown-based Attention OS.

Uses the "Write-to-Temp + os.replace()" pattern to guarantee that
Markdown files are never left in a corrupted state, even during crashes.
"""

import os
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any
from .attention_node import AttentionNode
import logging

logger = logging.getLogger(__name__)


class AtomicWriter:
    """
    Handles the safe persistence of AttentionNode metadata back to Markdown files.
    """

    @staticmethod
    def save_node(node: AttentionNode) -> bool:
        """
        Atomically updates the Frontmatter of a specific Markdown file.
        
        Args:
            node: The AttentionNode containing updated metadata.
            
        Returns:
            True if the file was successfully updated.
        """
        file_path = Path(node.content_path)
        if not file_path.exists():
            logger.warning(f"File not found for node {node.node_id}: {file_path}")
            return False

        try:
            # 1. Read existing content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 2. Prepare new Frontmatter
            new_meta = {
                "id": node.node_id,
                "attention_score": node.score,
                "parents": node.parents,
                "type": node.type,
                "last_updated": node.last_updated.isoformat()
            }
            
            # 3. Construct new file content (replace old Frontmatter)
            new_content = AtomicWriter._replace_frontmatter(content, new_meta)

            # 4. Write to temporary file in the same directory (for atomic replace)
            dir_name = file_path.parent
            fd, tmp_path = tempfile.mkstemp(dir=str(dir_name), suffix='.tmp')
            
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as tmp_file:
                    tmp_file.write(new_content)
                
                # 5. Atomic replace
                os.replace(tmp_path, str(file_path))
                logger.debug(f"Atomically saved node {node.node_id} to {file_path}")
                return True
                
            except Exception as e:
                # Clean up tmp file if replace fails
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise e

        except Exception as e:
            logger.error(f"Failed to atomically save {file_path}: {e}")
            return False

    @staticmethod
    def _replace_frontmatter(content: str, new_meta: Dict[str, Any]) -> str:
        """
        Replaces the YAML Frontmatter in a Markdown string.
        """
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                # Keep the body (parts[2]) and replace the header
                return f"---\n{yaml.dump(new_meta, sort_keys=False)}---{parts[2]}"
        
        # If no frontmatter, prepend it
        return f"---\n{yaml.dump(new_meta, sort_keys=False)}---\n{content}"
