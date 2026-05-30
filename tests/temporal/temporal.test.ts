// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

import { TimeWeightCalculator, TimeWeightConfig } from "../../src/temporal/time_aware";

// ── Time Weight Calculator Tests ───────────────────────────────────

function testExponentialDecay(): boolean {
  const calc = new TimeWeightCalculator();

  // Recent memory should get weight close to base (1.0)
  const recentWeight = calc.calculate(new Date().toISOString());
  if (recentWeight < 0.9 || recentWeight > 1.0) {
    console.error(`FAIL: Recent memory weight should be ~1.0, got ${recentWeight}`);
    return false;
  }

  // Very old memory should decay toward min_weight (0.1)
  const oldWeight = calc.calculate("2020-01-01T00:00:00Z");
  if (oldWeight > 0.5) {
    console.error(`FAIL: Old memory weight should be low, got ${oldWeight}`);
    return false;
  }

  console.log("  PASS: Exponential decay calculation");
  return true;
}

function testLinearDecay(): boolean {
  const config = new TimeWeightConfig({
    decayType: "linear",
    maxAgeDays: 100,
    baseWeight: 1.0,
    minWeight: 0.1,
  });
  const calc = new TimeWeightCalculator(config);

  // Brand new memory (age 0) should get base_weight
  const freshWeight = calc.calculate(new Date().toISOString());
  if (Math.abs(freshWeight - 1.0) > 0.01) {
    console.error(`FAIL: Fresh memory weight should be ~1.0, got ${freshWeight}`);
    return false;
  }

  // Memory at max age should get min_weight
  const maxAgeDate = new Date();
  maxAgeDate.setDate(maxAgeDate.getDate() - 100);
  const oldWeight = calc.calculate(maxAgeDate.toISOString());
  if (Math.abs(oldWeight - 0.1) > 0.02) {
    console.error(`FAIL: Max-age memory weight should be ~0.1, got ${oldWeight}`);
    return false;
  }

  console.log("  PASS: Linear decay calculation");
  return true;
}

// ── Run ────────────────────────────────────────────────────────────

function run(): void {
  console.log("\nTemporal Module Tests\n");

  let passed = 0;
  let failed = 0;

  const tests: [string, () => boolean][] = [
    ["Exponential decay calculation", testExponentialDecay],
    ["Linear decay calculation", testLinearDecay],
  ];

  for (const [name, fn] of tests) {
    try {
      if (fn()) {
        passed++;
      } else {
        console.error(`  FAIL: ${name}`);
        failed++;
      }
    } catch (err) {
      console.error(`  ERROR: ${name} — ${err}`);
      failed++;
    }
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed\n`);
  if (failed > 0) process.exit(1);
}

run();
