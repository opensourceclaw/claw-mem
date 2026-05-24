"""
ConsolidationLoop — periodic memory consolidation from hippocampus to neocortex.

Simulates human sleep-based memory consolidation with periodic triggers,
importance-weighted selection, and cleanup of consolidated memories.
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ConsolidationResult:
    """Result of a consolidation cycle.

    Attributes:
        cycle_id: Unique cycle identifier.
        memories_consolidated: Number of memories moved to neocortex.
        concepts_abstracted: Number of concepts extracted.
        memories_cleaned: Number of memories cleaned from hippocampus.
        duration_ms: Cycle duration in milliseconds.
        timestamp: When the cycle occurred.
    """

    cycle_id: str = field(default_factory=lambda: str(uuid4()))
    memories_consolidated: int = 0
    concepts_abstracted: int = 0
    memories_cleaned: int = 0
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "memories_consolidated": self.memories_consolidated,
            "concepts_abstracted": self.concepts_abstracted,
            "memories_cleaned": self.memories_cleaned,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


class ConsolidationLoop:
    """Periodic consolidation from hippocampus to neocortex.

    Simulates sleep-based memory consolidation:
    - Cycles every configurable interval
    - Selects most important hippocampal memories
    - Consolidates to neocortex (abstraction + storage)
    - Cleans consolidated memories from hippocampus

    Usage::

        loop = ConsolidationLoop(hippocampal, neocortical, interval=3600)
        result = loop.run_consolidation()
        loop.start_background()
    """

    def __init__(
        self,
        hippocampal: Any,
        neocortical: Any,
        interval_seconds: int = 3600,
        batch_size: int = 100,
        importance_threshold: float = 0.3,
    ):
        """Initialize the consolidation loop.

        Args:
            hippocampal: HippocampalStore instance.
            neocortical: NeocorticalStore instance.
            interval_seconds: Consolidation interval in seconds.
            batch_size: Max memories per cycle.
            importance_threshold: Min importance for selection.
        """
        self._hippocampal = hippocampal
        self._neocortical = neocortical
        self._interval = interval_seconds
        self._batch_size = batch_size
        self._importance_threshold = importance_threshold

        self._history: List[ConsolidationResult] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def run_consolidation(self) -> ConsolidationResult:
        """Execute one consolidation cycle.

        1. Select most important hippocampal memories
        2. Consolidate to neocortex (abstract concepts + store)
        3. Clean consolidated memories from hippocampus

        Returns:
            ConsolidationResult with cycle statistics.
        """
        start = time.time()

        # 1. Select memories
        memories = self._hippocampal.get_pending_consolidation(
            min_importance=self._importance_threshold,
            limit=self._batch_size,
        )

        if not memories:
            result = ConsolidationResult(duration_ms=0)
            self._history.append(result)
            return result

        # 2. Consolidate to neocortex
        consolidated_ids = self._neocortical.consolidate(memories)
        concepts = self._neocortical.list_concepts()
        concepts_before = len(concepts) - (len(consolidated_ids) > 0 and 1 or 0)  # approximate

        # 3. Clean hippocampal memories
        cleaned = self._hippocampal.remove_batch(
            [getattr(m, "memory_id", "") for m in memories]
        )

        duration = (time.time() - start) * 1000
        concepts_after = self._neocortical.concept_count()
        result = ConsolidationResult(
            memories_consolidated=len(consolidated_ids),
            concepts_abstracted=max(0, concepts_after - concepts_before),
            memories_cleaned=cleaned,
            duration_ms=duration,
        )
        self._history.append(result)
        return result

    def start_background(self) -> None:
        """Start background consolidation thread.

        Runs consolidation cycles at the configured interval.
        Non-blocking — runs in a daemon thread.
        """
        if self._running:
            return

        self._running = True
        self._stop_event.clear()

        def _loop():
            while not self._stop_event.is_set():
                try:
                    self.run_consolidation()
                except Exception:
                    pass  # Don't crash the thread
                # Sleep in small increments so we can stop cleanly
                for _ in range(self._interval):
                    if self._stop_event.is_set():
                        break
                    time.sleep(1)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_background(self) -> None:
        """Stop the background consolidation thread."""
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    @property
    def is_running(self) -> bool:
        """Whether background consolidation is active."""
        return self._running

    def get_history(self) -> List[ConsolidationResult]:
        """Get consolidation cycle history."""
        return list(self._history)

    def get_statistics(self) -> Dict[str, Any]:
        """Get consolidation statistics."""
        total = len(self._history)
        total_consolidated = sum(r.memories_consolidated for r in self._history)
        total_concepts = sum(r.concepts_abstracted for r in self._history)
        return {
            "cycles_completed": total,
            "total_memories_consolidated": total_consolidated,
            "total_concepts_abstracted": total_concepts,
            "is_running": self._running,
            "interval_seconds": self._interval,
        }

    def reset(self) -> None:
        """Clear history and stop background thread."""
        self.stop_background()
        self._history.clear()
