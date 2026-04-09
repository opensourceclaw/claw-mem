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
Enhanced Smart Retriever

Fully integrated retriever with all features including time parsing and preference detection.
"""

from typing import List, Dict, Optional
from .heuristic_retriever import HeuristicRetriever, HeuristicConfig
from .time_parser import TimeExpressionParser
from .preference_detector import PreferenceDetector
from ..importance import ImportanceScorer


class EnhancedSmartRetriever:
    """
    Enhanced Smart Retriever
    
    Fully integrated retriever with all features:
    - BM25 relevance ranking
    - Entity recognition
    - Time decay
    - Type matching
    - Keyword importance
    - Time expression parsing
    - Preference detection
    - Importance ranking
    """
    
    def __init__(self, config: Optional[HeuristicConfig] = None):
        """
        Initialize enhanced smart retriever.
        
        Args:
            config: Heuristic configuration
        """
        self.config = config or HeuristicConfig()
        self.heuristic_retriever = HeuristicRetriever(self.config)
        self.importance_scorer = ImportanceScorer()
        self.time_parser = TimeExpressionParser()
        self.preference_detector = PreferenceDetector()
    
    def search(self, query: str, memories: List[Dict], limit: int = 10,
               rank_by_importance: bool = True) -> List[Dict]:
        """
        Enhanced smart search with all features.
        
        Args:
            query: Search query
            memories: List of memory records
            limit: Number of results
            rank_by_importance: Apply importance ranking
            
        Returns:
            List[Dict]: Memory records sorted by relevance
        """
        # Check if query is about time
        is_time_query = self.time_parser.is_time_query(query)
        
        # Check if query is about preferences
        is_preference_query = self.preference_detector.is_preference_query(query)
        
        # Get heuristic results
        results = self.heuristic_retriever.search(query, memories, limit=limit * 2)
        
        # Apply time filtering if query is about time
        if is_time_query and results:
            time_range = self.time_parser.parse(query)
            if time_range:
                start_time, end_time = time_range
                # Filter by time range
                filtered = []
                for memory in results:
                    timestamp_str = memory.get("timestamp")
                    if timestamp_str:
                        try:
                            from datetime import datetime
                            if isinstance(timestamp_str, str):
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            elif isinstance(timestamp_str, datetime):
                                timestamp = timestamp_str
                            else:
                                continue
                            
                            if start_time <= timestamp <= end_time:
                                filtered.append(memory)
                        except:
                            pass
                
                # If we have filtered results, use them; otherwise keep all
                if filtered:
                    results = filtered
        
        # Apply preference boost if query is about preferences
        if is_preference_query and results:
            for memory in results:
                boost = self.preference_detector.get_preference_boost(query, memory)
                if boost > 0:
                    # Add preference boost to memory metadata
                    if "_preference_boost" not in memory:
                        memory["_preference_boost"] = boost
            
            # Re-sort by preference boost
            results.sort(key=lambda x: x.get("_preference_boost", 0), reverse=True)
        
        # Apply importance ranking if enabled
        if rank_by_importance and results:
            results = self.importance_scorer.rank_memories(results)
        
        # Clean up internal metadata
        for result in results:
            result.pop("_preference_boost", None)
        
        return results[:limit]
