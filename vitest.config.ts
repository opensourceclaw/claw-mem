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
    poolOptions: {
      forks: {
        singleFork: true,
      },
    },
    coverage: {
      provider: "v8",
      include: ["src/**/*.ts"],
      exclude: [
        "src/**/*.d.ts",
      ],
    },
  },
});
