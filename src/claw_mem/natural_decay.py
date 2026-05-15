"""Natural Decay — Ebbinghaus-style memory importance decay for claw-mem v2.15.0."""

import logging
import math
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NaturalDecay:
    """Exponential decay with important memory protection.

    Applies Ebbinghaus forgetting curve to memory importance scores,
    while protecting highly salient memories from dropping below
    a minimum threshold.
    """

    def __init__(self, decay_rate: float = 0.1, min_importance_ratio: float = 0.3):
        self.decay_rate = decay_rate
        self.min_importance_ratio = min_importance_ratio

    def calculate_importance(self, memory: Dict, now: Optional[float] = None) -> float:
        """Calculate current importance applying decay.

        Args:
            memory: Dict with 'salience_score'/'importance' and 'timestamp'/'last_access'
            now: Current timestamp (defaults to time.time())

        Returns:
            Decayed importance score (0-1)
        """
        base = memory.get("salience_score", memory.get("importance", 0.5))
        ts = memory.get("timestamp", memory.get("last_access", time.time()))
        now = now or time.time()

        days = max(0, (now - ts) / 86400.0)
        decayed = base * math.exp(-self.decay_rate * days)
        protected = max(decayed, self.min_importance_ratio * base)

        return round(protected, 4)

    def apply_decay(self, memories: List[Dict]) -> List[Dict]:
        """Apply decay to all memories in-place and return sorted by importance."""
        now = time.time()
        for mem in memories:
            mem["importance"] = self.calculate_importance(mem, now)
        return sorted(memories, key=lambda m: m.get("importance", 0), reverse=True)
