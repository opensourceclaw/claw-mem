"""
Keyword Retriever (MVP Version)

Provides basic keyword search functionality with importance ranking.
"""

from typing import List, Dict, Optional
from ..importance import ImportanceScorer


class KeywordRetriever:
    """
    Keyword Retriever
    
    MVP version supports keyword matching only. Semantic search will be added in future iterations.
    """
    
    def __init__(self):
        """Initialize retriever with importance scorer"""
        self.scorer = ImportanceScorer()
    
    def search(self, query: str, episodic, semantic, procedural,
               memory_type: Optional[str] = None, limit: int = 10,
               rank_by_importance: bool = True) -> List[Dict]:
        """
        Retrieve memories
        
        Args:
            query: Search query
            episodic: Episodic storage
            semantic: Semantic storage
            procedural: Procedural storage
            memory_type: Memory type filter
            limit: Number of results
            rank_by_importance: Sort by importance score (default: True)
            
        Returns:
            List[Dict]: Memory records (sorted by importance if enabled)
        """
        results = []
        query_lower = query.lower()
        
        # Retrieve based on type
        if memory_type is None or memory_type == "episodic":
            for memory in episodic.get_recent(limit * 2):
                if self._match(query_lower, memory):
                    results.append(memory)
        
        if memory_type is None or memory_type == "semantic":
            for memory in semantic.get_all():
                if self._match(query_lower, memory):
                    results.append(memory)
        
        if memory_type is None or memory_type == "procedural":
            for memory in procedural.get_all():
                if self._match(query_lower, memory):
                    results.append(memory)
        
        # Sort by importance if enabled
        if rank_by_importance and results:
            results = self.scorer.rank_memories(results)
        
        # Limit results
        return results[:limit]
        
        # Sort and return
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results[:limit]
    
    def _match(self, query_lower: str, memory: Dict) -> bool:
        """
        Check if memory matches query
        
        Args:
            query_lower: Lowercase query
            memory: Memory record
            
        Returns:
            bool: Match status
        """
        content = memory.get("content", "").lower()
        tags = [tag.lower() for tag in memory.get("tags", [])]
        
        # Check if content contains query (support both English and Chinese)
        if query_lower in content:
            return True
        
        # Check if tags match
        for tag in tags:
            if query_lower in tag:
                return True
        
        # Check individual characters for Chinese queries
        # This helps match "语言" in "用户偏好使用中文交流"
        if any(char in content for char in query_lower if '\u4e00' <= char <= '\u9fff'):
            return True
        
        return False
