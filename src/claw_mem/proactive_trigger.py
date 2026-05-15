"""Proactive Trigger — time/event-based memory recall triggers for claw-mem v2.15.0."""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProactiveTrigger:
    """Time and event-based proactive memory triggers.

    Use cases:
    - "Remind me next Monday" → time trigger
    - "When we discuss Project Neo" → event trigger
    """

    def __init__(self):
        self._time_triggers: List[Dict] = []
        self._event_triggers: List[Dict] = []

    def add_time_trigger(self, memory_id: str, trigger_time: float, message: str) -> str:
        """Add a time-based trigger."""
        tid = f"time_{len(self._time_triggers)}"
        self._time_triggers.append({
            "id": tid, "type": "time", "memory_id": memory_id,
            "trigger_time": trigger_time, "message": message, "fired": False,
        })
        logger.debug("Time trigger added: %s for %s", message, memory_id)
        return tid

    def add_event_trigger(self, memory_id: str, event_pattern: str, message: str) -> str:
        """Add an event-based trigger (e.g., 'mention:Project Neo')."""
        tid = f"event_{len(self._event_triggers)}"
        self._event_triggers.append({
            "id": tid, "type": "event", "memory_id": memory_id,
            "event_pattern": event_pattern, "message": message, "fired": False,
        })
        return tid

    def check_triggers(self, context: Optional[Dict] = None) -> List[Dict]:
        """Check all triggers and return triggered ones."""
        triggered = []
        now = time.time()
        context_text = " ".join(str(v) for v in (context or {}).values()).lower()

        # Check time triggers
        for t in self._time_triggers:
            if not t["fired"] and now >= t["trigger_time"]:
                t["fired"] = True
                triggered.append(t)

        # Check event triggers
        for t in self._event_triggers:
            if not t["fired"]:
                pattern = t["event_pattern"].lower()
                if pattern.startswith("mention:"):
                    keyword = pattern[8:].strip()
                    if keyword in context_text:
                        t["fired"] = True
                        triggered.append(t)
                elif pattern in context_text:
                    t["fired"] = True
                    triggered.append(t)

        return triggered

    def get_pending(self) -> List[Dict]:
        """Get unfired triggers."""
        return [t for t in self._time_triggers + self._event_triggers if not t["fired"]]
