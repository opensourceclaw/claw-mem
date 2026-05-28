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
Dreaming Engine — Deep Phase (Candidate Scorer | v4.12.0)

Six-dimensional heuristic scoring with weighted composite.
Scores normalized to 0.0–1.0, weighted by DreamingConfig.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config import DreamingConfig
    from .light import Signal


@dataclass
class ScoredCandidate:
    """A signal with all six dimension scores and a weighted composite.

    Attributes:
        signal: The original staged signal.
        frequency_score: 0.0-1.0, based on recall_count.
        relevance_score: 0.0-1.0, from prior relevance_scores.
        query_diversity_score: 0.0-1.0, based on unique_queries.
        recency_score: 0.0-1.0, temporal freshness.
        consolidation_score: 0.0-1.0, integration with existing knowledge.
        conceptual_richness_score: 0.0-1.0, information density.
        composite: Weighted sum of all six scores.
    """

    signal: Any  # Signal
    frequency_score: float = 0.0
    relevance_score: float = 0.0
    query_diversity_score: float = 0.0
    recency_score: float = 0.0
    consolidation_score: float = 0.0
    conceptual_richness_score: float = 0.0
    composite: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal": self.signal.to_dict(),
            "frequency_score": round(self.frequency_score, 3),
            "relevance_score": round(self.relevance_score, 3),
            "query_diversity_score": round(self.query_diversity_score, 3),
            "recency_score": round(self.recency_score, 3),
            "consolidation_score": round(self.consolidation_score, 3),
            "conceptual_richness_score": round(self.conceptual_richness_score, 3),
            "composite": round(self.composite, 3),
        }


class CandidateScorer:
    """Six-dimensional heuristic scorer for dreaming candidates.

    Each dimension is independently scored 0.0–1.0, then combined
    using configured weights to produce a composite score.
    """

    def __init__(self, config: Optional[DreamingConfig] = None):
        from .config import DreamingConfig

        self._config = config or DreamingConfig()

    def score_all(self, signals: List) -> List[ScoredCandidate]:
        """Score all staged signals.

        Args:
            signals: List of Signal objects from the light phase.

        Returns:
            List of ScoredCandidate sorted by composite descending.
        """
        candidates: List[ScoredCandidate] = []

        for sig in signals:
            freq = self._score_frequency(sig)
            rel = self._score_relevance(sig)
            div = self._score_query_diversity(sig)
            rec = self._score_recency(sig)
            con = self._score_consolidation(sig)
            rich = self._score_conceptual_richness(sig)

            composite = (
                freq * self._config.frequency_weight
                + rel * self._config.relevance_weight
                + div * self._config.query_diversity_weight
                + rec * self._config.recency_weight
                + con * self._config.consolidation_weight
                + rich * self._config.conceptual_richness_weight
            )

            candidates.append(
                ScoredCandidate(
                    signal=sig,
                    frequency_score=freq,
                    relevance_score=rel,
                    query_diversity_score=div,
                    recency_score=rec,
                    consolidation_score=con,
                    conceptual_richness_score=rich,
                    composite=composite,
                )
            )

        candidates.sort(key=lambda c: c.composite, reverse=True)
        return candidates

    def filter(self, candidates: List[ScoredCandidate]) -> List[ScoredCandidate]:
        """Filter candidates by score threshold and top-k.

        Args:
            candidates: Scored candidates (already sorted by composite).

        Returns:
            Filtered list of ScoredCandidate.
        """
        above_threshold = [
            c for c in candidates if c.composite >= self._config.score_threshold
        ]
        return above_threshold[: self._config.top_k_candidates]

    # ── dimension scorers ──────────────────────────────────────────

    @staticmethod
    def _score_frequency(sig) -> float:
        """Score based on recall_count. Saturates at ~10."""
        return min(sig.recall_count / 10.0, 1.0)

    @staticmethod
    def _score_relevance(sig) -> float:
        """Average of existing relevance scores, defaulting to 0.5."""
        scores = sig.relevance_scores
        if not scores:
            return 0.5
        return sum(scores) / len(scores)

    @staticmethod
    def _score_query_diversity(sig) -> float:
        """Score based on unique query count. Saturates at ~5."""
        return min(sig.unique_queries / 5.0, 1.0)

    @staticmethod
    def _score_recency(sig) -> float:
        """Exponential decay from timestamp. Newer = higher score."""
        if not sig.timestamp:
            return 0.5
        try:
            ts = datetime.fromisoformat(sig.timestamp)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            ts_naive = ts.replace(tzinfo=None)
            age_hours = (now - ts_naive).total_seconds() / 3600.0
            # Clamp negative ages (future timestamps) to zero age
            if age_hours < 0:
                age_hours = 0.0
            # Half-life of 24 hours
            return math.exp(-age_hours / 24.0)
        except (ValueError, TypeError):
            return 0.5

    @staticmethod
    def _score_consolidation(sig) -> float:
        """Proxy: higher tag count suggests better integration."""
        tag_count = len(sig.tags) if sig.tags else 0
        return min(tag_count / 5.0, 1.0)

    @staticmethod
    def _score_conceptual_richness(sig) -> float:
        """Proxy: content length and named-entity count as information density."""
        text = sig.content or ""
        # Length component
        length_score = min(len(text) / 200.0, 1.0)
        # Named entity proxy: uppercase words as simple heuristic
        entities = len(re.findall(r"\b[A-Z][a-z]+\b", text))
        entity_score = min(entities / 3.0, 1.0)
        return (length_score * 0.6 + entity_score * 0.4)
