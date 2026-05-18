# Copyright 2026 Peter Cheng
"""Context warning hook for CMS Perception Layer (v3.0.0-rc.1).

Emits warnings when memory capacity exceeds configured thresholds,
with cooldown to prevent warning spam.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class WarningEvent:
    """Context capacity warning event."""
    severity: str           # "info" / "warning" / "critical"
    message: str
    utilization: float
    threshold: float
    total_memories: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "message": self.message,
            "utilization": round(self.utilization, 4),
            "threshold": round(self.threshold, 4),
            "total_memories": self.total_memories,
            "timestamp": self.timestamp.isoformat(),
        }


class ContextWarningHook:
    """Emits capacity warnings on a cooldown timer.

    Hooks into store() calls to check capacity and emit
    WarningEvent when thresholds are exceeded.
    """

    def __init__(self, capacity_monitor,
                 cooldown_seconds: int = 300):
        self._monitor = capacity_monitor
        self._cooldown_seconds = cooldown_seconds
        self._last_warning_time: float = 0.0
        self._warning_count: int = 0
        self._store_count: int = 0

    def check_and_emit(self) -> Optional[WarningEvent]:
        """Check capacity and emit warning if needed (with cooldown)."""
        stats = self._monitor.check()
        if stats is None:
            return None

        now = time.time()
        if now - self._last_warning_time < self._cooldown_seconds:
            return None  # cooldown period

        severity = self._determine_severity(stats.utilization)
        message = (
            f"Memory capacity at {stats.utilization:.0%}. "
            f"Total: {stats.total_memories} memories. "
            f"Consider compressing or archiving old memories."
        )

        event = WarningEvent(
            severity=severity,
            message=message,
            utilization=stats.utilization,
            threshold=self._monitor._warning_level,
            total_memories=stats.total_memories,
        )

        self._last_warning_time = now
        self._warning_count += 1
        return event

    def on_memory_stored(self, memory_id: str = "") -> None:
        """Hook called after each memory store."""
        self._store_count += 1
        # Check every 10 stores
        if self._store_count % 10 == 0:
            return self.check_and_emit()
        return None

    def _determine_severity(self, utilization: float) -> str:
        if utilization >= 0.95:
            return "critical"
        elif utilization >= 0.85:
            return "warning"
        return "info"

    def get_stats(self) -> dict:
        return {
            "warning_count": self._warning_count,
            "store_count": self._store_count,
            "last_warning_time": self._last_warning_time,
            "cooldown_seconds": self._cooldown_seconds,
        }
