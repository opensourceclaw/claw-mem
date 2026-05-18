# Copyright 2026 Peter Cheng
"""Compression strategy selector for CMS Phase 2 (v3.0.0-rc.2).

Selects optimal compression strategy based on capacity utilization
and recommends specific compression actions.
"""

from typing import Dict, Optional
from .compression_result import CompressionPlan


class CompressionStrategySelector:
    """Select compression strategy based on capacity utilization.

    Strategies:
      - aggressive:  utilization > 90%
        target 70% reduction, suggest dedup + summarize + archive
      - balanced:    75% < utilization <= 90%
        target 50% reduction, suggest dedup + summarize
      - conservative: utilization <= 75%
        target 20% reduction, suggest summarize only
    """

    def select(self, utilization: float, total_memories: int = 0) -> CompressionPlan:
        """Select compression strategy based on utilization.

        Args:
            utilization: Current capacity utilization (0.0-1.0).
            total_memories: Total memory count for savings estimate.

        Returns:
            CompressionPlan with strategy, target, and suggested actions.
        """
        if utilization > 0.90:
            return self._aggressive_plan(utilization, total_memories)
        elif utilization > 0.75:
            return self._balanced_plan(utilization, total_memories)
        else:
            return self._conservative_plan(utilization, total_memories)

    def _aggressive_plan(self, utilization: float, total: int) -> CompressionPlan:
        est_savings = int(total * 0.7 * 50)  # ~50 tokens/memory
        return CompressionPlan(
            strategy="aggressive",
            utilization=utilization,
            target_reduction=0.70,
            suggested_actions=["deduplicate", "summarize", "archive_expired"],
            estimated_token_savings=est_savings,
        )

    def _balanced_plan(self, utilization: float, total: int) -> CompressionPlan:
        est_savings = int(total * 0.5 * 50)
        return CompressionPlan(
            strategy="balanced",
            utilization=utilization,
            target_reduction=0.50,
            suggested_actions=["deduplicate", "summarize"],
            estimated_token_savings=est_savings,
        )

    def _conservative_plan(self, utilization: float, total: int) -> CompressionPlan:
        est_savings = int(total * 0.2 * 50)
        return CompressionPlan(
            strategy="conservative",
            utilization=utilization,
            target_reduction=0.20,
            suggested_actions=["summarize"],
            estimated_token_savings=est_savings,
        )
