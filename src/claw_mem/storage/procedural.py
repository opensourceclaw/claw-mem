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
Procedural Memory Storage

Stores skill and process memories, format: memory/skills/*.md
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class ProceduralStorage:
    """
    Procedural Memory Storage
    
    Storage location: ~/.openclaw/workspace/memory/skills/*.md
    
    Features:
    - Permanent storage (no expiry)
    - Skills, processes, best practices
    - Markdown format, human-readable
    - Skill-based file storage
    """
    
    def __init__(self, workspace: Path):
        """
        Initialize Procedural Storage
        
        Args:
            workspace: Workspace path
        """
        self.workspace = workspace
        self.skills_dir = workspace / "memory" / "skills"
        
        # Ensure directory exists
        self.skills_dir.mkdir(parents=True, exist_ok=True)
    
    def store(self, memory_record: Dict) -> None:
        """
        Store skill memory
        
        Args:
            memory_record: Memory record
        """
        # Extract skill name from tags or content
        skill_name = self._extract_skill_name(memory_record)
        file_path = self.skills_dir / f"{skill_name}.md"
        
        # Format and store
        content = self._format_memory(memory_record)
        
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
    
    def get_skill(self, skill_name: str) -> List[Dict]:
        """
        Get memories for specific skill
        
        Args:
            skill_name: Skill name
            
        Returns:
            List[Dict]: Memory records
        """
        file_path = self.skills_dir / f"{skill_name}.md"
        if file_path.exists():
            return self._read_file(file_path)
        return []
    
    def get_all(self) -> List[Dict]:
        """
        Get all skill memories
        
        Returns:
            List[Dict]: Memory records
        """
        memories = []
        
        for file_path in self.skills_dir.glob("*.md"):
            memories.extend(self._read_file(file_path))
        
        return memories
    
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """
        Search skill memories by keyword
        
        Args:
            keyword: Keyword
            
        Returns:
            List[Dict]: Memory records
        """
        memories = []
        
        for file_path in self.skills_dir.glob("*.md"):
            file_memories = self._read_file(file_path)
            for memory in file_memories:
                if keyword.lower() in memory.get("content", "").lower():
                    memories.append(memory)
        
        return memories
    
    def count(self) -> int:
        """
        Get number of procedural memory records
        
        Returns:
            int: Record count
        """
        count = 0
        for file_path in self.skills_dir.glob("*.md"):
            count += len(self._read_file(file_path))
        return count
    
    def _extract_skill_name(self, memory_record: Dict) -> str:
        """
        Extract skill name from memory record
        
        Args:
            memory_record: Memory record
            
        Returns:
            str: Skill name
        """
        # Prefer tags
        tags = memory_record.get("tags", [])
        for tag in tags:
            if tag not in ["procedural", "skill"]:
                return self._sanitize_filename(tag)
        
        # Otherwise use generic name
        return "general"
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize filename characters
        
        Args:
            name: Original name
            
        Returns:
            str: Sanitized name
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        return name.lower().strip()
    
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
        
        # Add metadata comments
        meta = []
        if tags:
            meta.append(f"tags: {', '.join(tags)}")
        
        # Format output
        lines = []
        if meta:
            lines.append("<!-- " + "; ".join(meta) + " -->")
        lines.append(f"[{timestamp}] {content}")
        lines.append("")  # Empty line separator
        
        return "\n".join(lines)
    
    def _read_file(self, file_path: Path) -> List[Dict]:
        """
        Read skill file
        
        Args:
            file_path: File path
            
        Returns:
            List[Dict]: Memory records
        """
        memories = []
        
        if not file_path.exists():
            return memories
        
        with open(file_path, "r", encoding="utf-8") as f:
            current_meta = {}
            for line in f:
                line = line.strip()
                if not line:
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
                            "timestamp": timestamp,
                            "content": content,
                            "tags": current_meta.get("tags", "").split(", ") if current_meta.get("tags") else [],
                            "type": "procedural",
                            "source": str(file_path)
                        })
                        current_meta = {}  # Reset metadata
                    except (ValueError, IndexError):
                        continue
        
        return memories
    
    def __repr__(self) -> str:
        return f"ProceduralStorage(dir={self.skills_dir})"
