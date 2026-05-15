"""Engram Index — O(1) NN-gram hash lookup for claw-mem v2.15.0."""

import hashlib
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EngramIndex:
    """O(1) lookup index using NN-gram hashing.

    Builds a hash-based inverted index over memory content
    for constant-time exact and near-exact match retrieval.
    """

    def __init__(self, ngram_size: int = 3):
        self.ngram_size = ngram_size
        self._index: Dict[str, List[str]] = defaultdict(list)
        self._memories: Dict[str, Dict] = {}
        self._built = False

    def build(self, memories: List[Dict]) -> None:
        """Build the engram hash index from a list of memories.

        Each memory should have 'id' and 'content'/'text' keys.
        """
        self._index.clear()
        self._memories.clear()
        for mem in memories:
            mid = mem.get("id", "")
            text = mem.get("content", mem.get("text", ""))
            if not mid or not text:
                continue
            self._memories[mid] = mem
            for ngram in self._extract_ngrams(text):
                self._index[ngram].append(mid)
        self._built = True
        logger.info("Engram index built: %d entries, %d ngrams", len(memories), len(self._index))

    def _extract_ngrams(self, text: str) -> List[str]:
        """Extract NN-grams with hashing for uniqueness."""
        text = str(text).lower().strip()
        if len(text) < self.ngram_size:
            return [hashlib.md5(text.encode()).hexdigest()[:8]]
        ngrams = []
        for i in range(len(text) - self.ngram_size + 1):
            chunk = text[i : i + self.ngram_size]
            ngrams.append(hashlib.md5(chunk.encode()).hexdigest()[:8])
        return ngrams

    def lookup(self, query: str, top_k: int = 10) -> List[Dict]:
        """O(1) lookup by NN-gram hash matching."""
        if not self._built:
            return []

        query_ngrams = set(self._extract_ngrams(query))
        scores: Dict[str, float] = defaultdict(float)

        for ngram in query_ngrams:
            for mid in self._index.get(ngram, []):
                scores[mid] += 1.0

        if not scores:
            return []

        max_score = max(scores.values())
        sorted_ids = sorted(scores, key=scores.get, reverse=True)
        results = []
        for mid in sorted_ids[:top_k]:
            mem = self._memories.get(mid, {})
            results.append(
                {
                    "id": mid,
                    "score": round(scores[mid] / max_score, 4) if max_score else 0.0,
                    "text": str(mem.get("content", mem.get("text", "")))[:200],
                }
            )
        return results

    def get_stats(self) -> Dict:
        return {
            "indexed_ngrams": len(self._index),
            "indexed_memories": len(self._memories),
            "built": self._built,
        }
