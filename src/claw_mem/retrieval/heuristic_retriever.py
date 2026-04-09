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
Heuristic Retriever

Provides time decay and heuristic rules to improve search relevance.
Part of the hybrid search strategy for MVP stage.
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from .time_parser import TimeExpressionParser
from .preference_detector import PreferenceDetector


@dataclass
class HeuristicConfig:
    """Configuration for heuristic rules."""
    # Time decay parameters
    time_decay_enabled: bool = True
    time_decay_half_life_days: float = 30.0  # Half-life in days
    time_decay_min_weight: float = 0.1  # Minimum time weight
    
    # Type matching parameters
    type_matching_enabled: bool = True
    type_keywords: Dict[str, List[str]] = None
    
    # Keyword importance parameters
    keyword_importance_enabled: bool = True
    important_keywords: List[str] = None
    
    # Score weights
    time_weight: float = 0.2
    type_weight: float = 0.2
    keyword_weight: float = 0.1
    
    def __post_init__(self):
        """Initialize default values."""
        if self.type_keywords is None:
            self.type_keywords = {
                "food": ["food", "eat", "meal", "restaurant", "cuisine", "dish", "pizza", "burger", "coffee", "tea"],
                "movie": ["movie", "film", "cinema", "watch", "actor", "director", "star wars", "matrix"],
                "music": ["music", "song", "listen", "band", "artist", "album", "concert"],
                "book": ["book", "read", "author", "novel", "story", "literature"],
                "hobby": ["hobby", "play", "game", "sport", "tennis", "football", "gaming"],
                "work": ["work", "job", "company", "project", "team", "office", "career"],
                "location": ["city", "country", "place", "live", "live in", "from", "location"],
                "person": ["name", "who", "person", "friend", "family", "colleague"],
            }
        
        if self.important_keywords is None:
            self.important_keywords = [
                "favorite", "prefer", "like", "love", "best", "top",
                "important", "key", "main", "primary", "essential"
            ]


class TimeDecayScorer:
    """
    Time Decay Scorer
    
    Calculates time-based relevance scores using exponential decay.
    More recent memories get higher scores.
    """
    
    def __init__(self, half_life_days: float = 30.0, min_weight: float = 0.1):
        """
        Initialize time decay scorer.
        
        Args:
            half_life_days: Half-life in days (default: 30 days)
            min_weight: Minimum time weight (default: 0.1)
        """
        self.half_life_days = half_life_days
        self.min_weight = min_weight
        self.decay_constant = 0.693147 / half_life_days  # ln(2) / half_life
    
    def calculate_score(self, memory: Dict) -> float:
        """
        Calculate time decay score for a memory.
        
        Args:
            memory: Memory record with timestamp
            
        Returns:
            Time decay score (0-1)
        """
        # Get timestamp
        timestamp_str = memory.get("timestamp")
        if not timestamp_str:
            return 0.5  # Default score for memories without timestamp
        
        try:
            # Parse timestamp
            if isinstance(timestamp_str, str):
                # Try ISO format
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif isinstance(timestamp_str, datetime):
                timestamp = timestamp_str
            else:
                return 0.5
            
            # Calculate age in days
            now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
            age = now - timestamp
            age_days = age.total_seconds() / 86400  # Convert to days
            
            # Calculate decay score
            decay_score = 2.718281828 ** (-self.decay_constant * age_days)
            
            # Apply minimum weight
            decay_score = max(decay_score, self.min_weight)
            
            return decay_score
            
        except (ValueError, TypeError, AttributeError):
            return 0.5  # Default score on error


class TypeMatcher:
    """
    Type Matcher
    
    Matches query types to memory content for improved relevance.
    """
    
    def __init__(self, type_keywords: Dict[str, List[str]]):
        """
        Initialize type matcher.
        
        Args:
            type_keywords: Dictionary mapping types to keywords
        """
        self.type_keywords = type_keywords
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build reverse index from keywords to types."""
        self.keyword_to_type = {}
        for type_name, keywords in self.type_keywords.items():
            for keyword in keywords:
                self.keyword_to_type[keyword.lower()] = type_name
    
    def detect_query_type(self, query: str) -> List[str]:
        """
        Detect type(s) from query.
        
        Args:
            query: Search query
            
        Returns:
            List of detected types
        """
        query_lower = query.lower()
        detected_types = set()
        
        for keyword, type_name in self.keyword_to_type.items():
            if keyword in query_lower:
                detected_types.add(type_name)
        
        return list(detected_types)
    
    def calculate_score(self, query: str, memory: Dict) -> float:
        """
        Calculate type matching score.
        
        Args:
            query: Search query
            memory: Memory record
            
        Returns:
            Type match score (0-1)
        """
        # Detect query types
        query_types = self.detect_query_type(query)
        
        if not query_types:
            return 0.5  # No type detected, neutral score
        
        # Check if memory content matches any type
        content_lower = memory.get("content", "").lower()
        
        for query_type in query_types:
            # Check if memory contains keywords of the same type
            type_keywords = self.type_keywords.get(query_type, [])
            for keyword in type_keywords:
                if keyword in content_lower:
                    return 1.0  # Type match found
        
        return 0.3  # Query has type but memory doesn't match


class KeywordImportanceScorer:
    """
    Keyword Importance Scorer
    
    Boosts scores for memories containing important keywords.
    """
    
    def __init__(self, important_keywords: List[str]):
        """
        Initialize keyword importance scorer.
        
        Args:
            important_keywords: List of important keywords
        """
        self.important_keywords = [kw.lower() for kw in important_keywords]
    
    def calculate_score(self, memory: Dict) -> float:
        """
        Calculate keyword importance score.
        
        Args:
            memory: Memory record
            
        Returns:
            Importance score (0-1)
        """
        content_lower = memory.get("content", "").lower()
        
        # Count important keywords
        count = sum(1 for kw in self.important_keywords if kw in content_lower)
        
        # Normalize to 0-1 range (max boost at 3+ keywords)
        return min(count / 3.0, 1.0)


class HeuristicRetriever:
    """
    Heuristic Retriever
    
    Combines BM25 + Entity Recognition + Time Decay + Type Matching + Keyword Importance.
    """
    
    def __init__(self, config: Optional[HeuristicConfig] = None):
        """
        Initialize heuristic retriever.
        
        Args:
            config: Heuristic configuration (uses defaults if None)
        """
        from .bm25_retriever import BM25Retriever
        from .entity_retriever import EntityRecognizer
        
        self.config = config or HeuristicConfig()
        self.bm25_retriever = BM25Retriever()
        self.entity_recognizer = EntityRecognizer(use_spacy=False)
        
        self.time_scorer = TimeDecayScorer(
            half_life_days=self.config.time_decay_half_life_days,
            min_weight=self.config.time_decay_min_weight
        )
        
        self.type_matcher = TypeMatcher(self.config.type_keywords)
        self.keyword_scorer = KeywordImportanceScorer(self.config.important_keywords)
    
    def search(self, query: str, memories: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Search memories with all heuristic rules applied.
        
        Args:
            query: Search query
            memories: List of memory records
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records sorted by combined score
        """
        # Stage 1: BM25 search
        bm25_results = self.bm25_retriever.search(
            query, memories, limit=limit * 3, rank_by_importance=False
        )
        
        # Stage 2: Calculate heuristic scores
        query_entities = set()
        if self.config.type_matching_enabled:
            try:
                entities = self.entity_recognizer.extract_entities(query)
                query_entities = {e.text.lower() for e in entities}
            except Exception:
                pass
        
        # Get max BM25 score for normalization
        max_bm25 = max((m.get("_bm25_score", 0) for m in bm25_results), default=0)
        
        # Calculate combined scores
        scored_results = []
        for memory in bm25_results:
            scores = {}
            
            # BM25 score (normalized)
            bm25_score = memory.get("_bm25_score", 0)
            scores["bm25"] = bm25_score / max_bm25 if max_bm25 > 0 else 0
            
            # Time decay score
            if self.config.time_decay_enabled:
                scores["time"] = self.time_scorer.calculate_score(memory)
            else:
                scores["time"] = 0.5
            
            # Type matching score
            if self.config.type_matching_enabled:
                scores["type"] = self.type_matcher.calculate_score(query, memory)
            else:
                scores["type"] = 0.5
            
            # Keyword importance score
            if self.config.keyword_importance_enabled:
                scores["keyword"] = self.keyword_scorer.calculate_score(memory)
            else:
                scores["keyword"] = 0.5
            
            # Entity matching score
            if query_entities:
                content = memory.get("content", "")
                try:
                    memory_entities = self.entity_recognizer.extract_entities(content)
                    memory_entity_texts = {e.text.lower() for e in memory_entities}
                    if memory_entity_texts:
                        intersection = query_entities & memory_entity_texts
                        union = query_entities | memory_entity_texts
                        scores["entity"] = len(intersection) / len(union) if union else 0
                    else:
                        scores["entity"] = 0
                except Exception:
                    scores["entity"] = 0
            else:
                scores["entity"] = 0.5
            
            # Calculate combined score
            combined_score = (
                0.3 * scores["bm25"] +
                self.config.time_weight * scores["time"] +
                self.config.type_weight * scores["type"] +
                self.config.keyword_weight * scores["keyword"] +
                0.2 * scores["entity"]
            )
            
            memory_copy = memory.copy()
            memory_copy["_scores"] = scores
            memory_copy["_combined_score"] = combined_score
            scored_results.append(memory_copy)
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x.get("_combined_score", 0), reverse=True)
        
        # Remove internal scores before returning
        for result in scored_results:
            result.pop("_scores", None)
            result.pop("_combined_score", None)
            result.pop("_bm25_score", None)
        
        return scored_results[:limit]


class SmartRetriever:
    """
    Smart Retriever
    
    Fully integrated retriever with all features:
    - BM25 relevance ranking
    - Entity recognition
    - Time decay
    - Type matching
    - Keyword importance
    - Importance ranking
    """
    
    def __init__(self, config: Optional[HeuristicConfig] = None):
        """
        Initialize smart retriever.
        
        Args:
            config: Heuristic configuration
        """
        from .bm25_retriever import HybridBM25Retriever
        from .entity_retriever import HybridEntityRetriever
        from ..importance import ImportanceScorer
        
        self.config = config or HeuristicConfig()
        self.heuristic_retriever = HeuristicRetriever(self.config)
        self.importance_scorer = ImportanceScorer()
    
    def search(self, query: str, memories: List[Dict], limit: int = 10,
               rank_by_importance: bool = True) -> List[Dict]:
        """
        Smart search with all features.
        
        Args:
            query: Search query
            memories: List of memory records
            limit: Number of results
            rank_by_importance: Apply importance ranking
            
        Returns:
            List[Dict]: Memory records sorted by relevance
        """
        # Get heuristic results
        results = self.heuristic_retriever.search(query, memories, limit=limit * 2)
        
        # Apply importance ranking if enabled
        if rank_by_importance and results:
            results = self.importance_scorer.rank_memories(results)
        
        return results[:limit]
