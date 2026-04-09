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
Entity-Enhanced Retriever

Provides entity recognition and matching to improve search relevance.
Part of the hybrid search strategy for MVP stage.
"""

import re
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class Entity:
    """Represents a recognized entity."""
    text: str
    label: str  # PERSON, ORG, GPE, etc.
    start: int
    end: int


class EntityRecognizer:
    """
    Entity Recognizer
    
    Recognizes entities in text using spaCy or fallback regex patterns.
    """
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize entity recognizer.
        
        Args:
            use_spacy: Use spaCy for entity recognition (default: True)
        """
        self.use_spacy = use_spacy
        self.nlp = None
        
        if use_spacy:
            try:
                import spacy
                # Try to load English model
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    # Model not found, will use fallback
                    self.nlp = None
            except ImportError:
                # spaCy not installed, will use fallback
                self.nlp = None
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Extract entities from text.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of Entity objects
        """
        if self.nlp:
            # Use spaCy
            doc = self.nlp(text)
            entities = []
            for ent in doc.ents:
                entities.append(Entity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char
                ))
            return entities
        else:
            # Use fallback regex patterns
            return self._extract_entities_regex(text)
    
    def _extract_entities_regex(self, text: str) -> List[Entity]:
        """
        Fallback entity extraction using regex patterns.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of Entity objects
        """
        entities = []
        
        # Person names (capitalized words)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        for match in re.finditer(person_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="PERSON",
                start=match.start(),
                end=match.end()
            ))
        
        # Organizations (capitalized words followed by common org suffixes)
        org_pattern = r'\b[A-Z][a-zA-Z]+ (?:Inc|Corp|LLC|Ltd|Company|Co|Foundation)\b'
        for match in re.finditer(org_pattern, text):
            entities.append(Entity(
                text=match.group(),
                label="ORG",
                start=match.start(),
                end=match.end()
            ))
        
        # Locations (capitalized words)
        gpe_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
        for match in re.finditer(gpe_pattern, text):
            # Skip if already captured as person or org
            text_snippet = match.group()
            if not any(e.text == text_snippet for e in entities):
                entities.append(Entity(
                    text=text_snippet,
                    label="GPE",
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def get_entity_types(self) -> List[str]:
        """
        Get list of supported entity types.
        
        Returns:
            List of entity type labels
        """
        if self.nlp:
            # spaCy entity types
            return ["PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", 
                    "WORK_OF_ART", "LAW", "LANGUAGE", "DATE", "TIME",
                    "PERCENT", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL"]
        else:
            # Fallback entity types
            return ["PERSON", "ORG", "GPE"]


class EntityEnhancedRetriever:
    """
    Entity-Enhanced Retriever
    
    Combines BM25 with entity recognition for improved relevance.
    """
    
    def __init__(self, use_spacy: bool = True,
                 entity_weight: float = 0.3,
                 bm25_weight: float = 0.7):
        """
        Initialize entity-enhanced retriever.
        
        Args:
            use_spacy: Use spaCy for entity recognition
            entity_weight: Weight for entity matching score
            bm25_weight: Weight for BM25 score
        """
        from .bm25_retriever import BM25Retriever
        
        self.entity_recognizer = EntityRecognizer(use_spacy=use_spacy)
        self.bm25_retriever = BM25Retriever()
        self.entity_weight = entity_weight
        self.bm25_weight = bm25_weight
        
        # Cache for entity extraction
        self._entity_cache: Dict[str, Set[str]] = {}
    
    def extract_and_cache_entities(self, text: str) -> Set[str]:
        """
        Extract entities from text and cache them.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Set of entity texts (lowercase)
        """
        # Check cache
        cache_key = text[:100]  # Use first 100 chars as key
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key]
        
        # Extract entities
        entities = self.entity_recognizer.extract_entities(text)
        entity_texts = {e.text.lower() for e in entities}
        
        # Cache (limit cache size)
        if len(self._entity_cache) < 1000:
            self._entity_cache[cache_key] = entity_texts
        
        return entity_texts
    
    def calculate_entity_score(self, query_entities: Set[str], 
                               memory_entities: Set[str]) -> float:
        """
        Calculate entity match score.
        
        Args:
            query_entities: Entities in query
            memory_entities: Entities in memory
            
        Returns:
            Entity match score (0-1)
        """
        if not query_entities or not memory_entities:
            return 0.0
        
        # Jaccard similarity
        intersection = query_entities & memory_entities
        union = query_entities | memory_entities
        
        return len(intersection) / len(union) if union else 0.0
    
    def search(self, query: str, memories: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Search memories with entity-enhanced scoring.
        
        Args:
            query: Search query
            memories: List of memory records
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records sorted by combined score
        """
        # Extract entities from query
        query_entities = self.extract_and_cache_entities(query)
        
        # Get BM25 results
        bm25_results = self.bm25_retriever.search(
            query, memories, limit=limit * 3, rank_by_importance=False
        )
        
        # Calculate entity scores for each result
        scored_results = []
        for memory in bm25_results:
            content = memory.get("content", "")
            memory_entities = self.extract_and_cache_entities(content)
            
            # Calculate entity match score
            entity_score = self.calculate_entity_score(query_entities, memory_entities)
            
            # Get BM25 score (normalized)
            bm25_score = memory.get("_bm25_score", 0)
            if bm25_results:
                max_bm25 = max(m.get("_bm25_score", 0) for m in bm25_results)
                if max_bm25 > 0:
                    bm25_score = bm25_score / max_bm25
            
            # Combine scores
            combined_score = (
                self.bm25_weight * bm25_score +
                self.entity_weight * entity_score
            )
            
            memory_copy = memory.copy()
            memory_copy["_combined_score"] = combined_score
            memory_copy["_entity_score"] = entity_score
            memory_copy["_bm25_score_normalized"] = bm25_score
            scored_results.append(memory_copy)
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x.get("_combined_score", 0), reverse=True)
        
        # Remove internal scores before returning
        for result in scored_results:
            result.pop("_combined_score", None)
            result.pop("_entity_score", None)
            result.pop("_bm25_score_normalized", None)
        
        return scored_results[:limit]


class HybridEntityRetriever:
    """
    Hybrid Retriever combining BM25 + Entity Recognition + Keyword matching.
    
    Three-stage retrieval:
    1. BM25 for relevance ranking
    2. Entity matching for semantic boost
    3. Keyword matching as fallback
    """
    
    def __init__(self, use_spacy: bool = True,
                 bm25_weight: float = 0.5,
                 entity_weight: float = 0.3,
                 keyword_weight: float = 0.2):
        """
        Initialize hybrid retriever.
        
        Args:
            use_spacy: Use spaCy for entity recognition
            bm25_weight: Weight for BM25 score
            entity_weight: Weight for entity match score
            keyword_weight: Weight for keyword match score
        """
        from .bm25_retriever import BM25Retriever
        
        self.entity_recognizer = EntityRecognizer(use_spacy=use_spacy)
        self.bm25_retriever = BM25Retriever()
        self.bm25_weight = bm25_weight
        self.entity_weight = entity_weight
        self.keyword_weight = keyword_weight
        
        self._entity_cache: Dict[str, Set[str]] = {}
    
    def extract_entities_cached(self, text: str) -> Set[str]:
        """Extract and cache entities."""
        cache_key = text[:100]
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key]
        
        entities = self.entity_recognizer.extract_entities(text)
        entity_texts = {e.text.lower() for e in entities}
        
        if len(self._entity_cache) < 1000:
            self._entity_cache[cache_key] = entity_texts
        
        return entity_texts
    
    def search(self, query: str, memories: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Search using hybrid approach.
        
        Args:
            query: Search query
            memories: List of memory records
            limit: Number of results
            
        Returns:
            List[Dict]: Memory records
        """
        # Stage 1: BM25 search
        bm25_results = self.bm25_retriever.search(
            query, memories, limit=limit * 3, rank_by_importance=False
        )
        
        # Stage 2: Entity matching
        query_entities = self.extract_entities_cached(query)
        
        # Stage 3: Keyword matching
        query_lower = query.lower()
        keyword_matches = []
        for memory in memories:
            content = memory.get("content", "").lower()
            if query_lower in content:
                keyword_matches.append(memory)
        
        # Combine scores
        result_scores = {}
        max_bm25 = max((m.get("_bm25_score", 0) for m in bm25_results), default=0)
        
        # BM25 scores
        for idx, memory in enumerate(bm25_results):
            memory_id = memory.get("id", idx)
            bm25_score = memory.get("_bm25_score", 0)
            normalized_bm25 = bm25_score / max_bm25 if max_bm25 > 0 else 0
            result_scores[memory_id] = result_scores.get(memory_id, 0) + self.bm25_weight * normalized_bm25
        
        # Entity scores
        for idx, memory in enumerate(bm25_results):
            memory_id = memory.get("id", idx)
            content = memory.get("content", "")
            memory_entities = self.extract_entities_cached(content)
            
            if query_entities and memory_entities:
                intersection = query_entities & memory_entities
                union = query_entities | memory_entities
                entity_score = len(intersection) / len(union) if union else 0
                result_scores[memory_id] = result_scores.get(memory_id, 0) + self.entity_weight * entity_score
        
        # Keyword scores
        for idx, memory in enumerate(keyword_matches):
            memory_id = memory.get("id", idx)
            keyword_score = (len(keyword_matches) - idx) / len(keyword_matches) if keyword_matches else 0
            result_scores[memory_id] = result_scores.get(memory_id, 0) + self.keyword_weight * keyword_score
        
        # Sort by combined score
        sorted_ids = sorted(result_scores.keys(), key=lambda x: result_scores[x], reverse=True)
        
        # Build final results
        id_to_memory = {m.get("id", idx): m for idx, m in enumerate(memories)}
        final_results = [id_to_memory[mid] for mid in sorted_ids if mid in id_to_memory]
        
        return final_results[:limit]
