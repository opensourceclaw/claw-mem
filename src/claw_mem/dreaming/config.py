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
Dreaming Engine Configuration (v4.12.0)

Weighted scoring parameters for the light→deep→REM→promote pipeline.
All weights sum to 1.0 for a normalized composite score.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DreamingConfig:
    """Configuration for the Dreaming Engine pipeline.

    Attributes:
        frequency_weight: Weight for how often a signal appears (0.0-1.0).
        relevance_weight: Weight for semantic relevance to existing knowledge.
        query_diversity_weight: Weight for number of distinct queries.
        recency_weight: Weight for temporal freshness.
        consolidation_weight: Weight for how well-integrated the signal is.
        conceptual_richness_weight: Weight for information density.
        score_threshold: Minimum composite score to pass the deep filter (0.0-1.0).
        max_staged: Maximum signals to stage in light phase.
        top_k_candidates: Max candidates after deep scoring.
        dry_run: If True, the pipeline scores but does not persist.
    """

    frequency_weight: float = 0.20
    relevance_weight: float = 0.20
    query_diversity_weight: float = 0.15
    recency_weight: float = 0.15
    consolidation_weight: float = 0.15
    conceptual_richness_weight: float = 0.15

    score_threshold: float = 0.35
    max_staged: int = 50
    top_k_candidates: int = 20
    dry_run: bool = False

    def validate(self) -> bool:
        """Check that all weights sum approximately to 1.0."""
        total = (
            self.frequency_weight
            + self.relevance_weight
            + self.query_diversity_weight
            + self.recency_weight
            + self.consolidation_weight
            + self.conceptual_richness_weight
        )
        return abs(total - 1.0) < 0.01
