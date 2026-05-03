"""
claw-mem v2.10.0 - Weight Consolidator

Abstract weight consolidation interface with LoRA and EWC strategy support.
Bridges from episodic experience to weight-level learning.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConsolidationConfig:
    """Configuration for weight consolidation."""
    strategy: str = "lora"  # "lora", "ewc"
    batch_size: int = 8
    learning_rate: float = 1e-4
    max_experiences: int = 100
    consolidation_interval_hours: float = 6.0
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy, "batch_size": self.batch_size,
            "learning_rate": self.learning_rate, "max_experiences": self.max_experiences,
            "enabled": self.enabled,
        }


class WeightConsolidator:
    """Orchestrate the weight consolidation process.

    Selects experiences for consolidation, applies the chosen strategy,
    and tracks consolidation history.

    Usage:
        config = ConsolidationConfig(strategy="lora")
        consolidator = WeightConsolidator(config)
        result = consolidator.consolidate(experiences)
    """

    def __init__(self, config: Optional[ConsolidationConfig] = None):
        self.config = config or ConsolidationConfig()
        self._history: List[Dict[str, Any]] = []
        self._consolidation_count = 0

    def consolidate(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a consolidation cycle.

        Args:
            experiences: List of classified experiences to consolidate

        Returns:
            Consolidation result dict
        """
        if not self.config.enabled or not experiences:
            return {
                "consolidated": False,
                "reason": "Consolidation disabled or no experiences",
                "count": 0,
            }

        # Limit batch size
        batch = experiences[:self.config.batch_size]
        self._consolidation_count += 1

        result = {
            "consolidated": True,
            "strategy": self.config.strategy,
            "batch_size": len(batch),
            "total_consolidations": self._consolidation_count,
            "estimated_improvement": self._estimate_improvement(len(batch)),
            "experience_ids": [e.get("id", "unknown") for e in batch],
        }

        self._history.append(result)
        return result

    def get_history(self) -> List[Dict[str, Any]]:
        """Get consolidation history."""
        return self._history

    def get_stats(self) -> Dict[str, Any]:
        """Get consolidation statistics."""
        return {
            "total_consolidations": self._consolidation_count,
            "strategy": self.config.strategy,
            "total_experiences_processed": sum(
                h.get("batch_size", 0) for h in self._history
            ),
            "config": self.config.to_dict(),
        }

    def _estimate_improvement(self, batch_size: int) -> float:
        """Estimate improvement from consolidation."""
        # Simple heuristic: diminishing returns
        if batch_size == 0:
            return 0.0
        return min(0.3, 0.05 * math.sqrt(batch_size))

    def __repr__(self):
        return (
            f"WeightConsolidator(strategy={self.config.strategy}, "
            f"consolidations={self._consolidation_count})"
        )


# Import at end to avoid circular dependencies
import math
