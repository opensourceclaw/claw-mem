"""Oblivion: Memory Decay and Forgetting Control."""

import logging
import math
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReadGate:
    """Uncertainty-gated retrieval filter."""

    def filter(
        self, results: List[Dict], threshold: float = 0.3
    ) -> List[Dict]:
        """Filter results below confidence/accessibility threshold."""
        return [r for r in results if r.get("accessibility", r.get("score", 1.0)) >= threshold]


class WriteGate:
    """Feedback-driven write control."""

    def should_store(
        self, content: str, feedback: Optional[float] = None
    ) -> bool:
        """Decide whether to store based on content significance."""
        if not content or len(str(content).strip()) < 3:
            return False
        if feedback is not None and feedback < 0.3:
            return False
        return True


class DecayController:
    """Oblivion: Ebbinghaus-style memory decay and forgetting.

    Implements:
    - DecayScheduler: time-based accessibility decay
    - ReadGate: uncertainty-gated retrieval
    - WriteGate: feedback-driven storage decisions
    """

    def __init__(
        self,
        decay_rate: float = 0.1,
        decay_period: int = 86400,
        forget_threshold: float = 0.1,
    ):
        self.decay_rate = decay_rate
        self.decay_period = decay_period  # seconds (default: 1 day)
        self.forget_threshold = forget_threshold
        self.read_gate = ReadGate()
        self.write_gate = WriteGate()

    def apply_decay(self, memories: List[Dict]) -> List[Dict]:
        """Apply Ebbinghaus-style decay to memories.

        accessibility = exp(-t / (period / rate))
        """
        now = time.time()
        for mem in memories:
            timestamp = mem.get("timestamp", now)
            elapsed = max(0, now - timestamp)
            periods = elapsed / self.decay_period
            accessibility = math.exp(-periods * self.decay_rate)
            mem["accessibility"] = round(accessibility, 4)
            if accessibility < self.forget_threshold:
                mem["_forgotten"] = True
        return memories

    def get_accessibility(
        self, memory: Dict, last_access: Optional[float] = None
    ) -> float:
        """Compute current accessibility of a memory."""
        ts = last_access or memory.get("timestamp", time.time())
        elapsed = max(0, time.time() - ts)
        periods = elapsed / self.decay_period
        return round(math.exp(-periods * self.decay_rate), 4)

    def should_forget(self, memory: Dict) -> bool:
        """Check if a memory should be forgotten."""
        acc = self.get_accessibility(memory)
        return acc < self.forget_threshold

    def get_forgettable(
        self, memories: List[Dict]
    ) -> List[Dict]:
        """Return memories that should be forgotten."""
        return [m for m in memories if self.should_forget(m)]
