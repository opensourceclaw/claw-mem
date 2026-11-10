import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    // Only run tests in tests/unit and tests/ (exclude integration-external)
    include: [
      "tests/unit/**/*.test.ts",
      "tests/**/*.test.ts",
    ],
    exclude: [
      "tests/integration-external/**",
      "tests/p0-coverage.test.ts",
      "tests/integration/full_pipeline.test.ts",
    ],
    // Prevent hangs from too many concurrent claw-mem instances
    pool: 'forks',
    // Single fork: files already run sequentially (fileParallelism:false), so
    // one long-lived worker removes ~500 fork spawns AND the end-of-batch
    // worker close race ("Closing rpc while onUserConsoleLog was pending" /
    // EnvironmentTeardownError flake, CI run 42792161580 on d7a099db).
    poolOptions: { forks: { singleFork: true } },
    // Generous teardown budget for slow CI runners.
    teardownTimeout: 30000,
    // Test files share the default ~/.openclaw/workspace; parallel files
    // race on the same daily memory file (same-ms tmp + rename ENOENT).
    fileParallelism: false,
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: [
        "src/**/*.d.ts",
      ],
    },
  },
});
