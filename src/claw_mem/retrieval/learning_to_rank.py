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
Learning-to-Rank Re-Ranker (P0-1 Stage 3)

ML-based re-ranking of retrieval candidates using feature extraction
and a lightweight ranking model. Supports online learning from
user feedback.

Features:
- BM25 score
- Recency score
- Access frequency
- Concept similarity
- Query-document similarity
- User interaction history
"""

import json
import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from .query_understanding import ExpandedQuery
from .multi_strategy_retriever import Candidate


@dataclass
class RankingFeatures:
    """Feature vector for a candidate memory."""
    bm25_score: float = 0.0
    recency_score: float = 0.0
    frequency_score: float = 0.0
    concept_similarity: float = 0.0
    query_content_similarity: float = 0.0
    interaction_score: float = 0.0
    length_normalization: float = 0.0
    tag_match_score: float = 0.0


@dataclass
class Result:
    """Final ranked result after re-ranking."""
    memory_id: str
    content: str
    score: float
    rank: int
    features: RankingFeatures = field(default_factory=RankingFeatures)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "score": self.score,
            "rank": self.rank,
            "features": {
                "bm25_score": self.features.bm25_score,
                "recency_score": self.features.recency_score,
                "frequency_score": self.features.frequency_score,
                "concept_similarity": self.features.concept_similarity,
                "query_content_similarity": self.features.query_content_similarity,
                "interaction_score": self.features.interaction_score,
                "length_normalization": self.features.length_normalization,
                "tag_match_score": self.features.tag_match_score,
            },
            "metadata": self.metadata,
        }


class LearningToRankReranker:
    """Stage 3: ML-based re-ranking of retrieval candidates.

    Extracts features from candidates and applies a lightweight linear
    ranking model. Supports online learning from user feedback signals.

    Usage:
        reranker = LearningToRankReranker()
        results = reranker.rerank(expanded_query, candidates, top_k=10)
    """

    # Default feature weights (learnt from training)
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "bm25_score": 0.30,
        "recency_score": 0.20,
        "frequency_score": 0.10,
        "concept_similarity": 0.15,
        "query_content_similarity": 0.15,
        "interaction_score": 0.05,
        "length_normalization": 0.02,
        "tag_match_score": 0.03,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 learning_rate: float = 0.01):
        """Initialize re-ranker.

        Args:
            weights: Feature weight dictionary (defaults to DEFAULT_WEIGHTS)
            learning_rate: Online learning rate
        """
        self.weights = dict(weights or self.DEFAULT_WEIGHTS)
        self.learning_rate = learning_rate
        self._feedback_buffer: List[Dict] = []
        self._stats = {"sessions": 0, "reranked": 0, "feedback_events": 0}

    def rerank(
        self,
        query: 'ExpandedQuery',
        candidates: List['Candidate'],
        top_k: int = 10,
    ) -> List['Result']:
        """Re-rank candidates using ML features.

        Args:
            query: Expanded query with entities and intent
            candidates: List of retrieval candidates
            top_k: Max results to return

        Returns:
            Sorted list of ranked Results
        """
        self._stats["sessions"] += 1
        self._stats["reranked"] += len(candidates)

        results = []
        now = time.time()

        for rank, candidate in enumerate(candidates):
            features = self.extract_features(query, candidate, now)
            score = self._compute_score(features)

            results.append(Result(
                memory_id=candidate.memory_id,
                content=candidate.content,
                score=score,
                rank=rank,
                features=features,
                metadata=candidate.metadata,
            ))

        # Sort by computed score descending
        results.sort(key=lambda r: r.score, reverse=True)

        # Update ranks
        for i, r in enumerate(results[:top_k]):
            r.rank = i + 1

        return results[:top_k]

    def extract_features(
        self,
        query: 'ExpandedQuery',
        candidate: 'Candidate',
        now: Optional[float] = None,
    ) -> RankingFeatures:
        """Extract feature vector from candidate.

        Args:
            query: Expanded query
            candidate: Candidate memory
            now: Current timestamp for recency calculation

        Returns:
            RankingFeatures dataclass
        """
        meta = candidate.metadata
        content = candidate.content
        now = now or time.time()

        # BM25 score (normalized)
        bm25_score = candidate.score

        # Recency score (0-1, 1 = very recent)
        recency_score = self._compute_recency(meta.get("timestamp", ""), now)

        # Frequency score (0-1, based on access count)
        access_count = meta.get("access_count", meta.get("accessCount", 0))
        frequency_score = self._compute_frequency(access_count)

        # Concept similarity (from query entities)
        concept_similarity = self._compute_concept_similarity(
            query.entities, content, meta.get("tags", [])
        )

        # Query-content similarity (Jaccard-like)
        query_content_similarity = self._compute_text_similarity(
            query.expanded_text, content
        )

        # Interaction history score
        interaction_score = self._compute_interaction(
            meta.get("interaction_count", meta.get("interactionCount", 0)),
            meta.get("last_interaction", ""),
            now,
        )

        # Length normalization (penalize too short or too long)
        length_norm = self._compute_length_norm(len(content))

        # Tag match score
        tag_match_score = self._compute_tag_match(
            query.entities, meta.get("tags", [])
        )

        return RankingFeatures(
            bm25_score=bm25_score,
            recency_score=recency_score,
            frequency_score=frequency_score,
            concept_similarity=concept_similarity,
            query_content_similarity=query_content_similarity,
            interaction_score=interaction_score,
            length_normalization=length_norm,
            tag_match_score=tag_match_score,
        )

    def record_feedback(self, memory_id: str, query_id: str,
                        clicked: bool, relevance: float = 0.0):
        """Record user feedback for online learning.

        Args:
            memory_id: Selected or rejected memory ID
            query_id: Query identifier
            clicked: Whether user selected this memory
            relevance: Relevance rating (0-1)
        """
        self._stats["feedback_events"] += 1
        self._feedback_buffer.append({
            "memory_id": memory_id,
            "query_id": query_id,
            "clicked": clicked,
            "relevance": relevance,
            "timestamp": time.time(),
        })

        # Trigger online learning if buffer is large enough
        if len(self._feedback_buffer) >= 10:
            self._online_learn()

    def _online_learn(self):
        """Perform online learning from accumulated feedback."""
        if not self._feedback_buffer:
            return

        # Simple perceptron-style update: reinforce features of clicked items
        clicked_ids = {fb["memory_id"] for fb in self._feedback_buffer if fb["clicked"]}
        if not clicked_ids:
            self._feedback_buffer.clear()
            return

        # Small weight adjustments
        for fb in self._feedback_buffer[-10:]:
            if fb["clicked"]:
                # Positive feedback: reinforce all weights slightly
                for key in self.weights:
                    self.weights[key] *= (1 + self.learning_rate * 0.1)
            else:
                # Negative feedback: dampen weights slightly
                for key in self.weights:
                    self.weights[key] *= (1 - self.learning_rate * 0.05)

        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        if total > 0:
            for key in self.weights:
                self.weights[key] /= total

        self._feedback_buffer.clear()

    def get_weights(self) -> Dict[str, float]:
        """Get current feature weights."""
        return dict(self.weights)

    def set_weights(self, weights: Dict[str, float]):
        """Set feature weights directly."""
        self.weights = dict(weights)

    def get_statistics(self) -> Dict:
        """Get re-ranker statistics."""
        return dict(self._stats)

    def _compute_score(self, features: RankingFeatures) -> float:
        """Compute weighted score from features."""
        score = 0.0
        score += self.weights.get("bm25_score", 0) * features.bm25_score
        score += self.weights.get("recency_score", 0) * features.recency_score
        score += self.weights.get("frequency_score", 0) * features.frequency_score
        score += self.weights.get("concept_similarity", 0) * features.concept_similarity
        score += self.weights.get("query_content_similarity", 0) * features.query_content_similarity
        score += self.weights.get("interaction_score", 0) * features.interaction_score
        score += self.weights.get("length_normalization", 0) * features.length_normalization
        score += self.weights.get("tag_match_score", 0) * features.tag_match_score
        return score

    @staticmethod
    def _compute_recency(timestamp_str: str, now: float) -> float:
        """Compute recency score (0-1)."""
        if not timestamp_str:
            return 0.5
        try:
            if 'T' in timestamp_str:
                ts = time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%dT%H:%M:%S"))
            else:
                ts = time.mktime(time.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S"))
            age_hours = max(0, (now - ts)) / 3600
            # Half-life of ~48 hours
            return math.exp(-math.log(2) * age_hours / 48)
        except (ValueError, TypeError):
            return 0.5

    @staticmethod
    def _compute_frequency(access_count: int) -> float:
        """Compute frequency score (0-1)."""
        if access_count <= 0:
            return 0.0
        return min(1.0, math.log(access_count + 1) / math.log(101))

    @staticmethod
    def _compute_concept_similarity(entities: List[str], content: str,
                                     tags: List[str]) -> float:
        """Compute concept/entity overlap with content and tags."""
        if not entities:
            return 0.0
        content_lower = (content + " " + " ".join(tags)).lower()
        matches = sum(1 for e in entities if e.lower() in content_lower)
        return matches / len(entities)

    @staticmethod
    def _compute_text_similarity(query_text: str, content: str) -> float:
        """Compute Jaccard-like text similarity."""
        if not query_text or not content:
            return 0.0
        query_tokens = set(query_text.lower().split())
        content_tokens = set(content.lower().split())
        if not query_tokens or not content_tokens:
            return 0.0
        intersection = query_tokens & content_tokens
        union = query_tokens | content_tokens
        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def _compute_interaction(interaction_count: int,
                              last_interaction: str,
                              now: float) -> float:
        """Compute interaction history score (0-1)."""
        if interaction_count <= 0:
            return 0.0
        # Base score from interaction count
        count_score = min(1.0, math.log(interaction_count + 1) / math.log(51))
        # Recency bonus for recent interactions
        if last_interaction:
            try:
                ts = time.mktime(time.strptime(last_interaction[:19], "%Y-%m-%dT%H:%M:%S"))
                hours = max(0, (now - ts)) / 3600
                recency_bonus = math.exp(-math.log(2) * hours / 168)  # 1 week half-life
                return count_score * (0.7 + 0.3 * recency_bonus)
            except (ValueError, TypeError):
                pass
        return count_score * 0.7

    @staticmethod
    def _compute_length_norm(content_length: int) -> float:
        """Normalize content length (penalize extremes)."""
        if content_length < 10:
            return 0.3
        if content_length < 50:
            return 0.6
        if content_length < 1000:
            return 1.0
        if content_length < 5000:
            return 0.7
        return 0.4

    @staticmethod
    def _compute_tag_match(entities: List[str], tags: List[str]) -> float:
        """Compute tag match score with query entities."""
        if not entities or not tags:
            return 0.0
        entity_set = {e.lower() for e in entities}
        tag_set = {t.lower() for t in tags}
        matches = entity_set & tag_set
        return len(matches) / len(entity_set) if entity_set else 0.0


__all__ = [
    'LearningToRankReranker',
    'RankingFeatures',
    'Result',
]
