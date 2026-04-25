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
claw-mem Memory Links and Tags

Simple markdown-based linking and tagging system.
Maintains simplicity while adding association capabilities.

Syntax:
- Links: [[memory_id]] or [[2026-03-25#investment决策]]
- Tags: #tag or #tagname
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryLink:
    """Memory link"""
    source_id: str
    target_id: str
    link_type: str = "reference"  # reference, related, see_also
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "link_type": self.link_type,
            "created_at": self.created_at
        }


@dataclass
class MemoryTags:
    """Memory tags"""
    memory_id: str
    tags: Set[str] = field(default_factory=set)
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "tags": list(self.tags),
            "updated_at": self.updated_at
        }


class MemoryLinkParser:
    """
    Memory Link Parser
    
    Parses [[memory_id]] syntax from markdown content.
    """
    
    # Pattern: [[memory_id]] or [[date#title]]
    LINK_PATTERN = re.compile(r'\[\[([^\]]+)\]\]')
    
    def parse_links(self, content: str, source_id: str) -> List[MemoryLink]:
        """
        Parse links from content
        
        Args:
            content: Markdown content
            source_id: Source memory ID
            
        Returns:
            List[MemoryLink]: Parsed links
        """
        links = []
        
        for match in self.LINK_PATTERN.finditer(content):
            target = match.group(1).strip()
            
            # Parse target (could be memory_id or date#title)
            if '#' in target:
                # date#title format
                date_part, title_part = target.split('#', 1)
                target_id = f"{date_part}#{title_part}"
            else:
                # Simple memory_id
                target_id = target
            
            links.append(MemoryLink(
                source_id=source_id,
                target_id=target_id,
                link_type="reference"
            ))
        
        return links
    
    def remove_links(self, content: str) -> str:
        """
        Remove link syntax from content
        
        Args:
            content: Markdown content
            
        Returns:
            str: Content without link syntax
        """
        # Replace [[memory_id]] with memory_id
        return self.LINK_PATTERN.sub(r'\1', content)
    
    def extract_link_targets(self, content: str) -> List[str]:
        """
        Extract link targets from content
        
        Args:
            content: Markdown content
            
        Returns:
            List[str]: Link targets
        """
        return [
            match.group(1).strip()
            for match in self.LINK_PATTERN.finditer(content)
        ]


class MemoryTagParser:
    """
    Memory Tag Parser
    
    Parses #tag syntax from markdown content.
    """
    
    # Pattern: #tag or #tagname (Unicode supported)
    TAG_PATTERN = re.compile(r'#([a-zA-Z0-9\u4e00-\u9fa5_]+)')
    
    def parse_tags(self, content: str) -> Set[str]:
        """
        Parse tags from content
        
        Args:
            content: Markdown content
            
        Returns:
            Set[str]: Parsed tags
        """
        tags = set()
        
        for match in self.TAG_PATTERN.finditer(content):
            tag = match.group(1).strip()
            tags.add(tag.lower())  # Normalize to lowercase
        
        return tags
    
    def remove_tags(self, content: str) -> str:
        """
        Remove tag syntax from content
        
        Args:
            content: Markdown content
            
        Returns:
            str: Content without tag syntax
        """
        # Replace #tag with empty string
        return self.TAG_PATTERN.sub('', content)
    
    def extract_tags(self, content: str) -> Set[str]:
        """
        Extract tags from content
        
        Args:
            content: Markdown content
            
        Returns:
            Set[str]: Tags
        """
        return self.parse_tags(content)


class MemoryLinkManager:
    """
    Memory Link Manager
    
    Manages memory links and tags.
    """
    
    def __init__(self):
        """Initialize Link Manager"""
        self.link_parser = MemoryLinkParser()
        self.tag_parser = MemoryTagParser()
        
        # In-memory storage
        self.links: Dict[str, List[MemoryLink]] = {}  # source_id -> links
        self.tags: Dict[str, MemoryTags] = {}  # memory_id -> tags
        
        # Reverse index for tag search
        self.tag_index: Dict[str, Set[str]] = {}  # tag -> memory_ids
    
    def process_memory(
        self,
        memory_id: str,
        content: str
    ) -> Tuple[List[MemoryLink], Set[str]]:
        """
        Process a memory (extract links and tags)
        
        Args:
            memory_id: Memory ID
            content: Memory content
            
        Returns:
            Tuple: (links, tags)
        """
        # Extract links
        links = self.link_parser.parse_links(content, memory_id)
        
        # Extract tags
        tags = self.tag_parser.parse_tags(content)
        
        # Store links
        self.links[memory_id] = links
        
        # Store tags
        self._update_tags(memory_id, tags)
        
        return links, tags
    
    def _update_tags(self, memory_id: str, tags: Set[str]) -> None:
        """Update tags for a memory"""
        if memory_id in self.tags:
            # Remove from old tag index
            old_tags = self.tags[memory_id].tags
            for tag in old_tags:
                if tag in self.tag_index:
                    self.tag_index[tag].discard(memory_id)
        
        # Update tags
        self.tags[memory_id] = MemoryTags(
            memory_id=memory_id,
            tags=tags,
            updated_at=datetime.now().isoformat()
        )
        
        # Update tag index
        for tag in tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(memory_id)
    
    def get_linked_memories(self, memory_id: str) -> List[str]:
        """
        Get memories linked from a memory
        
        Args:
            memory_id: Memory ID
            
        Returns:
            List[str]: Linked memory IDs
        """
        if memory_id not in self.links:
            return []
        
        return [link.target_id for link in self.links[memory_id]]
    
    def get_backlinks(self, memory_id: str) -> List[str]:
        """
        Get memories that link to this memory
        
        Args:
            memory_id: Memory ID
            
        Returns:
            List[str]: Backlink memory IDs
        """
        backlinks = []
        
        for source_id, links in self.links.items():
            for link in links:
                if link.target_id == memory_id:
                    backlinks.append(source_id)
        
        return backlinks
    
    def search_by_tag(self, tag: str) -> List[str]:
        """
        Search memories by tag
        
        Args:
            tag: Tag name
            
        Returns:
            List[str]: Memory IDs with this tag
        """
        tag_lower = tag.lower()
        return list(self.tag_index.get(tag_lower, set()))
    
    def get_tags_for_memory(self, memory_id: str) -> Set[str]:
        """
        Get tags for a memory
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Set[str]: Tags
        """
        if memory_id not in self.tags:
            return set()
        
        return self.tags[memory_id].tags.copy()
    
    def get_all_tags(self) -> Set[str]:
        """
        Get all tags
        
        Returns:
            Set[str]: All tags
        """
        return set(self.tag_index.keys())
    
    def get_related_memories(
        self,
        memory_id: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get related memories (links + shared tags)
        
        Args:
            memory_id: Memory ID
            limit: Result limit
            
        Returns:
            List[str]: Related memory IDs
        """
        related = set()
        
        # Add linked memories
        linked = self.get_linked_memories(memory_id)
        related.update(linked)
        
        # Add backlinks
        backlinks = self.get_backlinks(memory_id)
        related.update(backlinks)
        
        # Add memories with shared tags
        my_tags = self.get_tags_for_memory(memory_id)
        for tag in my_tags:
            tagged_memories = self.search_by_tag(tag)
            related.update(tagged_memories)
        
        # Remove self
        related.discard(memory_id)
        
        # Return limited list
        return list(related)[:limit]
    
    def export_links(self) -> Dict:
        """
        Export links and tags
        
        Returns:
            Dict: Exported data
        """
        return {
            "links": {
                source: [link.to_dict() for link in links]
                for source, links in self.links.items()
            },
            "tags": {
                memory_id: tags.to_dict()
                for memory_id, tags in self.tags.items()
            },
            "tag_index": {
                tag: list(memories)
                for tag, memories in self.tag_index.items()
            }
        }
