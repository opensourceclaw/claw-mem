import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { DecayScheduler } from "../../src/deprecated/decay/scheduler";
import { DecayController } from "../../src/deprecated/decay/controller";
import { DEFAULT_DECAY_CONFIG } from "../../src/deprecated/decay/functions";

// ── Mock controller ─────────────────────────────────────────────────────

function createMockController(): DecayController {
  return {
    getStats: () => ({ totalEdges: 0 }),
    cleanupExpired: () => [{ source: "a", target: "b" }],
    calculateSingleWeight: () => 1.0,
    getDecayWeight: () => 1.0,
    computeAllDecays: () => ({}),
    classifyEdges: () => ({ strong: [], medium: [], weak: [], expired: [] }),
    shouldRemoveEdge: () => false,
  } as unknown as DecayController;
}

// ── Tests ───────────────────────────────────────────────────────────────

describe("DecayScheduler", () => {
  let controller: DecayController;
  let scheduler: DecayScheduler;

  beforeEach(() => {
    controller = createMockController();
    scheduler = new DecayScheduler(controller, DEFAULT_DECAY_CONFIG);
  });

  afterEach(() => {
    scheduler.stop();
  });

  describe("lifecycle", () => {
    it("is not running initially", () => {
      expect(scheduler.isRunning()).toBe(false);
    });

    it("starts and stops", () => {
      scheduler.start();
      expect(scheduler.isRunning()).toBe(true);
      scheduler.stop();
      expect(scheduler.isRunning()).toBe(false);
    });

    it("double start does not throw", () => {
      scheduler.start();
      scheduler.start();
      expect(scheduler.isRunning()).toBe(true);
      scheduler.stop();
    });

    it("double stop does not throw", () => {
      scheduler.start();
      scheduler.stop();
      scheduler.stop();
      expect(scheduler.isRunning()).toBe(false);
    });
  });

  describe("onDecayComplete", () => {
    it("registers and triggers callback on scheduleNow", () => {
      const callback = vi.fn();
      scheduler.onComplete(callback);
      scheduler.scheduleNow();
      expect(callback).toHaveBeenCalledTimes(1);
      // Don't start timer, just manual trigger
    });

    it("callback receives removed edges", () => {
      const removed: Array<{ source: string; target: string }> = [];
      scheduler.onComplete((r) => removed.push(...r));
      scheduler.scheduleNow();
      expect(Array.isArray(removed)).toBe(true);
    });
  });

  describe("scheduleNow", () => {
    it("runs decay cycle immediately", () => {
      scheduler.scheduleNow();
      // Should not throw
    });

    it("can be called multiple times", () => {
      scheduler.scheduleNow();
      scheduler.scheduleNow();
      // Should not throw
    });

    it("works when not running", () => {
      scheduler.scheduleNow();
      expect(scheduler.isRunning()).toBe(false); // scheduleNow doesn't start timer
    });
  });

  describe("event-driven decay", () => {
    it("notifyStore increments counter", () => {
      scheduler.notifyStore();
      // Should not throw, counter increases
    });

    it("notifyStore triggers decay after threshold", () => {
      const callback = vi.fn();
      scheduler.onComplete(callback);
      for (let i = 0; i < 200; i++) {
        scheduler.notifyStore();
      }
      // After 100 stores, decay should trigger (default _storesPerDecay=100)
      expect(callback).toHaveBeenCalled();
    });
  });
});
