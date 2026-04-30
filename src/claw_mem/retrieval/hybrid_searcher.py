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
Hybrid Searcher for claw-mem v2.5.0
Combines BM25 (keyword) + Semantic (embedding) search
"""

from typing import List, Optional, Dict, Any, Tuple
import math

from .bm25_retriever import BM25Retriever
from .semantic_retriever import SemanticRetriever
from .query_cache import get_query_cache


class HybridSearcher:
    """Hybrid Searcher

    Combines BM25 keyword search with semantic embedding search
    using weighted scoring and reciprocal rank fusion

    Features:
    - Configurable BM25/Semantic weight
    - Reciprocal Rank Fusion
    - Query preprocessing
    - Result caching
    """

    def __init__(
        self,
        bm25_weight: float = 1.0,
        semantic_weight: float = 0.0,
        semantic_top_k: int = 20,
        use_rrf: bool = True,
        rrf_k: int = 60,
        use_cache: bool = True,
        recency_boost: float = 0.1,
        frequency_boost: float = 0.05
    ):
        """Initialize hybrid searcher

        Args:
            bm25_weight: Weight for BM25 scores (0-1)
            semantic_weight: Weight for semantic scores (0-1, default 0 = disabled)
            semantic_top_k: Top-k for semantic search
            use_rrf: Use Reciprocal Rank Fusion
            rrf_k: RRF parameter (default 60)
            use_cache: Use query result caching
            recency_boost: Boost score for recent memories (0-0.3)
            frequency_boost: Boost score for frequent accesses (0-0.2)
        """
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.semantic_top_k = semantic_top_k
        self.use_rrf = use_rrf
        self.rrf_k = rrf_k
        self.use_cache = use_cache
        self.recency_boost = recency_boost
        self.frequency_boost = frequency_boost

        self.bm25 = BM25Retriever()
        self.semantic = SemanticRetriever(top_k=semantic_top_k)
        self._documents: List[Dict[str, Any]] = []

        # Access tracking for frequency boost
        self._access_counts: Dict[str, int] = {}
        self._access_times: Dict[str, float] = {}

        # Cache
        if self.use_cache:
            self._cache = get_query_cache()
        else:
            self._cache = None

    def index_document(
        self,
        id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add document to both indexes

        Args:
            id: Unique document ID
            text: Document text
            metadata: Additional metadata
        """
        # Store in semantic index (may fail if no provider)
        try:
            self.semantic.add(id, text, metadata)
        except Exception:
            pass  # Skip semantic if no provider

        # For BM25, we need to rebuild index with all documents
        # Store documents for later search
        if not hasattr(self, '_documents'):
            self._documents = []
        self._documents.append({
            "id": id,
            "content": text,
            "metadata": metadata or {}
        })

        # Rebuild BM25 index
        self.bm25.build_index(self._documents)

    def search(
        self,
        query: str,
        top_k: int = 10,
        bm25_threshold: float = 0.0,
        semantic_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Hybrid search

        Args:
            query: Search query
            top_k: Number of results
            bm25_threshold: Minimum BM25 score
            semantic_threshold: Minimum semantic score
            filters: Filter by metadata

        Returns:
            List of ranked results
        """
        # Quick check: if no documents, return empty
        if not self._documents:
            return []

        # Get BM25 results (use position as score)
        bm25_results = self.bm25.search(query, self._documents, limit=self.semantic_top_k)
        bm25_dict = {}
        for idx, r in enumerate(bm25_results):
            # Use reverse rank as score
            bm25_dict[r.get("id", idx)] = (len(bm25_results) - idx) / len(bm25_results) if bm25_results else 0

        # Get semantic results
        try:
            semantic_results = self.semantic.search(
                query,
                top_k=self.semantic_top_k,
                score_threshold=semantic_threshold,
                filters=filters
            )
            semantic_dict = {
                r["id"]: r["score"]
                for r in semantic_results
            }
        except Exception:
            semantic_dict = {}

        # Get all document IDs
        all_ids = set(bm25_dict.keys()) | set(semantic_dict.keys())

        if not all_ids:
            return []

        if self.use_rrf:
            # Reciprocal Rank Fusion
            scores = self._reciprocal_rank_fusion(bm25_dict, semantic_dict)
        else:
            # Weighted combination
            scores = self._weighted_combination(bm25_dict, semantic_dict)

        # Build result list
        results = []
        for id, score in scores.items():
            # Get text and metadata from stored documents
            doc = next((d for d in self._documents if d["id"] == id), None)
            if doc:
                results.append({
                    "id": id,
                    "text": doc["content"],
                    "score": score,
                    "metadata": doc.get("metadata", {}),
                    "bm25_score": bm25_dict.get(id, 0),
                    "semantic_score": semantic_dict.get(id, 0)
                })

        # Apply recency and frequency boost
        if self.recency_boost > 0 or self.frequency_boost > 0:
            import time
            now = time.time()
            results = self._apply_boosts(results, now)

        # Sort by combined score
        results.sort(key=lambda x: x["score"], reverse=True)
        final_results = results[:top_k]

        # Cache results
        if self._cache:
            self._cache.put(query, results, top_k)

        # Track access for frequency boost
        import time
        now = time.time()
        for result in final_results:
            doc_id = result["id"]
            self._access_counts[doc_id] = self._access_counts.get(doc_id, 0) + 1
            self._access_times[doc_id] = now

        return final_results

    def _apply_boosts(self, results: List[Dict[str, Any]], now: float) -> List[Dict[str, Any]]:
        """Apply recency and frequency boosts

        Args:
            results: Search results
            now: Current timestamp

        Returns:
            Results with boosted scores
        """
        if not results:
            return results

        # Calculate max age for normalization
        max_age = 1.0  # 1 day
        access_times = list(self._access_times.values())
        if access_times:
            max_age = max(now - min(access_times), 1.0)

        max_access = max(self._access_counts.values()) if self._access_counts else 1

        for result in results:
            doc_id = result["id"]
            boost = 0.0

            # Recency boost (newer = higher boost)
            if doc_id in self._access_times:
                age = now - self._access_times[doc_id]
                recency_score = max(0, 1 - age / max_age)
                boost += self.recency_boost * recency_score

            # Frequency boost (more frequent = higher boost)
            if doc_id in self._access_counts:
                freq_score = self._access_counts[doc_id] / max_access
                boost += self.frequency_boost * freq_score

            result["score"] += boost

        return results

    def _reciprocal_rank_fusion(
        self,
        bm25_scores: Dict[str, float],
        semantic_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Reciprocal Rank Fusion

        RRF score = sum(1 / (k + rank)) for each ranker
        """
        # Get ranked lists
        bm25_ranked = sorted(bm25_scores.keys(), key=lambda x: bm25_scores[x], reverse=True)
        semantic_ranked = sorted(semantic_scores.keys(), key=lambda x: semantic_scores[x], reverse=True)

        # Calculate RRF scores
        rrf_scores = {}
        all_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())

        for id in all_ids:
            score = 0

            # BM25 contribution
            if id in bm25_ranked:
                rank = bm25_ranked.index(id) + 1
                score += 1.0 / (self.rrf_k + rank)

            # Semantic contribution
            if id in semantic_ranked:
                rank = semantic_ranked.index(id) + 1
                score += 1.0 / (self.rrf_k + rank)

            rrf_scores[id] = score

        return rrf_scores

    def _weighted_combination(
        self,
        bm25_scores: Dict[str, float],
        semantic_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Weighted score combination"""
        # Normalize scores
        max_bm25 = max(bm25_scores.values()) if bm25_scores else 1
        max_semantic = max(semantic_scores.values()) if semantic_scores else 1

        combined = {}
        all_ids = set(bm25_scores.keys()) | set(semantic_scores.keys())

        for id in all_ids:
            bm25_norm = bm25_scores.get(id, 0) / max_bm25 if max_bm25 > 0 else 0
            semantic_norm = semantic_scores.get(id, 0) / max_semantic if max_semantic > 0 else 0

            combined[id] = (
                self.bm25_weight * bm25_norm +
                self.semantic_weight * semantic_norm
            )

        return combined

    def clear(self):
        """Clear all indexes"""
        self._documents = []
        self._access_counts = {}
        self._access_times = {}
        if self._cache:
            self._cache.invalidate()

    def count(self) -> int:
        """Get number of indexed documents"""
        return self.semantic.count()


# Default instance
_hybrid_searcher: Optional[HybridSearcher] = None


def get_hybrid_searcher(
    bm25_weight: float = 1.0,
    semantic_weight: float = 0.0,
    top_k: int = 10
) -> HybridSearcher:
    """Get global hybrid searcher instance (BM25-only by default)"""
    global _hybrid_searcher

    if _hybrid_searcher is None:
        _hybrid_searcher = HybridSearcher(
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
            semantic_top_k=top_k * 2
        )

    return _hybrid_searcher
