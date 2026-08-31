// claw-mem v7.5.0 — RetentionScoreEngine unit tests (ADR-002)
// Licensed under the Apache License, Version 2.0

import { describe, expect, it } from "vitest";
import { RetentionScoreEngine, DEFAULT_RETENTION_CONFIG } from "../../src/retention/retention-engine";

const RHO = DEFAULT_RETENTION_CONFIG.rho; // 0.85
const BOOST = DEFAULT_RETENTION_CONFIG.selectedBoost; // 0.1

describe("RetentionScoreEngine", () => {
  describe("initialize", () => {
    it("initializes success outcome to 0.75", () => {
      const engine = new RetentionScoreEngine();
      const state = engine.initialize("m1", "success");
      expect(state.score).toBe(0.75);
      expect(state.missedStreak).toBe(0);
      expect(state.initializedAt).toBeDefined();
    });

    it("initializes failure outcome to 0.30", () => {
      const engine = new RetentionScoreEngine();
      expect(engine.initialize("m2", "failure").score).toBe(0.3);
    });

    it("initializes without outcome to neutral 0.5", () => {
      const engine = new RetentionScoreEngine();
      expect(engine.initialize("m3").score).toBe(0.5);
    });

    it("re-initialize overwrites existing state", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success");
      const state = engine.initialize("m1", "failure");
      expect(state.score).toBe(0.3);
    });
  });

  describe("onSelected", () => {
    it("boosts score by 0.1 and resets missedStreak", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success");
      const state = engine.onSelected("m1");
      expect(state.score).toBeCloseTo(0.85);
      expect(state.missedStreak).toBe(0);
    });

    it("caps score at 1.0 (clip upper bound)", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success");
      engine.onSelected("m1"); // 0.85
      engine.onSelected("m1"); // 0.95
      const state = engine.onSelected("m1"); // would be 1.05 → 1.0
      expect(state.score).toBe(1.0);
      expect(state.score).toBeLessThanOrEqual(1.0);
    });

    it("records lastSelected timestamp", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1");
      const state = engine.onSelected("m1");
      expect(state.lastSelected).toBeDefined();
      expect(new Date(state.lastSelected).getTime()).not.toBeNaN();
    });

    it("recovers from a missed streak (streak cleared, boost applied)", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success"); // 0.75
      engine.onCandidateMissed("m1"); // ×ρ^1
      engine.onCandidateMissed("m1"); // ×ρ^2
      const state = engine.onSelected("m1");
      expect(state.missedStreak).toBe(0);
      expect(state.score).toBeCloseTo(0.75 * Math.pow(RHO, 1 + 2) + BOOST, 5);
    });
  });

  describe("onCandidateMissed", () => {
    it("increments streak first, then decays by rho^min(m, M)", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success"); // 0.75
      const first = engine.onCandidateMissed("m1"); // m=1
      expect(first.missedStreak).toBe(1);
      expect(first.score).toBeCloseTo(0.75 * Math.pow(RHO, 1), 5);
    });

    it("decays geometrically over consecutive misses (cumulative exponents)", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success"); // 0.75
      let state = engine.onCandidateMissed("m1"); // ×ρ^1
      state = engine.onCandidateMissed("m1"); // ×ρ^2
      state = engine.onCandidateMissed("m1"); // ×ρ^3
      expect(state.missedStreak).toBe(3);
      expect(state.score).toBeCloseTo(0.75 * Math.pow(RHO, 1 + 2 + 3), 5);
    });

    it("acceptance anchor: 5 consecutive misses drops score to <= 0.5 * initial", () => {
      const engine = new RetentionScoreEngine();
      let state = engine.initialize("m1", "success"); // 0.75
      for (let i = 0; i < 5; i++) state = engine.onCandidateMissed("m1");
      expect(state.missedStreak).toBe(5);
      expect(state.score).toBeLessThanOrEqual(0.5 * 0.75);
      expect(state.score).toBeCloseTo(0.75 * Math.pow(RHO, 15), 5);
    });

    it("caps streak contribution at M: misses beyond M keep decaying at rho^M rate", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1"); // 0.5
      for (let i = 0; i < 5; i++) engine.onCandidateMissed("m1");
      const afterM = engine.getState("m1")!.score;
      const beforeM6 = engine.onCandidateMissed("m1").score;
      const afterM6 = engine.onCandidateMissed("m1").score;
      expect(beforeM6).toBeCloseTo(afterM * Math.pow(RHO, 5), 5);
      expect(afterM6).toBeCloseTo(afterM * Math.pow(RHO, 5) * Math.pow(RHO, 5), 5);
      expect(engine.getState("m1")!.missedStreak).toBe(7);
    });

    it("never drops below 0 (clip lower bound): repeated decay stays positive", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "failure"); // 0.30
      let state = engine.initialize("m1", "failure");
      for (let i = 0; i < 100; i++) state = engine.onCandidateMissed("m1");
      expect(state.score).toBeGreaterThan(0);
      expect(state.score).toBeLessThan(0.3);
      expect(state.score).toBeLessThan(1e-6);
    });

    it("decays from score=1 correctly (clip upper bound does not stick)", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1");
      for (let i = 0; i < 6; i++) engine.onSelected("m1"); // 0.5 → 1.0 (capped)
      const state = engine.onCandidateMissed("m1");
      expect(state.score).toBeCloseTo(1.0 * Math.pow(RHO, 1), 5);
    });
  });

  describe("getRetentionScore", () => {
    it("returns neutral 0.5 for unknown ids", () => {
      const engine = new RetentionScoreEngine();
      expect(engine.getRetentionScore("ghost")).toBe(0.5);
    });

    it("returns live score for known ids", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("m1", "success");
      expect(engine.getRetentionScore("m1")).toBe(0.75);
    });
  });

  describe("lazy initialization", () => {
    it("onSelected on unknown id initializes from neutral 0.5 then applies boost", () => {
      const engine = new RetentionScoreEngine();
      const state = engine.onSelected("ghost");
      expect(state.score).toBeCloseTo(0.5 + BOOST, 5);
      expect(state.missedStreak).toBe(0);
      expect(state.lastSelected).toBeDefined();
    });

    it("onCandidateMissed on unknown id initializes from neutral 0.5 then decays", () => {
      const engine = new RetentionScoreEngine();
      const state = engine.onCandidateMissed("ghost");
      expect(state.missedStreak).toBe(1);
      expect(state.score).toBeCloseTo(0.5 * Math.pow(RHO, 1), 5);
    });

    it("getRetentionScore does not create state (read-only)", () => {
      const engine = new RetentionScoreEngine();
      engine.getRetentionScore("ghost");
      expect(engine.size()).toBe(0);
    });
  });

  describe("state persistence bridge", () => {
    it("setState hydrates and getState reads back the same state", () => {
      const engine = new RetentionScoreEngine();
      engine.setState("m1", { score: 0.61, missedStreak: 2, lastSelected: "2026-08-31T00:00:00.000Z", initializedAt: "2026-07-01T00:00:00.000Z" });
      const state = engine.getState("m1")!;
      expect(state.score).toBe(0.61);
      expect(state.missedStreak).toBe(2);
      expect(engine.getRetentionScore("m1")).toBe(0.61);
    });

    it("getState returns null for uninitialized ids", () => {
      const engine = new RetentionScoreEngine();
      expect(engine.getState("ghost")).toBeNull();
    });
  });

  describe("getStats (memory_stats distribution)", () => {
    it("returns zeros for empty engine", () => {
      const engine = new RetentionScoreEngine();
      expect(engine.getStats()).toEqual({ count: 0, mean: 0, median: 0, belowThreshold: 0, threshold: 0.3 });
    });

    it("computes mean/median/below-threshold over live states", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("a", "success"); // 0.75
      engine.initialize("b", "failure"); // 0.30
      engine.initialize("c"); // 0.5
      let d = engine.initialize("d", "success"); // 0.75 → decayed below 0.3
      for (let i = 0; i < 3; i++) d = engine.onCandidateMissed("d"); // 0.75·ρ^6≈0.283
      expect(d.score).toBeLessThan(0.3);
      const stats = engine.getStats();
      expect(stats.count).toBe(4);
      expect(stats.mean).toBeCloseTo((0.75 + 0.3 + 0.5 + d.score) / 4, 5);
      expect(stats.median).toBeCloseTo((0.3 + 0.5) / 2, 5);
      expect(stats.belowThreshold).toBe(1);
    });

    it("threshold boundary: score equal to threshold is not below", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("b", "failure"); // exactly 0.30 == threshold
      const stats = engine.getStats();
      expect(stats.belowThreshold).toBe(0);
    });

    it("even count median is the midpoint of the two middle scores", () => {
      const engine = new RetentionScoreEngine();
      engine.initialize("a", "success"); // 0.75
      engine.initialize("b", "failure"); // 0.30
      const stats = engine.getStats();
      expect(stats.median).toBeCloseTo((0.75 + 0.3) / 2, 5);
    });
  });
});
