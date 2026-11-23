import { defineConfig } from "vitest/config";

/**
 * v7.11 — performance benchmarks, split out of the default `npm test` path.
 *
 * The ConvoMem benchmark completes its work (1000/1000 = 100%) but exceeds the
 * old 60s per-test wall-clock cap on the dev machine (observed 60-260s). The
 * default suite must stay deterministic; benchmarks keep their assertions and
 * gain real headroom here. Run with `npm run bench`.
 */
export default defineConfig({
  test: {
    globals: true,
    include: ["tests/performance/**/*.test.ts"],
    pool: "forks",
    poolOptions: { forks: { singleFork: true } },
    fileParallelism: false,
    // >=2x the observed worst wall clock; assertions are unchanged.
    testTimeout: 300000,
    teardownTimeout: 30000,
  },
});
