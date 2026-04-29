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


class HybridSearcher:
    """Hybrid Searcher

    Combines BM25 keyword search with semantic embedding search
    using weighted scoring and reciprocal rank fusion

    Features:
    - Configurable BM25/Semantic weight
    - Reciprocal Rank Fusion
    - Query preprocessing
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        semantic_weight: float = 0.5,
        semantic_top_k: int = 20,
        use_rrf: bool = True,
        rrf_k: int = 60
    ):
        """Initialize hybrid searcher

        Args:
            bm25_weight: Weight for BM25 scores (0-1)
            semantic_weight: Weight for semantic scores (0-1)
            semantic_top_k: Top-k for semantic search
            use_rrf: Use Reciprocal Rank Fusion
            rrf_k: RRF parameter (default 60)
        """
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.semantic_top_k = semantic_top_k
        self.use_rrf = use_rrf
        self.rrf_k = rrf_k

        self.bm25 = BM25Retriever()
        self.semantic = SemanticRetriever(top_k=semantic_top_k)

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
        self.bm25.add_document(id, text, metadata)
        self.semantic.add(id, text, metadata)

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
        # Get BM25 results
        bm25_results = self.bm25.search(query, top_k=self.semantic_top_k)
        bm25_dict = {
            r["id"]: r["score"]
            for r in bm25_results
            if r["score"] >= bm25_threshold
        }

        # Get semantic results
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
            # Get text and metadata from semantic index
            doc = self.semantic.get(id)
            if doc:
                results.append({
                    "id": id,
                    "text": doc["text"],
                    "score": score,
                    "metadata": doc.get("metadata", {}),
                    "bm25_score": bm25_dict.get(id, 0),
                    "semantic_score": semantic_dict.get(id, 0)
                })

        # Sort by combined score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

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
        self.bm25.clear()
        self.semantic.clear()

    def count(self) -> int:
        """Get number of indexed documents"""
        return self.semantic.count()


# Default instance
_hybrid_searcher: Optional[HybridSearcher] = None


def get_hybrid_searcher(
    bm25_weight: float = 0.5,
    semantic_weight: float = 0.5,
    top_k: int = 10
) -> HybridSearcher:
    """Get global hybrid searcher instance"""
    global _hybrid_searcher

    if _hybrid_searcher is None:
        _hybrid_searcher = HybridSearcher(
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight,
            semantic_top_k=top_k * 2
        )

    return _hybrid_searcher
