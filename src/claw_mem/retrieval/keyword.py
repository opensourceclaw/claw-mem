"""
Keyword Retriever (MVP Version)

Provides basic keyword search functionality.
"""

from typing import List, Dict, Optional


class KeywordRetriever:
    """
    Keyword Retriever
    
    MVP version supports keyword matching only. Semantic search will be added in future iterations.
    """
    
    def search(self, query: str, episodic, semantic, procedural,
               memory_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Retrieve memories
        
        Args:
            query: Search query
            episodic: Episodic storage
            semantic: Semantic storage
            procedural: Procedural storage
            memory_type: Memory type filter
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records
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
        
        # Check if content contains query
        if query_lower in content:
            return True
        
        # Check if tags match
        for tag in tags:
            if query_lower in tag:
                return True
        
        return False
