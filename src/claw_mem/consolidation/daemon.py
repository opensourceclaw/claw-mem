"""
claw-mem v2.10.0 - Consolidation Daemon

Periodic background process for weight consolidation.
"""

import time
import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


@dataclass
class DaemonConfig:
    interval_seconds: float = 3600.0  # 1 hour
    batch_size: int = 8
    enabled: bool = True
    run_on_start: bool = False


class ConsolidationDaemon:
    """Background daemon for periodic weight consolidation.

    Usage:
        daemon = ConsolidationDaemon(
            queue=queue, consolidator=consolidator, classifier=classifier,
        )
        daemon.start()
    """

    def __init__(
        self,
        queue: Any = None,
        consolidator: Any = None,
        classifier: Any = None,
        detector: Any = None,
        config: Optional[DaemonConfig] = None,
    ):
        self.queue = queue
        self.consolidator = consolidator
        self.classifier = classifier
        self.detector = detector
        self.config = config or DaemonConfig()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._cycles = 0
        self._last_run: Optional[str] = None
        self._on_complete: Optional[Callable] = None

    def start(self):
        """Start the daemon in a background thread."""
        if not self.config.enabled:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the daemon."""
        self._running = False

    def run_once(self) -> Dict[str, Any]:
        """Execute one consolidation cycle."""
        self._cycles += 1
        now = datetime.utcnow().isoformat()
        self._last_run = now

        if not self.queue or not self.classifier:
            return {"consolidated": False, "reason": "Missing components"}

        if self.queue.size == 0:
            return {"consolidated": False, "reason": "Queue empty"}

        batch = self.queue.dequeue_batch(self.config.batch_size)

        # Security check: filter injection attempts
        if self.detector:
            safe_batch = [
                e for e in batch
                if self.detector.is_safe(e.get("content", ""))
            ]
            if len(safe_batch) < len(batch):
                from datetime import datetime as dt
        else:
            safe_batch = batch

        # Classify experiences
        classified = []
        for exp in safe_batch:
            result = self.classifier.classify(exp)
            if result.should_consolidate:
                classified.append(exp)

        # Consolidate
        if self.consolidator and classified:
            result = self.consolidator.consolidate(classified)
            if self._on_complete:
                self._on_complete(result)
            return result

        return {"consolidated": False, "reason": "No experiences to consolidate"}

    def _run_loop(self):
        """Main daemon loop."""
        if self.config.run_on_start:
            self.run_once()

        while self._running:
            time.sleep(self.config.interval_seconds)
            if not self._running:
                break
            self.run_once()

    def on_complete(self, callback: Callable):
        """Register a callback for consolidation completion."""
        self._on_complete = callback

    def get_stats(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "cycles": self._cycles,
            "last_run": self._last_run,
            "config": {
                "interval_seconds": self.config.interval_seconds,
                "enabled": self.config.enabled,
            },
        }
