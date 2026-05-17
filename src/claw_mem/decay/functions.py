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
Decay functions and configuration for the Oblivion forgetting mechanism.

Core formula: weight(t) = base * exp(-lambda * days)
  lambda = ln(2) / half_life_days
"""

import math
from dataclasses import dataclass, field
from typing import Dict


# ── Half-life constants (days) ──────────────────────────────────────

HALF_LIFE: Dict[str, float] = {
    "episodic": 7.0,
    "semantic": 90.0,
    "procedural": 180.0,
    "temporal": 7.0,
    "causal": 14.0,
    "entity": 30.0,
    "fact_node": 90.0,
    "episode_node": 7.0,
}

# Decay rate lambda = ln(2) / half_life
LAMBDA: Dict[str, float] = {
    k: math.log(2) / v for k, v in HALF_LIFE.items()
}


# ── Core decay function ─────────────────────────────────────────────

def exponential_decay(base: float, days_elapsed: float,
                      half_life_days: float) -> float:
    """Compute exponential decay weight.

    Args:
        base: Initial weight (typically 1.0).
        days_elapsed: Days since creation/last-update.
        half_life_days: Half-life in days.

    Returns:
        Decayed weight in [0.0, 1.0].
    """
    if days_elapsed <= 0:
        return base
    if half_life_days <= 0:
        return 0.0
    decay_rate = math.log(2) / half_life_days
    return base * math.exp(-decay_rate * days_elapsed)


def calculate_weight(initial_weight: float, days_elapsed: float,
                     category: str) -> float:
    """Calculate decayed weight for a given category.

    Args:
        initial_weight: Starting weight (default 1.0).
        days_elapsed: Days since creation.
        category: Half-life category name ('temporal', 'semantic', etc.).

    Returns:
        Decayed weight.
    """
    half_life = HALF_LIFE.get(category, 30.0)
    return exponential_decay(initial_weight, days_elapsed, half_life)


def half_life_to_days(weight: float, initial: float,
                      days_elapsed: float) -> float:
    """Infer half-life from observed decay (for adaptive tuning).

    Uses the formula: t_half = -ln(2) * days / ln(weight / initial)
    """
    if weight >= initial or weight <= 0 or days_elapsed <= 0:
        return 30.0
    return -math.log(2) * days_elapsed / math.log(weight / initial)


# ── Configuration ───────────────────────────────────────────────────

@dataclass
class DecayConfig:
    """Decay configuration, tunable via MemoryManager constructor."""

    # Half-life per category (days)
    half_life_temporal: float = 7.0
    half_life_causal: float = 14.0
    half_life_semantic: float = 90.0
    half_life_entity: float = 30.0
    half_life_episode_node: float = 7.0
    half_life_fact_node: float = 90.0

    # Weight thresholds
    strong_threshold: float = 0.7
    archive_threshold: float = 0.3
    expire_threshold: float = 0.1
    purge_threshold: float = 0.05

    # Scheduler settings
    decay_interval_hours: int = 24
    batch_size: int = 1000
    max_concurrent: int = 1

    # Protection
    protect_critical: bool = True
    protect_pinned: bool = True

    @classmethod
    def default(cls) -> "DecayConfig":
        return cls()
