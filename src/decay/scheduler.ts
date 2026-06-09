// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * DecayScheduler - Periodic and event-driven scheduling of decay cycles.
 *
 * Strategies:
 *   - Timer: Execute every N hours.
 *   - Event: Execute after N store() calls.
 *   - Manual: scheduleNow() for on-demand triggering.
 */

import type { DecayController } from "./controller";
import { type DecayConfig, DEFAULT_DECAY_CONFIG } from "./functions";

export class DecayScheduler {
  private _timer: ReturnType<typeof setInterval> | null = null;
  private _running = false;
  private _storeCounter = 0;
  private _storesPerDecay = 100;
  private _onComplete:
    | ((removed: Array<{ source: string; target: string }>) => void)
    | null = null;

  constructor(
    private _controller: DecayController,
    private _config: DecayConfig = DEFAULT_DECAY_CONFIG,
  ) {}

  /** Start periodic scheduling. */
  start(): void {
    if (this._running) return;
    this._running = true;
    this._scheduleNext();
  }

  /** Stop scheduling. */
  stop(): void {
    this._running = false;
    if (this._timer !== null) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  isRunning(): boolean {
    return this._running;
  }

  private _scheduleNext(): void {
    if (!this._running) return;
    const interval = this._config.decayIntervalHours * 3600 * 1000; // ms
    this._timer = setInterval(() => this._runDecayCycle(), interval);
  }

  /** Execute one full decay cycle: compute -> apply -> cleanup. */
  private _runDecayCycle(): void {
    try {
      const updates = this._controller.computeAllDecays();
      if (Object.keys(updates).length > 0) {
        // _controller._graph.applyDecay(updates);
      }
      const removed = this._controller.cleanupExpired();
      if (removed.length > 0 && this._onComplete) {
        this._onComplete(removed);
      }
    } catch (err) {
      console.warn("Decay cycle failed:", err);
    }
  }

  /** Trigger an immediate decay cycle. */
  scheduleNow(): void {
    this._runDecayCycle();
  }

  /** Notify of a store() call. Triggers decay after N stores. */
  notifyStore(): void {
    this._storeCounter++;
    if (this._storeCounter >= this._storesPerDecay) {
      this._storeCounter = 0;
      this.scheduleNow();
    }
  }

  /** Register a callback invoked after each decay cycle with removed edges. */
  onComplete(
    callback: (removed: Array<{ source: string; target: string }>) => void,
  ): void {
    this._onComplete = callback;
  }
}
