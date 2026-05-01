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
BM25 Retriever

Provides BM25-based search functionality for improved relevance ranking.
Part of the hybrid search strategy for MVP stage.

v2.7.0: Added configurable parameters, recency_boost, frequency_boost,
and version-based incremental rebuild detection.
"""

import re
import time as _time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from rank_bm25 import BM25Okapi
from ..importance import ImportanceScorer


class BM25Retriever:
    """
    BM25 Retriever

    Uses BM25 algorithm for better relevance ranking compared to simple keyword matching.
    Supports both English and Chinese text.

    v2.7.0 parameters:
        k1: BM25 term frequency saturation (default 1.5)
        b: BM25 document length normalization (default 0.75)
        recency_boost: Weight multiplier for recent memories (default 1.0 = off)
        frequency_boost: Weight multiplier for frequently accessed memories (default 1.0 = off)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75,
                 recency_boost: float = 1.0, frequency_boost: float = 1.0):
        self.k1 = k1
        self.b = b
        self.recency_boost = recency_boost
        self.frequency_boost = frequency_boost
        self.scorer = ImportanceScorer()
        self._corpus: List[List[str]] = []
        self._memories: List[Dict] = []
        self._bm25: Optional[BM25Okapi] = None
        self._index_version: int = -1  # Version counter for incremental rebuild detection
        self._access_counts: Dict[str, int] = {}
        self._access_times: Dict[str, float] = {}
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Supports both English and Chinese.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Lowercase
        text = text.lower()
        
        # Split on whitespace and punctuation for English
        tokens = re.findall(r'\b\w+\b', text)
        
        # For Chinese, split into individual characters
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        tokens.extend(chinese_chars)
        
        return tokens
    
    def build_index(self, memories: List[Dict], force: bool = False) -> None:
        """
        Build BM25 index from memories.

        Uses version-based incremental detection: only rebuilds when memory
        count changes, avoiding redundant rebuilds on identical inputs.

        Args:
            memories: List of memory records
            force: Force rebuild even if count unchanged
        """
        new_version = len(memories)
        if not force and self._bm25 and new_version == self._index_version:
            return  # No change, skip rebuild

        self._memories = memories
        self._index_version = new_version
        self._corpus = []

        for memory in memories:
            content = memory.get("content", "")
            tags = " ".join(memory.get("tags", []))
            text = f"{content} {tags}"
            tokens = self.tokenize(text)
            self._corpus.append(tokens)

        if self._corpus:
            self._bm25 = BM25Okapi(self._corpus, k1=self.k1, b=self.b)

    def _apply_boosts(self, result: Dict, bm25_score: float) -> float:
        """Apply recency and frequency boosts to a BM25 score."""
        score = bm25_score
        if self.recency_boost > 1.0:
            ts = result.get("timestamp")
            if ts:
                try:
                    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    days_ago = (_time.time() - dt.timestamp()) / 86400
                    if days_ago < 1:
                        score *= self.recency_boost
                    elif days_ago < 7:
                        score *= 1.0 + (self.recency_boost - 1.0) * 0.5
                except (ValueError, TypeError):
                    pass
        if self.frequency_boost > 1.0:
            count = result.get("access_count", 0)
            if count > 3:
                score *= self.frequency_boost
        return score
    
    def search(self, query: str, memories: List[Dict], limit: int = 10,
               rank_by_importance: bool = True,
               min_score: float = 0.0) -> List[Dict]:
        """
        Search memories using BM25 algorithm.
        
        Args:
            query: Search query
            memories: List of memory records to search
            limit: Number of results
            rank_by_importance: Sort by importance score (default: True)
            min_score: Minimum BM25 score threshold
            
        Returns:
            List[Dict]: Memory records sorted by relevance
        """
        # Build index with version-based incremental detection
        self.build_index(memories)

        if not self._bm25 or not self._corpus:
            return []

        # Tokenize query
        query_tokens = self.tokenize(query)

        if not query_tokens:
            return []

        # Get BM25 scores
        scores = self._bm25.get_scores(query_tokens)

        # Create scored results with optional recency/frequency boosts
        scored_results = []
        for idx, score in enumerate(scores):
            if score > min_score:
                memory = self._memories[idx].copy()
                boosted = self._apply_boosts(memory, float(score))
                memory["_bm25_score"] = boosted
                scored_results.append(memory)

        # Sort by (boosted) BM25 score
        scored_results.sort(key=lambda x: x.get("_bm25_score", 0), reverse=True)
        
        # Apply importance ranking if enabled
        if rank_by_importance and scored_results:
            scored_results = self.scorer.rank_memories(scored_results)
        
        # Remove internal score before returning
        for result in scored_results:
            result.pop("_bm25_score", None)
        
        return scored_results[:limit]
    
    def get_top_k_tokens(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Get top-k most important tokens for a query.
        
        This can be useful for understanding what the BM25 algorithm is focusing on.
        
        Args:
            query: Search query
            top_k: Number of top tokens
            
        Returns:
            List of (token, idf_score) tuples
        """
        if not self._bm25:
            return []
        
        query_tokens = self.tokenize(query)
        
        # Get IDF scores for query tokens
        token_scores = []
        for token in query_tokens:
            if token in self._bm25.idf:
                token_scores.append((token, float(self._bm25.idf[token])))
        
        # Sort by IDF score
        token_scores.sort(key=lambda x: x[1], reverse=True)
        
        return token_scores[:top_k]
    
    def explain(self, query: str, memory_idx: int) -> Dict:
        """
        Explain why a memory was matched.
        
        Args:
            query: Search query
            memory_idx: Index of memory in the corpus
            
        Returns:
            Dict with explanation
        """
        if not self._bm25 or memory_idx >= len(self._corpus):
            return {"error": "Invalid index or empty corpus"}
        
        query_tokens = self.tokenize(query)
        doc_tokens = self._corpus[memory_idx]
        
        # Calculate individual token scores
        token_scores = {}
        for token in query_tokens:
            if token in doc_tokens:
                # Simplified BM25 score calculation for explanation
                tf = doc_tokens.count(token)
                idf = float(self._bm25.idf.get(token, 0))
                doc_len = len(doc_tokens)
                avgdl = self._bm25.avgdl
                
                # BM25 formula
                numerator = idf * tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avgdl)
                score = numerator / denominator
                
                token_scores[token] = {
                    "tf": tf,
                    "idf": idf,
                    "score": score
                }
        
        return {
            "query_tokens": query_tokens,
            "doc_tokens": doc_tokens[:20],  # First 20 tokens
            "token_scores": token_scores,
            "total_score": sum(t["score"] for t in token_scores.values())
        }


class HybridBM25Retriever:
    """
    Hybrid Retriever combining BM25 with keyword matching.
    
    Uses BM25 for relevance ranking and keyword matching as a fallback.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75,
                 bm25_weight: float = 0.7, keyword_weight: float = 0.3,
                 recency_boost: float = 1.0, frequency_boost: float = 1.0):
        """
        Initialize hybrid retriever.

        Args:
            k1: BM25 k1 parameter
            b: BM25 b parameter
            bm25_weight: Weight for BM25 scores
            keyword_weight: Weight for keyword matching
            recency_boost: Weight multiplier for recent memories
            frequency_boost: Weight multiplier for frequently accessed memories
        """
        self.bm25_retriever = BM25Retriever(
            k1=k1, b=b,
            recency_boost=recency_boost,
            frequency_boost=frequency_boost
        )
        self.bm25_weight = bm25_weight
        self.keyword_weight = keyword_weight
    
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
        # Get BM25 results
        bm25_results = self.bm25_retriever.search(
            query, memories, limit=limit * 2, rank_by_importance=False
        )
        
        # Keyword matching for fallback
        keyword_results = []
        query_lower = query.lower()
        for memory in memories:
            content = memory.get("content", "").lower()
            if query_lower in content:
                keyword_results.append(memory)
        
        # Merge results with weighted scoring
        result_scores = {}
        for idx, result in enumerate(bm25_results):
            memory_id = result.get("id", idx)
            bm25_score = (len(bm25_results) - idx) / len(bm25_results) if bm25_results else 0
            result_scores[memory_id] = result_scores.get(memory_id, 0) + self.bm25_weight * bm25_score
        
        for idx, result in enumerate(keyword_results):
            memory_id = result.get("id", idx)
            keyword_score = (len(keyword_results) - idx) / len(keyword_results) if keyword_results else 0
            result_scores[memory_id] = result_scores.get(memory_id, 0) + self.keyword_weight * keyword_score
        
        # Sort by combined score
        sorted_ids = sorted(result_scores.keys(), key=lambda x: result_scores[x], reverse=True)
        
        # Build final results
        id_to_memory = {m.get("id", idx): m for idx, m in enumerate(memories)}
        final_results = [id_to_memory[mid] for mid in sorted_ids if mid in id_to_memory]
        
        return final_results[:limit]
