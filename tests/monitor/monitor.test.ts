// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

import { PerformanceMonitor } from "../../src/monitor/performance";
import { describe, it, expect } from "vitest";

// ── Performance Monitor Tests ──────────────────────────────────────

function testMetricTracking(): boolean {
  const monitor = new PerformanceMonitor();

  monitor.recordSearch(5.0);
  monitor.recordSearch(10.0);
  monitor.recordSearch(15.0);
  monitor.recordCacheHit();
  monitor.recordCacheHit();
  monitor.recordCacheMiss();

  const stats = monitor.getStats();

  if (stats.search_count !== 3) {
    console.error(`FAIL: Expected search_count 3, got ${stats.search_count}`);
    return false;
  }
  if (stats.avg_latency_ms < 9.0 || stats.avg_latency_ms > 11.0) {
    console.error(`FAIL: Expected avg_latency_ms ~10, got ${stats.avg_latency_ms}`);
    return false;
  }
  if (stats.min_latency_ms !== 5.0) {
    console.error(`FAIL: Expected min_latency_ms 5, got ${stats.min_latency_ms}`);
    return false;
  }
  if (stats.max_latency_ms !== 15.0) {
    console.error(`FAIL: Expected max_latency_ms 15, got ${stats.max_latency_ms}`);
    return false;
  }
  if (stats.cache_hits !== 2) {
    console.error(`FAIL: Expected cache_hits 2, got ${stats.cache_hits}`);
    return false;
  }
  if (stats.cache_misses !== 1) {
    console.error(`FAIL: Expected cache_misses 1, got ${stats.cache_misses}`);
    return false;
  }
  if (Math.abs(stats.cache_hit_rate - 2 / 3) > 0.01) {
    console.error(`FAIL: Expected cache_hit_rate ~0.667, got ${stats.cache_hit_rate}`);
    return false;
  }

  console.log("  PASS: Metric tracking accuracy");
  return true;
}

function testPercentileCalculation(): boolean {
  const monitor = new PerformanceMonitor();

  // Record 100 latencies from 1 to 100
  for (let i = 1; i <= 100; i++) {
    monitor.recordSearch(i);
  }

  const stats = monitor.getStats();

  if (stats.p50_latency_ms < 49 || stats.p50_latency_ms > 51) {
    console.error(`FAIL: Expected p50 ~50, got ${stats.p50_latency_ms}`);
    return false;
  }
  if (stats.p95_latency_ms < 94 || stats.p95_latency_ms > 96) {
    console.error(`FAIL: Expected p95 ~95, got ${stats.p95_latency_ms}`);
    return false;
  }
  if (stats.p99_latency_ms < 98 || stats.p99_latency_ms > 100) {
    console.error(`FAIL: Expected p99 ~99, got ${stats.p99_latency_ms}`);
    return false;
  }

  console.log("  PASS: Percentile calculation accuracy");
  return true;
}

// ── Run ────────────────────────────────────────────────────────────


describe("monitor.test", () => {
  it("Metric tracking accuracy", () => {    expect(testMetricTracking()).toBe(true);  });
  it("Percentile calculation accuracy", () => {    expect(testPercentileCalculation()).toBe(true);  });
});
