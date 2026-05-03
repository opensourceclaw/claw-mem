# claw-mem v2.9.1 - Temporal Module
#
# Time-aware search: applies time weighting to search results,
# boosting recent memories and decaying older ones.

from .time_aware import TimeWeightCalculator, TimeWeightConfig

__all__ = ["TimeWeightCalculator", "TimeWeightConfig"]
