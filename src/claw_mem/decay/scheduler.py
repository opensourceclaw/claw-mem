# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
DecayScheduler - Periodic and event-driven scheduling of decay cycles.

Strategies:
  - Timer: Execute every N hours.
  - Event: Execute after N store() calls.
  - Manual: schedule_now() for on-demand triggering.
"""

import threading
import logging
from typing import Callable, List, Optional, Tuple

from claw_mem.decay.controller import DecayController
from claw_mem.decay.functions import DecayConfig

logger = logging.getLogger("claw_mem.decay")


class DecayScheduler:
    """Schedules decay cycles on a background daemon thread.

    The single-threaded execution avoids concurrent modifications
    to the graph structure.
    """

    def __init__(self, controller: DecayController,
                 config: DecayConfig = None):
        self._controller = controller
        self._config = config or DecayConfig.default()
        self._timer: Optional[threading.Timer] = None
        self._running = False
        self._store_counter: int = 0
        self._stores_per_decay: int = 100
        self._on_complete: Optional[Callable[[List[Tuple[str, str]]], None]] = None

    def start(self) -> None:
        """Start periodic scheduling."""
        self._running = True
        self._schedule_next()

    def stop(self) -> None:
        """Stop scheduling. Waits for current cycle to finish."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def is_running(self) -> bool:
        return self._running

    def _schedule_next(self) -> None:
        if not self._running:
            return
        interval = self._config.decay_interval_hours * 3600
        self._timer = threading.Timer(interval, self._run_decay_cycle)
        self._timer.daemon = True
        self._timer.start()

    def _run_decay_cycle(self) -> None:
        """Execute one full decay cycle: compute → apply → cleanup."""
        try:
            updates = self._controller.compute_all_decays()
            if updates:
                self._controller._graph.apply_decay(updates)
            removed = self._controller.cleanup_expired()
            if removed and self._on_complete:
                self._on_complete(removed)
        except Exception:
            logger.warning("Decay cycle failed", exc_info=True)
        finally:
            if self._running:
                self._schedule_next()

    def schedule_now(self) -> None:
        """Trigger an immediate decay cycle (non-blocking)."""
        threading.Thread(target=self._run_decay_cycle, daemon=True).start()

    def notify_store(self) -> None:
        """Notify of a store() call. Triggers decay after N stores."""
        self._store_counter += 1
        if self._store_counter >= self._stores_per_decay:
            self._store_counter = 0
            self.schedule_now()

    def on_complete(self, callback: Callable[[List[Tuple[str, str]]], None]) -> None:
        """Register a callback invoked after each decay cycle with removed edges."""
        self._on_complete = callback
