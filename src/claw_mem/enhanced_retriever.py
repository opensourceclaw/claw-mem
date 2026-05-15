"""Enhanced Retriever — BM25 + semantic hybrid with recency/frequency boosting for claw-mem v2.15.0."""

import logging
import math
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EnhancedRetriever:
    """Hybrid retriever with BM25 weighting, semantic recall, and recency boost.

    Targets >95% retrieval accuracy through:
    - Higher BM25 weight (0.7) for exact matching
    - Recency boost (1.5x) for recent memories
    - Frequency boost (1.2x) for frequently accessed memories
    """

    def __init__(self, bm25_weight: float = 0.7, semantic_weight: float = 0.3,
                 recency_boost: float = 1.5, frequency_boost: float = 1.2):
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight
        self.recency_boost = recency_boost
        self.frequency_boost = frequency_boost
        self._access_counts: Dict[str, int] = defaultdict(int)
        self._access_times: Dict[str, float] = {}

    def search(self, query: str, candidates: List[Dict], limit: int = 10) -> List[Dict]:
        """Search and rank candidates using hybrid scoring.

        Args:
            query: Search query
            candidates: List of memories with 'content'/'text' and 'id' keys
            limit: Maximum results

        Returns:
            Ranked list of memories with added 'enhanced_score'
        """
        if not candidates:
            return []

        now = time.time()
        scored = []

        for mem in candidates:
            text = str(mem.get("content", mem.get("text", "")))
            mid = mem.get("id", "")

            # BM25 score: keyword overlap ratio
            query_terms = set(query.lower().split())
            text_terms = set(text.lower().split())
            bm25_score = len(query_terms & text_terms) / max(1, len(query_terms))

            # Semantic score: simple text similarity
            semantic_score = self._text_similarity(query.lower(), text.lower())

            # Recency boost
            last_access = self._access_times.get(mid, mem.get("timestamp", now))
            recency = 1.0 / (1.0 + math.log(1 + (now - last_access) / 3600))

            # Frequency boost
            freq = math.log(1 + self._access_counts.get(mid, 0)) * 0.1

            # Combined score
            score = (bm25_score * self.bm25_weight +
                     semantic_score * self.semantic_weight +
                     recency * self.recency_boost * 0.1 +
                     freq * self.frequency_boost * 0.1)

            scored.append({**mem, "enhanced_score": round(score, 4)})

        scored.sort(key=lambda x: x["enhanced_score"], reverse=True)

        # Record access
        for r in scored[:limit]:
            mid = r.get("id", "")
            self._access_counts[mid] += 1
            self._access_times[mid] = now

        return scored[:limit]

    def _text_similarity(self, a: str, b: str) -> float:
        """Simple word-overlap similarity."""
        from difflib import SequenceMatcher
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()
