import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    include: ["tests/**/*.test.ts"],
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
        "src/compression/index.ts",
        "src/decay/index.ts",
        "src/storage/index.ts",
        "src/retrieval/index.ts",
        "src/**/index.ts",
      ],
      reporter: ["text", "text-summary", "json", "html"],
      reportsDirectory: "./coverage",
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 45,
        statements: 60,
      },
      watermarks: {
        statements: [55, 75],
        functions: [55, 75],
        branches: [40, 65],
        lines: [55, 75],
      },
    },
  },
});
