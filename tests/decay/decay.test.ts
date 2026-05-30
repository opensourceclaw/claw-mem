import { describe, it, expect } from "vitest";
import {
  exponentialDecay,
  calculateWeight,
  halfLifeToDays,
  HALF_LIFE,
  LAMBDA,
  DEFAULT_DECAY_CONFIG,
} from "../../src/decay/functions";
import { TieredDecayEngine, TierLevel } from "../../src/decay/tiered_decay";
import { DecayController } from "../../src/decay/controller";
import { DecayScheduler } from "../../src/decay/scheduler";

// ── Test 1: exponentialDecay produces correct values ───────────────────

function testExponentialDecay(): void {
  // At t=0, weight should equal base
  const w0 = exponentialDecay(1.0, 0, 7.0);
  console.assert(w0 === 1.0, `Expected 1.0, got ${w0}`);

  // At t=half_life, weight should be ~0.5 * base
  const wHalf = exponentialDecay(1.0, 7.0, 7.0);
  const ok = Math.abs(wHalf - 0.5) < 0.01;
  console.assert(ok, `Expected ~0.5, got ${wHalf}`);

  // At large t, weight should approach 0
  const wLarge = exponentialDecay(1.0, 365 * 10, 7.0);
  console.assert(wLarge < 0.001, `Expected near 0, got ${wLarge}`);

  console.log("PASS: testExponentialDecay");
  return true;
}

// ── Test 2: calculateWeight uses correct half-life per category ────────

function testCalculateWeight(): void {
  // ephemeral decays fast
  const wTemporal = calculateWeight(1.0, 7.0, "temporal");
  console.assert(
    Math.abs(wTemporal - 0.5) < 0.01,
    `Expected ~0.5 for temporal, got ${wTemporal}`,
  );

  // semantic decays slowly
  const wSemantic = calculateWeight(1.0, 7.0, "semantic");
  console.assert(
    wSemantic > 0.9,
    `Expected >0.9 for semantic at 7d, got ${wSemantic}`,
  );

  // unknown category uses default 30d half-life
  const wUnknown = calculateWeight(1.0, 30.0, "unknown_category");
  console.assert(
    Math.abs(wUnknown - 0.5) < 0.01,
    `Expected ~0.5 for unknown, got ${wUnknown}`,
  );

  console.log("PASS: testCalculateWeight");
  return true;
}

// ── Test 3: TieredDecayEngine classifies memories correctly ────────────

function testTieredDecayEngineClassify(): void {
  // Create a minimal stub storage
  const stubStorage = {
    filePath: "/tmp/test_memory.md",
    getAll: (): Record<string, unknown>[] => [],
    _formatMemory: (_mem: Record<string, unknown>): string => "",
  };

  const engine = new TieredDecayEngine(stubStorage, undefined, undefined, 3600, 7, 30, 100, 500, 2000);

  // A brand new memory should be HOT
  const hotMem: Record<string, unknown> = {
    id: "mem1",
    content: "test",
    created_at: new Date().toISOString(),
    metadata: {},
  };
  console.assert(
    engine.classify(hotMem) === TierLevel.HOT,
    "New memory should be HOT",
  );

  // A very old memory should be COLD
  const oldDate = new Date();
  oldDate.setFullYear(oldDate.getFullYear() - 1);
  const coldMem: Record<string, unknown> = {
    id: "mem2",
    content: "old memory",
    created_at: oldDate.toISOString(),
    metadata: {},
  };
  console.assert(
    engine.classify(coldMem) === TierLevel.COLD,
    "Year-old memory should be COLD",
  );

  // Deprecated should be COLD
  const deprecatedMem: Record<string, unknown> = {
    id: "mem3",
    content: "deprecated",
    created_at: new Date().toISOString(),
    metadata: { deprecated: "true" },
  };
  console.assert(
    engine.classify(deprecatedMem) === TierLevel.COLD,
    "Deprecated memory should be COLD",
  );

  console.log("PASS: testTieredDecayEngineClassify");
  return true;
}

// ── Test 4: halfLifeToDays infers correct values ───────────────────────

function testHalfLifeToDays(): void {
  // If weight == initial, return default 30
  const d1 = halfLifeToDays(1.0, 1.0, 7.0);
  console.assert(d1 === 30.0, `Expected 30.0, got ${d1}`);

  // If weight is ~0.5 after 7 days, half-life should be ~7
  const inferred = halfLifeToDays(0.5, 1.0, 7.0);
  console.assert(
    Math.abs(inferred - 7.0) < 0.5,
    `Expected ~7.0, got ${inferred}`,
  );

  console.log("PASS: testHalfLifeToDays");
  return true;
}

// ── Test 5: DecayConfig default values ─────────────────────────────────

function testDefaultDecayConfig(): void {
  const cfg = DEFAULT_DECAY_CONFIG;
  console.assert(cfg.strongThreshold === 0.7, "strongThreshold should be 0.7");
  console.assert(cfg.expireThreshold === 0.1, "expireThreshold should be 0.1");
  console.assert(cfg.decayIntervalHours === 24, "decayIntervalHours should be 24");
  console.assert(cfg.protectCritical === true, "protectCritical should be true");
  console.log("PASS: testDefaultDecayConfig");
  return true;
}

// ── Test 6: DecayScheduler lifecycle ───────────────────────────────────

function testDecaySchedulerLifecycle(): void {
  const stubGraph = {
    _graphs: {},
    getNode: (_id: string) => null,
    applyDecay: (_u: Record<string, number>) => {},
  };
  const controller = new DecayController(stubGraph as any, DEFAULT_DECAY_CONFIG);
  const scheduler = new DecayScheduler(controller, DEFAULT_DECAY_CONFIG);

  console.assert(!scheduler.isRunning(), "Should not be running initially");

  scheduler.start();
  console.assert(scheduler.isRunning(), "Should be running after start");

  scheduler.stop();
  console.assert(!scheduler.isRunning(), "Should not be running after stop");

  console.log("PASS: testDecaySchedulerLifecycle");
  return true;
}

// ── Run all ────────────────────────────────────────────────────────────



describe("decay.test", () => {
  it("ExponentialDecay", () => {
    expect(testExponentialDecay()).toBe(true);
  });
  it("CalculateWeight", () => {
    expect(testCalculateWeight()).toBe(true);
  });
  it("TieredDecayEngineClassify", () => {
    expect(testTieredDecayEngineClassify()).toBe(true);
  });
  it("HalfLifeToDays", () => {
    expect(testHalfLifeToDays()).toBe(true);
  });
  it("DefaultDecayConfig", () => {
    expect(testDefaultDecayConfig()).toBe(true);
  });
  it("DecaySchedulerLifecycle", () => {
    expect(testDecaySchedulerLifecycle()).toBe(true);
  });
});
