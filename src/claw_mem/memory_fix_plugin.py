#!/usr/bin/env python3
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
claw-mem Memory System Bug Fix Plugin

Fixes memory retrieval, update, and injection issues without modifying OpenClaw core.

Fixes:
1. Memory retrieval accuracy (exact match priority)
2. Memory deduplication (update vs add)
3. Session start validation
"""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class MemoryFixPlugin:
    """
    Memory System Fix Plugin
    
    Fixes known bugs by wrapping and enhancing OpenClaw native memory functions.
    """
    
    def __init__(self, workspace: str):
        """
        Initialize plugin
        
        Args:
            workspace: OpenClaw workspace path
        """
        self.workspace = Path(workspace).expanduser()
        self.memory_file = self.workspace / "MEMORY.md"
        self.fix_log_file = self.workspace / ".claw-mem" / "memory_fix.log"
        self.fix_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # Fix 1: Improved Memory Retrieval - Exact Match Priority
    # ========================================================================
    
    def retrieve_with_priority(self, query: str, memories: List[Dict]) -> List[Dict]:
        """
        Memory retrieval with priority
        
        Priority rules:
        1. Exact match (URL, path, name, etc.)
        2. Latest correction priority (time weight)
        3. Confidence score (user correction = high confidence)
        
        Args:
            query: Search query
            memories: Memory list
        
        Returns:
            list: Sorted memory list (most relevant first)
        """
        scored_memories = []
        
        for memory in memories:
            score = self._calculate_retrieval_score(query, memory)
            scored_memories.append({
                'memory': memory,
                'score': score
            })
        
        # Sort by score descending
        scored_memories.sort(key=lambda x: x['score'], reverse=True)
        
        # Return sorted memories
        return [item['memory'] for item in scored_memories]
    
    def _calculate_retrieval_score(self, query: str, memory: Dict) -> float:
        """
        Calculate memory retrieval score
        
        Args:
            query: Search query
            memory: Memory dict
        
        Returns:
            float: Retrieval score (higher = more relevant)
        """
        score = 0.0
        memory_content = memory.get('content', '')
        
        # 1. Exact match (highest priority)
        if self._is_exact_match(query, memory_content):
            score += 100.0
        
        # 2. Critical info type bonus (URL, path, etc.)
        if self._is_critical_info(query):
            if query.lower() in memory_content.lower():
                score += 50.0
        
        # 3. Time weight (new corrections priority)
        timestamp = memory.get('timestamp')
        if timestamp:
            days_old = self._days_since(timestamp)
            if days_old < 1:  # Today
                score += 20.0
            elif days_old < 7:  # Within 7 days
                score += 10.0
            elif days_old < 30:  # Within 30 days
                score += 5.0
        
        # 4. Confidence (user explicit correction priority)
        if memory.get('confidence', 0) > 0.8:
            score += 15.0
        
        # 5. Keyword matching
        query_words = query.lower().split()
        content_lower = memory_content.lower()
        matched_words = sum(1 for word in query_words if word in content_lower)
        score += matched_words * 2.0
        
        return score
    
    def _is_exact_match(self, query: str, content: str) -> bool:
        """Check if exact match"""
        # URL exact match
        url_pattern = r'https?://\S+'
        query_urls = re.findall(url_pattern, query)
        content_urls = re.findall(url_pattern, content)
        
        for url in query_urls:
            if url in content_urls:
                return True
        
        # Path exact match
        path_pattern = r'~?/\S+|\.openclaw/\S+'
        query_paths = re.findall(path_pattern, query)
        content_paths = re.findall(path_pattern, content)
        
        for path in query_paths:
            if path in content_paths:
                return True
        
        # Plain text exact match (case insensitive)
        return query.lower().strip() in content.lower().strip()
    
    def _is_critical_info(self, text: str) -> bool:
        """Check if critical info (URL, path, name, etc.)"""
        critical_patterns = [
            r'https?://',           # URL
            r'~?/\S+',              # Path
            r'\.openclaw',          # OpenClaw path
            r'github\.com',         # GitHub
            r'\.git$',              # Git repo
        ]
        
        return any(re.search(pattern, text) for pattern in critical_patterns)
    
    def _days_since(self, timestamp_str: str) -> int:
        """Calculate days since a date"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            return (datetime.now() - timestamp).days
        except (ValueError, TypeError) as e:
            # Invalid timestamp format, return a large number to indicate old data
            return 999
    
    # ========================================================================
    # Fix 2: Memory Update Deduplication - Detect and Update Instead of Add
    # ========================================================================
    
    def store_with_dedup(self, content: str, memory_type: str = "semantic", 
                         tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Memory storage with deduplication
        
        Args:
            content: Memory content
            memory_type: Memory type
            tags: Tag list
        
        Returns:
            tuple: (success, message)
        """
        if not self.memory_file.exists():
            return self._add_new_memory(content, memory_type, tags)
        
        # Read existing memories
        existing_memories = self._read_memories()
        
        # Detect similar entries
        similar = self._find_similar_memory(content, existing_memories)
        
        if similar:
            # Found similar entry, update instead of add
            return self._update_memory(similar['index'], content, tags)
        else:
            # No similar entry, add new
            return self._add_new_memory(content, memory_type, tags)
    
    def _find_similar_memory(self, content: str, memories: List[Dict]) -> Optional[Dict]:
        """
        Find similar memory entry
        
        Args:
            content: New memory content
            memories: Existing memory list
        
        Returns:
            Similar memory info (if found), otherwise None
        """
        for i, memory in enumerate(memories):
            similarity = self._calculate_similarity(content, memory['content'])
            if similarity > 0.7:  # 70% similarity threshold
                return {
                    'index': i,
                    'memory': memory,
                    'similarity': similarity
                }
        return None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts
        
        Args:
            text1: Text 1
            text2: Text 2
        
        Returns:
            float: Similarity (0-1)
        """
        # Extract key info (URL, path, etc.)
        key1 = self._extract_key_info(text1)
        key2 = self._extract_key_info(text2)
        
        # If key info is same, consider highly similar
        if key1 == key2 and len(key1) > 10:  # Avoid short string false positive
            return 1.0
        
        # Check if contains same key pattern
        if self._has_same_key_pattern(text1, text2):
            return 0.8
        
        # Simple word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Filter common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once'}
        words1 = {w for w in words1 if w not in stop_words and len(w) > 1}
        words2 = {w for w in words2 if w not in stop_words and len(w) > 1}
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _has_same_key_pattern(self, text1: str, text2: str) -> bool:
        """Check if has same key pattern (e.g. same URL or path)"""
        # Extract URLs
        urls1 = set(re.findall(r'https?://\S+', text1))
        urls2 = set(re.findall(r'https?://\S+', text2))
        if urls1 and urls2 and urls1 & urls2:
            return True
        
        # Extract paths
        paths1 = set(re.findall(r'~?/\S+|\.openclaw/\S+', text1))
        paths2 = set(re.findall(r'~?/\S+|\.openclaw/\S+', text2))
        if paths1 and paths2 and paths1 & paths2:
            return True
        
        return False
    
    def _extract_key_info(self, text: str) -> str:
        """Extract key info (URL, path, etc.)"""
        # URL
        urls = re.findall(r'https?://\S+', text)
        if urls:
            return urls[0]
        
        # Path
        paths = re.findall(r'~?/\S+|\.openclaw/\S+', text)
        if paths:
            return paths[0]
        
        return text.strip()
    
    def _read_memories(self) -> List[Dict]:
        """Read all memories from MEMORY.md"""
        if not self.memory_file.exists():
            return []
        
        memories = []
        with open(self.memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse memory entries
        pattern = r'\[([^\]]+)\]\s*(.+?)\s*(?:<!--\s*tags:\s*([^>]+)\s*-->)?'
        matches = re.findall(pattern, content, re.MULTILINE)
        
        for timestamp, content_str, tags_str in matches:
            memories.append({
                'timestamp': timestamp.strip(),
                'content': content_str.strip(),
                'tags': [t.strip() for t in tags_str.split(',')] if tags_str else [],
                'confidence': 1.0  # Default high confidence
            })
        
        return memories
    
    def _add_new_memory(self, content: str, memory_type: str, 
                       tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Add new memory"""
        try:
            timestamp = datetime.now().isoformat()
            tags_str = f" <!-- tags: {', '.join(tags)} -->" if tags else ""
            
            with open(self.memory_file, 'a', encoding='utf-8') as f:
                f.write(f"\n[{timestamp}] {content}{tags_str}\n")
            
            self._log_fix("add", content)
            return True, "Memory added successfully"
        except Exception as e:
            return False, f"Add failed: {str(e)}"
    
    def _update_memory(self, index: int, content: str, 
                      tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Update existing memory"""
        try:
            memories = self._read_memories()
            
            if index >= len(memories):
                return False, "Memory index out of range"
            
            # Update memory content
            memories[index]['content'] = content
            if tags:
                memories[index]['tags'] = tags
            memories[index]['timestamp'] = datetime.now().isoformat()
            memories[index]['confidence'] = 1.0  # User correction = high confidence
            
            # Write back to file
            self._write_memories(memories)
            
            self._log_fix("update", content)
            return True, "Memory updated successfully"
        except Exception as e:
            return False, f"Update failed: {str(e)}"
    
    def _write_memories(self, memories: List[Dict]):
        """Write back memory file"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            f.write("# MEMORY.md\n\n")
            f.write("<!-- Core Memory - Permanent Storage -->\n\n")
            
            for memory in memories:
                tags_str = f" <!-- tags: {', '.join(memory['tags'])} -->" if memory.get('tags') else ""
                f.write(f"[{memory['timestamp']}] {memory['content']}{tags_str}\n")
    
    def _log_fix(self, action: str, content: str):
        """Log fix action"""
        with open(self.fix_log_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {action.upper()}: {content}\n")
    
    # ========================================================================
    # Fix 3: Session Start Validation
    # ========================================================================
    
    def validate_session_memory(self) -> Dict:
        """
        Validate memory at session start
        
        Returns:
            dict: Validation result
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'memories_count': 0,
        }
        
        # Check if memory file exists
        if not self.memory_file.exists():
            result['warnings'].append("MEMORY.md does not exist, will create new file")
            return result
        
        # Read and validate memories
        try:
            memories = self._read_memories()
            result['memories_count'] = len(memories)
            
            if len(memories) == 0:
                result['warnings'].append("Memory file is empty")
            
            # Check duplicate entries
            duplicates = self._find_duplicates(memories)
            if duplicates:
                result['errors'].append(f"Found {len(duplicates)} duplicate entries")
                result['valid'] = False
            
            # Check conflict entries
            conflicts = self._find_conflicts(memories)
            if conflicts:
                result['errors'].append(f"Found {len(conflicts)} conflicting entries")
                result['valid'] = False
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Failed to read memories: {str(e)}")
        
        return result
    
    def _find_duplicates(self, memories: List[Dict]) -> List[Dict]:
        """Find duplicate entries"""
        seen = {}
        duplicates = []
        
        for memory in memories:
            key = self._extract_key_info(memory['content'])
            if key in seen:
                duplicates.append(memory)
            else:
                seen[key] = memory
        
        return duplicates
    
    def _find_conflicts(self, memories: List[Dict]) -> List[Dict]:
        """Find conflicting entries (same key info but different content)"""
        # Simplified version: check if URL/path maps to multiple different values
        urls = {}
        conflicts = []
        
        for memory in memories:
            url = self._extract_key_info(memory['content'])
            if url.startswith('http'):
                if url in urls and urls[url] != memory['content']:
                    conflicts.append(memory)
                else:
                    urls[url] = memory['content']
        
        return conflicts
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_fix_statistics(self) -> Dict:
        """Get fix statistics"""
        stats = {
            'workspace': str(self.workspace),
            'memory_file_exists': self.memory_file.exists(),
            'memories_count': 0,
            'fix_log_exists': self.fix_log_file.exists(),
            'fix_actions': 0,
        }
        
        if self.memory_file.exists():
            stats['memories_count'] = len(self._read_memories())
        
        if self.fix_log_file.exists():
            with open(self.fix_log_file, 'r') as f:
                stats['fix_actions'] = sum(1 for _ in f)
        
        return stats


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    workspace = "~/.openclaw/workspace"
    plugin = MemoryFixPlugin(workspace)
    
    print("Testing F000 Memory System Fix Plugin\n")
    
    # Test 1: Store memory (with dedup)
    print("Test 1: Store memory (with dedup)")
    success, msg = plugin.store_with_dedup(
        "User prefers Chinese language",
        memory_type="semantic",
        tags=["preference", "language"]
    )
    print(f"  {msg}")
    
    # Test 2: Validate session memory
    print("\nTest 2: Validate session memory")
    validation = plugin.validate_session_memory()
    print(f"  Valid: {validation['valid']}")
    print(f"  Memory count: {validation['memories_count']}")
    if validation['errors']:
        print(f"  Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"  Warnings: {validation['warnings']}")
    
    # Test 3: Get statistics
    print("\nTest 3: Get statistics")
    stats = plugin.get_fix_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
