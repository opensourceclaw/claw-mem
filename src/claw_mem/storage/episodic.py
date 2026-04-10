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
Episodic Memory Storage

Stores daily conversation records, format: memory/YYYY-MM-DD.md
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path


class EpisodicStorage:
    """
    Episodic Memory Storage
    
    Storage location: ~/.openclaw/workspace/memory/YYYY-MM-DD.md
    
    Features:
    - Date-based file storage
    - Auto-expiry (default 30 days)
    - Markdown format, human-readable
    """
    
    def __init__(self, workspace: Path, ttl_days: int = 30):
        """
        Initialize Episodic Storage
        
        Args:
            workspace: Workspace path
            ttl_days: Memory retention days
        """
        self.workspace = workspace
        self.memory_dir = workspace / "memory"
        self.ttl_days = ttl_days
        
        # Ensure directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def store(self, memory_record: Dict) -> None:
        """
        Store memory to today's file
        
        Args:
            memory_record: Memory record
        """
        # Get today's filename
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = self.memory_dir / f"{today}.md"
        
        # Format memory content
        content = self._format_memory(memory_record)
        
        # Append to file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content + "\n")
    
    def get_all(self) -> List[Dict]:
        """
        Get all Episodic memories
        
        Returns:
            List[Dict]: Memory records
        """
        return self._read_all_files()
    
    def get_recent(self, limit: int = 20) -> List[Dict]:
        """
        Get recent memories
        
        Args:
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records
        """
        memories = []
        
        # Get recent N files
        files = sorted(self.memory_dir.glob("*.md"), reverse=True)[:limit]
        
        for file_path in files:
            memories.extend(self._read_file(file_path))
        
        return memories[:limit]
    
    def get_by_date(self, date: str) -> List[Dict]:
        """
        Get memories by date
        
        Args:
            date: Date string (YYYY-MM-DD)
            
        Returns:
            List[Dict]: Memory records
        """
        file_path = self.memory_dir / f"{date}.md"
        if file_path.exists():
            return self._read_file(file_path)
        return []
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired memories
        
        Returns:
            int: Number of deleted files
        """
        cutoff_date = datetime.now() - timedelta(days=self.ttl_days)
        deleted_count = 0
        
        for file_path in self.memory_dir.glob("*.md"):
            # Parse date from filename
            try:
                file_date = datetime.strptime(file_path.stem, "%Y-%m-%d")
                if file_date < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            except ValueError:
                continue
        
        return deleted_count
    
    def count(self) -> int:
        """
        Get number of memory records
        
        Returns:
            int: Record count
        """
        count = 0
        for file_path in self.memory_dir.glob("*.md"):
            count += len(self._read_file(file_path))
        return count
    
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
        metadata = memory_record.get("metadata", {})
        
        # Add metadata comments
        meta = []
        if tags:
            meta.append(f"tags: {', '.join(tags)}")
        if memory_record.get("session_id"):
            meta.append(f"session: {memory_record['session_id']}")
        
        # Add custom metadata fields
        for key, value in metadata.items():
            meta.append(f"{key}: {value}")
        
        # Format output
        lines = []
        if meta:
            lines.append("<!-- " + "; ".join(meta) + " -->")
        lines.append(f"[{timestamp}] {content}")
        
        return "\n".join(lines)
    
    def _read_all_files(self) -> List[Dict]:
        """
        Read all memory files
        
        Returns:
            List[Dict]: All memory records
        """
        memories = []
        
        for file_path in sorted(self.memory_dir.glob("*.md"), reverse=True):
            memories.extend(self._read_file(file_path))
        
        return memories
    
    def _read_file(self, file_path: Path) -> List[Dict]:
        """
        Read memory file
        
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
                        
                        # Extract standard fields
                        session_id = current_meta.get("session")
                        tags_str = current_meta.get("tags", "")
                        
                        # Extract custom metadata (exclude standard fields)
                        metadata = {}
                        for key, value in current_meta.items():
                            if key not in ["tags", "session"]:
                                metadata[key] = value
                        
                        memories.append({
                            "timestamp": timestamp,
                            "content": content,
                            "tags": tags_str.split(", ") if tags_str else [],
                            "session_id": session_id,
                            "metadata": metadata,
                            "type": "episodic",
                            "source": str(file_path)
                        })
                        current_meta = {}  # Reset metadata
                    except (ValueError, IndexError):
                        continue
        
        return memories
    
    def __repr__(self) -> str:
        return f"EpisodicStorage(dir={self.memory_dir}, ttl={self.ttl_days}d)"
