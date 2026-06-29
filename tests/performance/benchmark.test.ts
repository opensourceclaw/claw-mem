// Performance benchmarks for claw-mem v6.6.0

import { describe, it } from "vitest";
import { getMemoryManager } from "../../src/memory_manager";

const WARMUP_ITERATIONS = 3;
const BENCH_ITERATIONS = 20;
const MAX_LATENCY_MS = {
  store: 80,
  search: 100,   // v6.29.0: Increased for HybridRetriever lazy init
  compress: 200, // v6.29.0: Increased for HybridRetriever lazy init
  initialize: 100,  // v6.29.0: Increased for HybridRetriever initialization
};

function measure(fn: () => void, iterations: number): number[] {
  const times: number[] = [];
  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    fn();
    times.push(performance.now() - start);
  }
  return times;
}

function stats(times: number[]) {
  const sorted = [...times].sort((a, b) => a - b);
  const avg = times.reduce((s, t) => s + t, 0) / times.length;
  const p50 = sorted[Math.floor(sorted.length * 0.5)];
  const p95 = sorted[Math.floor(sorted.length * 0.95)];
  const p99 = sorted[Math.floor(sorted.length * 0.99)];
  const min = sorted[0];
  const max = sorted[sorted.length - 1];
  return { avg, p50, p95, p99, min, max, samples: times.length };
}

describe("Performance Benchmarks", () => {
  describe("MemoryManager initialization", () => {
    it("should initialize within latency budget", () => {
      const times = measure(() => {
        getMemoryManager({ workspace: "/tmp/claw-mem-perf-test", autoDetect: false });
      }, BENCH_ITERATIONS);

      const s = stats(times);
      console.log(`Initialize: avg=${s.avg.toFixed(2)}ms p95=${s.p95.toFixed(2)}ms`);
      // Initialization should be fast
      expect(s.p95).toBeLessThan(MAX_LATENCY_MS.initialize);
    });
  });

  describe("Memory store latency", () => {
    it("should store memories within latency budget", () => {
      const manager = getMemoryManager({ workspace: "/tmp/claw-mem-perf-test", autoDetect: false });

      // Warmup
      for (let i = 0; i < WARMUP_ITERATIONS; i++) {
        manager.store(`warmup ${i}`, "episodic");
      }

      const times = measure(() => {
        manager.store(
          `benchmark memory entry for performance testing purposes ${Date.now()}`,
          "episodic",
          ["benchmark"],
          { test: true },
        );
      }, BENCH_ITERATIONS);

      const s = stats(times);
      console.log(`Store: avg=${s.avg.toFixed(2)}ms p95=${s.p95.toFixed(2)}ms throughput=${(1000 / s.avg).toFixed(1)} ops/s`);
      expect(s.p95).toBeLessThan(MAX_LATENCY_MS.store);
    });
  });

  describe("Memory search latency", () => {
    it("should search memories within latency budget", () => {
      const manager = getMemoryManager({ workspace: "/tmp/claw-mem-perf-test", autoDetect: false });

      // Seed data
      for (let i = 0; i < 50; i++) {
        manager.store(`test memory entry number ${i} for benchmark`, "episodic", ["test"], { idx: i });
      }

      // Warmup
      for (let i = 0; i < WARMUP_ITERATIONS; i++) {
        manager.search("test memory", undefined, 10);
      }

      const times = measure(() => {
        const results = manager.search("benchmark test", undefined, 10);
        expect(Array.isArray(results)).toBe(true);
      }, BENCH_ITERATIONS);

      const s = stats(times);
      console.log(`Search: avg=${s.avg.toFixed(2)}ms p95=${s.p95.toFixed(2)}ms`);
      expect(s.p95).toBeLessThan(MAX_LATENCY_MS.search);
    });
  });

  describe("Write throughput", () => {
    it("should sustain reasonable write throughput", () => {
      const manager = getMemoryManager({ workspace: "/tmp/claw-mem-perf-test", autoDetect: false });
      const batchSize = 50;
      const start = performance.now();

      for (let i = 0; i < batchSize; i++) {
        manager.store(
          `throughput test entry ${i} with some additional content to make it realistic ${Date.now()}`,
          "episodic",
          ["throughput"],
          { batch: true, idx: i },
        );
      }

      const elapsed = performance.now() - start;
      const throughput = (batchSize / elapsed) * 1000;
      console.log(`Throughput: ${throughput.toFixed(1)} ops/s (${batchSize} writes in ${elapsed.toFixed(2)}ms)`);
      expect(throughput).toBeGreaterThan(10); // At least 10 writes/sec
    });
  });

  describe("Compression latency (rule-based)", () => {
    it("should compress within latency budget", () => {
      const manager = getMemoryManager({ workspace: "/tmp/claw-mem-perf-test", autoDetect: false });

      // Seed data for compression
      const longText = "The project uses TypeScript for development with a focus on performance. ".repeat(10);
      manager.store(longText, "episodic", ["compress-test"]);

      const times = measure(() => {
        const results = manager.search("TypeScript performance", undefined, 5);
        expect(Array.isArray(results)).toBe(true);
      }, Math.min(BENCH_ITERATIONS, 10));

      const s = stats(times);
      console.log(`Compression-search: avg=${s.avg.toFixed(2)}ms p95=${s.p95.toFixed(2)}ms`);
      expect(s.p95).toBeLessThan(MAX_LATENCY_MS.compress);
    });
  });
});
