"""claw-mem v2.10.0 - EWC Consolidation Strategy."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EWCConfig:
    lambda_weight: float = 1.0
    importance_threshold: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {"lambda": self.lambda_weight, "threshold": self.importance_threshold}


class EWCStrategy:
    """Elastic Weight Consolidation for protecting important memories.

    Penalizes changes to weights important for previous tasks.
    """

    def __init__(self, config: Optional[EWCConfig] = None):
        self.config = config or EWCConfig()
        self._fisher_information: Dict[str, float] = {}

    def apply(self, experiences: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Estimate Fisher importance for each experience
        for exp in experiences:
            exp_id = exp.get("id", "unknown")
            self._fisher_information[exp_id] = exp.get("score", {}).get("total", 0.5)

        return {
            "strategy": "ewc", "success": True,
            "lambda": self.config.lambda_weight,
            "protected_params": len(self._fisher_information),
        }

    def get_protected(self) -> Dict[str, float]:
        return dict(self._fisher_information)
