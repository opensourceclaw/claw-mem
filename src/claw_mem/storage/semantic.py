"""
Semantic Memory Storage

Stores core factual memories, format: MEMORY.md
"""

import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SemanticStorage:
    """
    Semantic Memory Storage
    
    Storage location: ~/.openclaw/workspace/MEMORY.md
    
    Features:
    - Permanent storage (no expiry)
    - Core facts and user preferences
    - Markdown format, human-readable
    - Tag and category support
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize Semantic Storage
        
        Args:
            workspace: Workspace path
        """
        self.workspace = workspace
        self.file_path = workspace / "MEMORY.md"
        
        # Ensure file exists
        if not self.file_path.exists():
            self._initialize_file()
    
    def store(self, memory_record: Dict) -> None:
        """
        Store memory to MEMORY.md
        
        Args:
            memory_record: Memory record
        """
        content = self._format_memory(memory_record)
        
        # Append to file
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
    
    def get_all(self) -> List[Dict]:
        """
        Get all Semantic memories
        
        Returns:
            List[Dict]: Memory records
        """
        return self._read_file()
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """
        Search memories by tag
        
        Args:
            tag: Tag
            
        Returns:
            List[Dict]: Memory records
        """
        memories = self.get_all()
        return [m for m in memories if tag in m.get("tags", [])]
    
    def update(self, memory_id: str, new_content: str) -> bool:
        """
        Update memory content
        
        Args:
            memory_id: Memory ID
            new_content: New content
            
        Returns:
            bool: Success status
        """
        memories = self.get_all()
        
        for i, memory in enumerate(memories):
            if memory.get("id") == memory_id:
                memories[i]["content"] = new_content
                memories[i]["updated_at"] = datetime.now().isoformat()
                
                # Rewrite entire file
                self._rewrite_file(memories)
                return True
        
        return False
    
    def count(self) -> int:
        """
        Get memory count
        
        Returns:
            int: Memory count
        """
        return len(self.get_all())
    
    def _initialize_file(self) -> None:
        """
        Initialize MEMORY.md file
        """
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("# MEMORY.md\n\n")
            f.write("<!-- Core Memory - Permanent Storage -->\n\n")
            f.write("<!-- Format: [timestamp] content <!-- tags: tag1, tag2 --> -->\n\n")
    
    def _format_memory(self, memory_record: Dict) -> str:
        """
        Format memory record to Markdown
        
        Args:
            memory_record: Memory record
            
        Returns:
            str: Markdown formatted content
        """
        timestamp = memory_record.get("timestamp", datetime.now().isoformat())
        content = memory_record.get("content", "")
        tags = memory_record.get("tags", [])
        memory_id = memory_record.get("id", self._generate_id())
        
        # Add metadata comments
        meta = []
        if tags:
            meta.append(f"tags: {', '.join(tags)}")
        if memory_id:
            meta.append(f"id: {memory_id}")
        
        # Format output
        lines = []
        lines.append(f"<!-- " + "; ".join(meta) + " -->")
        lines.append(f"[{timestamp}] {content}")
        lines.append("")  # Empty line separator
        
        return "\n".join(lines)
    
    def _read_file(self) -> List[Dict]:
        """
        Read MEMORY.md file
        
        Returns:
            List[Dict]: Memory records
        """
        memories = []
        
        if not self.file_path.exists():
            return memories
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            current_meta = {}
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Parse metadata comments
                if line.startswith("<!--") and line.endswith("-->"):
                    meta_content = line[4:-3].strip()
                    for item in meta_content.split(";"):
                        if ":" in item:
                            key, value = item.split(":", 1)
                            current_meta[key.strip()] = value.strip()
                # Parse memory content
                elif line.startswith("["):
                    try:
                        end_timestamp = line.index("]")
                        timestamp = line[1:end_timestamp]
                        content = line[end_timestamp+1:].strip()
                        
                        memories.append({
                            "id": current_meta.get("id"),
                            "timestamp": timestamp,
                            "content": content,
                            "tags": current_meta.get("tags", "").split(", ") if current_meta.get("tags") else [],
                            "type": "semantic",
                            "source": str(self.file_path)
                        })
                        current_meta = {}  # Reset metadata
                    except (ValueError, IndexError):
                        continue
        
        return memories
    
    def _rewrite_file(self, memories: List[Dict]) -> None:
        """
        Rewrite MEMORY.md file
        
        Args:
            memories: Memory records
        """
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("# MEMORY.md\n\n")
            f.write("<!-- Core Memory - Permanent Storage -->\n\n")
            
            for memory in memories:
                f.write(self._format_memory(memory))
    
    def _generate_id(self) -> str:
        """
        Generate memory ID
        
        Returns:
            str: Memory ID
        """
        import uuid
        return str(uuid.uuid4())[:8]
    
    def __repr__(self) -> str:
        return f"SemanticStorage(file={self.file_path})"
