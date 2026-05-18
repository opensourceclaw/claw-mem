# Copyright 2026 Peter Cheng
"""Capacity monitor for CMS Perception Layer (v3.0.0-rc.1).

Tracks memory and token capacity in real-time, providing utilization
statistics and growth trends for context warning decisions.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CapacityStats:
    """Memory capacity snapshot."""

    total_memories: int
    total_tokens: int
    by_type: Dict[str, int] = field(default_factory=dict)
    utilization: float = 0.0
    threshold: int = 8000
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "total_memories": self.total_memories,
            "total_tokens": self.total_tokens,
            "by_type": self.by_type,
            "utilization": round(self.utilization, 4),
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CapacityTrend:
    """Capacity trend over time."""

    samples: List[CapacityStats] = field(default_factory=list)
    growth_rate: float = 0.0  # memories / operation
    estimated_time_to_full: float = 0.0  # seconds

    def to_dict(self) -> dict:
        return {
            "samples": [s.to_dict() for s in self.samples[-10:]],
            "growth_rate": round(self.growth_rate, 4),
            "estimated_time_to_full_s": round(self.estimated_time_to_full, 1),
        }


class CapacityMonitor:
    """Real-time memory capacity tracker.

    Monitors total memory count, estimated token count, per-type
    breakdown, and utilization ratio against configured thresholds.
    """

    def __init__(
        self,
        memory_manager=None,
        token_threshold: int = 8000,
        memory_threshold: int = 1000,
        warning_level: float = 0.8,
    ):
        self._mm = memory_manager
        self._token_threshold = token_threshold
        self._memory_threshold = memory_threshold
        self._warning_level = warning_level
        self._samples: List[CapacityStats] = []

    def get_stats(self) -> CapacityStats:
        """Collect current capacity statistics."""
        total_memories = 0
        total_tokens = 0
        by_type: Dict[str, int] = {}

        if self._mm:
            try:
                total_memories += self._mm.episodic.count()
                by_type["episodic"] = total_memories
            except Exception:
                pass
            try:
                sc = self._mm.semantic.count()
                total_memories += sc
                by_type["semantic"] = sc
            except Exception:
                pass
            try:
                pc = self._mm.procedural.count()
                total_memories += pc
                by_type["procedural"] = pc
            except Exception:
                pass
            total_tokens = total_memories * 50  # rough estimate

        utilization = total_memories / max(1, self._memory_threshold)

        stats = CapacityStats(
            total_memories=total_memories,
            total_tokens=total_tokens,
            by_type=by_type,
            utilization=min(1.0, utilization),
            threshold=self._memory_threshold,
            timestamp=datetime.now(),
        )
        self._samples.append(stats)
        return stats

    def get_trend(self) -> CapacityTrend:
        """Analyze capacity growth trend."""
        if len(self._samples) < 2:
            stats = self.get_stats()
            self._samples.append(stats)
            return CapacityTrend(samples=list(self._samples))

        recent = self._samples[-10:]
        if len(recent) >= 2:
            first = recent[0]
            last = recent[-1]
            ops = max(1, len(recent) - 1)
            growth_rate = (last.total_memories - first.total_memories) / ops

            remaining = self._memory_threshold - last.total_memories
            eta = (remaining / growth_rate * 60) if growth_rate > 0 else float("inf")
        else:
            growth_rate = 0.0
            eta = float("inf")

        return CapacityTrend(
            samples=list(recent),
            growth_rate=growth_rate,
            estimated_time_to_full=eta,
        )

    def should_warn(self, stats: Optional[CapacityStats] = None) -> bool:
        """Check if warning should be emitted."""
        if stats is None:
            stats = self.get_stats()
        return stats.utilization >= self._warning_level

    def check(self) -> Optional[CapacityStats]:
        """Check capacity and return stats if warning needed."""
        stats = self.get_stats()
        if self.should_warn(stats):
            return stats
        return None
