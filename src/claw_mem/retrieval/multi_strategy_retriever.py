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
Multi-Strategy Retrieval (P0-1 Stage 2)

Orchestrates multiple retrieval strategies and fuses results for
improved recall and relevance. Strategies include:
1. BM25 lexical search
2. Concept graph traversal
3. Temporal decay weighting
4. Result fusion

Target: retrieval hit rate >91%
"""

import math
import time
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from .query_understanding import ExpandedQuery, QueryIntent
from .bm25_retriever import BM25Retriever


@dataclass
class Candidate:
    """Candidate memory from a retrieval strategy."""

    memory_id: str
    content: str
    score: float
    source_strategy: str
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "score": self.score,
            "source_strategy": self.source_strategy,
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    """Final fused retrieval result."""

    candidates: List[Candidate]
    total_candidates: int
    strategies_used: List[str]
    fusion_method: str
    latency_ms: float = 0.0

    def get_top(self, k: int) -> List[Candidate]:
        """Get top-k candidates by score."""
        return sorted(self.candidates, key=lambda c: c.score, reverse=True)[:k]


class MultiStrategyRetriever:
    """Stage 2: Multi-strategy retrieval with fusion.

    Combines multiple retrieval strategies:
    1. BM25: Fast lexical matching
    2. Graph: Concept-mediated connections (optional)
    3. Temporal: Recency boost

    Usage:
        retriever = MultiStrategyRetriever()
        candidates = retriever.retrieve(expanded_query, memories)
    """

    def __init__(
        self,
        bm25: Optional[BM25Retriever] = None,
        graph_traverser: Optional["ConceptGraphTraverser"] = None,
        temporal_weighter: Optional["TemporalDecayWeighter"] = None,
    ):
        self.bm25 = bm25 or BM25Retriever()
        self.graph_traverser = graph_traverser or ConceptGraphTraverser()
        self.temporal_weighter = temporal_weighter or TemporalDecayWeighter()

    def retrieve(
        self,
        query: ExpandedQuery,
        memory_pool: List[Dict],
        top_k: int = 10,
        fusion_method: str = "weighted_sum",
    ) -> RetrievalResult:
        """Retrieve memories using multiple strategies and fuse results.

        Args:
            query: Expanded query with intent and entities
            memory_pool: List of memory dicts with content/timestamp/tags
            top_k: Maximum number of results to return
            fusion_method: "weighted_sum", "rrf", or "rank_ensemble"

        Returns:
            RetrievalResult with fused candidate list
        """
        t0 = time.perf_counter()
        candidates: Dict[str, Candidate] = {}
        strategies_used: List[str] = []

        # Strategy 1: BM25 lexical search (always enabled)
        self.bm25.build_index(memory_pool)

        bm25_results = self.bm25.search(query.expanded_text, memory_pool, limit=top_k * 3)
        strategies_used.append("bm25")

        for m in bm25_results:
            mid = m.get("id", m.get("memory_id", ""))
            score = m.get("_bm25_score", m.get("score", 0.0))
            candidates[mid] = Candidate(
                memory_id=mid,
                content=m.get("content", ""),
                score=score,
                source_strategy="bm25",
                metadata=m,
            )

        # Strategy 2: Concept graph traversal (if entities available)
        if query.entities:
            graph_results = self.graph_traverser.traverse(
                query.entities, memory_pool, depth=2, max_results=top_k * 2
            )
            strategies_used.append("concept_graph")

            for c in graph_results:
                mid = c.get("id", c.get("memory_id", ""))
                score = c.get("score", 0.0)
                if mid in candidates:
                    candidates[mid].score += score * 0.5  # Blend with BM25
                    candidates[mid].metadata["graph_score"] = score
                else:
                    candidates[mid] = Candidate(
                        memory_id=mid,
                        content=c.get("content", ""),
                        score=score * 0.6,  # Lower weight for standalone graph
                        source_strategy="concept_graph",
                        metadata=c,
                    )

        # Strategy 3: Temporal decay (reweight by recency)
        now = time.time()
        for mid, cand in candidates.items():
            meta = cand.metadata
            ts_str = meta.get("timestamp", "")
            temporal_weight = self.temporal_weighter.compute_weight(ts_str, now)
            cand.score *= temporal_weight
        strategies_used.append("temporal")

        # Strategy 4: Intent-based weighting adjustments
        if query.intent == QueryIntent.RECENT:
            # Boost recent memories for RECENT intent
            for cand in candidates.values():
                cand.score *= 1.3
            strategies_used.append("intent_boost")

        # Normalize scores
        sorted_candidates = self._normalize_and_sort(list(candidates.values()))

        # Trim to top_k
        final_candidates = sorted_candidates[:top_k]

        latency = (time.perf_counter() - t0) * 1000

        return RetrievalResult(
            candidates=final_candidates,
            total_candidates=len(sorted_candidates),
            strategies_used=strategies_used,
            fusion_method=fusion_method,
            latency_ms=latency,
        )

    def _normalize_and_sort(self, candidates: List[Candidate]) -> List[Candidate]:
        """Normalize scores to 0-1 range and sort descending."""
        if not candidates:
            return []
        max_score = max(c.score for c in candidates)
        min_score = min(c.score for c in candidates)
        score_range = max_score - min_score or 1.0
        for c in candidates:
            c.score = (c.score - min_score) / score_range
        return sorted(candidates, key=lambda c: c.score, reverse=True)


class ConceptGraphTraverser:
    """Concept graph traversal for entity-based retrieval.

    Traverses concept relationships to find memories connected to
    extracted entities, expanding recall beyond keyword matching.
    """

    def __init__(self, concept_map: Optional[Dict[str, List[str]]] = None):
        self._concept_map: Dict[str, List[str]] = concept_map or {}
        self._build_default_map()

    def _build_default_map(self):
        """Build default concept relationship map."""
        defaults = {
            "python": ["code", "programming", "script", "pip"],
            "javascript": ["code", "typescript", "frontend", "npm"],
            "api": ["interface", "endpoint", "rest", "http"],
            "memory": ["storage", "cache", "retrieval", "search"],
            "learning": ["training", "model", "rl", "improvement"],
            "agent": ["ai", "assistant", "bot", "automation"],
            "docker": ["container", "deployment", "image"],
            "git": ["commit", "branch", "merge", "repository"],
        }
        for k, v in defaults.items():
            if k not in self._concept_map:
                self._concept_map[k] = v

    def add_concept(self, concept: str, related: List[str]):
        """Add or extend a concept with related terms."""
        key = concept.lower()
        if key in self._concept_map:
            self._concept_map[key].extend(r for r in related if r not in self._concept_map[key])
        else:
            self._concept_map[key] = related

    def traverse(
        self,
        entities: List[str],
        memory_pool: List[Dict],
        depth: int = 2,
        max_results: int = 20,
    ) -> List[Dict]:
        """Traverse concept graph from entities to find related memories.

        Args:
            entities: Starting entities from query
            memory_pool: Available memories
            depth: BFS depth for traversal
            max_results: Max results to return

        Returns:
            List of memory dicts with concept graph scores
        """
        # BFS from entity nodes
        visited: set = set()
        frontier = [e.lower() for e in entities]
        traversal_terms: Dict[str, int] = {}  # term -> distance from start
        for e in frontier:
            traversal_terms[e] = 0

        for d in range(depth):
            next_frontier = []
            for term in frontier:
                if term in visited:
                    continue
                visited.add(term)
                related = self._concept_map.get(term, [])
                for r in related:
                    r_lower = r.lower()
                    if r_lower not in visited and r_lower not in traversal_terms:
                        traversal_terms[r_lower] = d + 1
                        next_frontier.append(r_lower)
            frontier = next_frontier

        # Score memories based on concept matches
        scored = []
        for mem in memory_pool:
            content_lower = (mem.get("content", "") + " " + " ".join(mem.get("tags", []))).lower()
            best_match_distance = float("inf")
            matched_terms = 0

            for term, dist in traversal_terms.items():
                if term in content_lower:
                    if dist < best_match_distance:
                        best_match_distance = dist
                    matched_terms += 1

            if matched_terms > 0:
                # Score: closer concepts + more matches = higher score
                concept_score = matched_terms / max(best_match_distance, 1.0)
                mem_copy = dict(mem)
                mem_copy["score"] = concept_score
                mem_copy["traversal_distance"] = best_match_distance
                mem_copy["matched_concepts"] = matched_terms
                scored.append(mem_copy)

        scored.sort(key=lambda m: m["score"], reverse=True)
        return scored[:max_results]


class TemporalDecayWeighter:
    """Apply temporal decay weighting to retrieval scores.

    Implements exponential decay: score *= e^(-lambda * age)
    Recent memories get higher weights, older ones get dampened.
    """

    # Half-life constants (in seconds)
    HALF_LIFE_SHORT = 1800  # 30 minutes
    HALF_LIFE_MEDIUM = 86400  # 1 day
    HALF_LIFE_LONG = 604800  # 1 week

    def __init__(self, base_half_life: float = HALF_LIFE_MEDIUM, min_weight: float = 0.1):
        """Initialize temporal weighter.

        Args:
            base_half_life: Half-life in seconds for exponential decay
            min_weight: Minimum weight to apply (floor)
        """
        self.base_half_life = base_half_life
        self.min_weight = min_weight
        self._decay_rate = math.log(2) / base_half_life

    def compute_weight(
        self, timestamp_str: Optional[str], reference_time: Optional[float] = None
    ) -> float:
        """Compute temporal weight for a memory timestamp.

        Args:
            timestamp_str: ISO format timestamp string
            reference_time: Reference time (default: now)

        Returns:
            Weight multiplier (1.0 = no decay, approaching min_weight for old)
        """
        if not timestamp_str:
            return 1.0

        ref = reference_time or time.time()

        try:
            # Try parsing ISO format
            if "T" in timestamp_str:
                ts = time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%dT%H:%M:%S"))
            else:
                ts = time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S"))
        except (ValueError, TypeError):
            return 1.0

        age_seconds = max(0, ref - ts)
        weight = math.exp(-self._decay_rate * age_seconds)
        return max(self.min_weight, weight)

    def apply_decay(
        self, candidates: List[Candidate], reference_time: Optional[float] = None
    ) -> List[Candidate]:
        """Apply temporal decay to all candidates in-place.

        Args:
            candidates: List of retrieval candidates
            reference_time: Reference timestamp

        Returns:
            Same candidates with scores multiplied by temporal weight
        """
        for cand in candidates:
            ts_str = cand.metadata.get("timestamp", "")
            weight = self.compute_weight(ts_str, reference_time)
            cand.score *= weight
            cand.metadata["temporal_weight"] = weight
        return candidates


__all__ = [
    "MultiStrategyRetriever",
    "ConceptGraphTraverser",
    "TemporalDecayWeighter",
    "Candidate",
    "RetrievalResult",
]
