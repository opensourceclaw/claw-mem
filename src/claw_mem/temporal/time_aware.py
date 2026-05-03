"""
claw-mem v2.9.1 - Time-Aware Search

Calculates time-based weights for search results, boosting recent
memories and decaying older ones based on configurable parameters.

Weight functions:
  - Exponential decay: w = e^(-age/half_life)
  - Linear decay:     w = max(0, 1 - age/max_age)
  - Step decay:       w = 1.0 if age < recent_window else 0.5 if age < older_window else 0.1
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class TimeWeightConfig:
    """Configuration for time weight calculation."""
    decay_type: str = "exponential"  # "exponential", "linear", "step"
    half_life_days: float = 30.0
    max_age_days: float = 365.0
    recent_window_days: float = 7.0
    older_window_days: float = 90.0
    base_weight: float = 1.0
    min_weight: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decay_type": self.decay_type,
            "half_life_days": self.half_life_days,
            "max_age_days": self.max_age_days,
        }


class TimeWeightCalculator:
    """Calculate time-based relevance weights for search results.

    Usage:
        calc = TimeWeightCalculator()
        weight = calc.calculate("2024-01-15T10:00:00")
        print(f"Time weight: {weight:.2f}")

        # Apply to search results
        results = calc.apply_weights(memories)
        # Results now sorted by time-weighted relevance
    """

    def __init__(self, config: Optional[TimeWeightConfig] = None):
        self.config = config or TimeWeightConfig()

    def calculate(self, timestamp: str, now: Optional[datetime] = None) -> float:
        """Calculate time weight for a memory.

        Args:
            timestamp: ISO format timestamp or date string
            now: Reference time (defaults to current UTC)

        Returns:
            Weight between min_weight and base_weight
        """
        age_days = self._age_days(timestamp, now)

        if self.config.decay_type == "linear":
            weight = max(self.config.min_weight,
                         self.config.base_weight * (1 - age_days / self.config.max_age_days))
        elif self.config.decay_type == "step":
            weight = self._step_weight(age_days)
        else:  # exponential (default)
            weight = self.config.base_weight * math.exp(
                -age_days / self.config.half_life_days * math.log(2)
            )

        return max(self.config.min_weight, min(weight, self.config.base_weight))

    def apply_weights(
        self, memories: List[Dict[str, Any]], weight_field: str = "time_weight",
        sort_by_weight: bool = True,
    ) -> List[Dict[str, Any]]:
        """Apply time weights to a list of memory records.

        Args:
            memories: List of memory dicts with "timestamp" field
            weight_field: Field name to store the weight
            sort_by_weight: Sort results by weight descending

        Returns:
            Memories with time_weight field added, optionally sorted
        """
        now = datetime.now(timezone.utc)
        for mem in memories:
            ts = mem.get("timestamp", "")
            mem[weight_field] = self.calculate(ts, now)

        if sort_by_weight:
            memories.sort(key=lambda m: m.get(weight_field, 0), reverse=True)

        return memories

    def get_best_time_range(self, query: str) -> Optional[str]:
        """Suggest a time range based on query analysis.

        Args:
            query: Search query

        Returns:
            Time range string (e.g., "7d", "30d", "90d") or None
        """
        import re
        query_lower = query.lower()

        # Parse explicit time range in query
        match = re.search(r"((?:last|past|recent|近|最近)\s*(\d+)\s*(?:day|week|month|year|天|周|月|年))",
                          query_lower)
        if match:
            return match.group(0)

        # Heuristic time ranges
        if any(kw in query_lower for kw in ("today", "今天", "now", "现在")):
            return "1d"
        if any(kw in query_lower for kw in ("recent", "this week", "最近", "本周")):
            return "7d"
        if any(kw in query_lower for kw in ("this month", "这个月")):
            return "30d"

        return None

    def _age_days(self, timestamp: str, now: Optional[datetime] = None) -> float:
        """Calculate age in days from timestamp."""
        now = now or datetime.now(timezone.utc)
        try:
            # Try ISO format
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                # Try date-only
                ts = datetime.strptime(timestamp[:10], "%Y-%m-%d")
                ts = ts.replace(tzinfo=timezone.utc)
            except (ValueError, AttributeError):
                return self.config.max_age_days  # Unknown timestamp = max age

        delta = now - ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else now - ts
        return max(0, delta.total_seconds() / 86400)  # Convert to days

    def _step_weight(self, age_days: float) -> float:
        """Step decay weight based on age thresholds."""
        if age_days <= self.config.recent_window_days:
            return self.config.base_weight
        elif age_days <= self.config.older_window_days:
            return max(self.config.min_weight, self.config.base_weight * 0.5)
        else:
            return self.config.min_weight
