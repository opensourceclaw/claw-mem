// CLI Runner - Benchmark execution entry point (v6.32.0)

import * as fs from "fs";
import * as path from "path";
import { BenchmarkResult, BenchmarkConfig } from "./core.js";
import { FactualRecallBenchmark } from "./factual-recall.js";
import { TemporalReasoningBenchmark } from "./temporal-reasoning.js";
import { LongHorizonBenchmark } from "./long-horizon.js";
import { UpdateRobustnessBenchmark } from "./update-robustness.js";
import { RetrievalFidelityBenchmark } from "./retrieval-fidelity.js";
import { OperationalCostBenchmark } from "./operational-cost.js";
import { ResultReporter, ReportOptions } from "./reporter.js";

export interface RunOptions extends Partial<BenchmarkConfig> {
  /** Run specific benchmark only */
  name?: string;
  /** Output format */
  format?: "json" | "markdown" | "both";
  /** Baseline file for comparison */
  baseline?: string;
  /** Output directory */
  outputDir?: string;
}

/**
 * Get version from package.json.
 */
function getVersion(): string {
  try {
    // Try two levels up first (compiled: dist/benchmarks/ -> project root)
    let pkgPath = path.resolve(__dirname, "..", "..", "package.json");
    if (!fs.existsSync(pkgPath)) {
      // Fallback to one level up (source: benchmarks/ -> project root)
      pkgPath = path.resolve(__dirname, "..", "package.json");
    }
    return JSON.parse(fs.readFileSync(pkgPath, "utf-8")).version || "unknown";
  } catch {
    return "unknown";
  }
}

// Cache for last benchmark results (used by bridge RPC)
let lastBenchmarkResults: BenchmarkResult[] | null = null;
let lastBenchmarkTimestamp: string | null = null;

/**
 * Get last cached benchmark results.
 */
export function getLastBenchmarkResults(): { results: BenchmarkResult[] | null; timestamp: string | null } {
  return { results: lastBenchmarkResults, timestamp: lastBenchmarkTimestamp };
}

/**
 * Run all benchmarks or a specific one.
 */
export async function runAll(options: RunOptions = {}): Promise<BenchmarkResult[]> {
  const results: BenchmarkResult[] = [];
  const errors: Error[] = [];

  const benchmarkFactories = [
    () => new FactualRecallBenchmark(options),
    () => new TemporalReasoningBenchmark(options),
    () => new LongHorizonBenchmark(options),
    () => new UpdateRobustnessBenchmark(options),
    () => new RetrievalFidelityBenchmark(options),
    () => new OperationalCostBenchmark(options),
  ];

  const benchmarkNames = [
    "factual-recall",
    "temporal-reasoning",
    "long-horizon",
    "update-robustness",
    "retrieval-fidelity",
    "operational-cost",
  ];

  for (let i = 0; i < benchmarkFactories.length; i++) {
    const benchmarkName = benchmarkNames[i];

    // Skip if running specific benchmark
    if (options.name && options.name !== benchmarkName) {
      continue;
    }

    try {
      console.log(`Running ${benchmarkName}...`);
      const benchmark = benchmarkFactories[i]();
      const result = await benchmark.run();
      results.push(result);
      console.log(`  ✓ ${result.name}: ${result.passed ? "PASS" : "FAIL"} (${result.durationMs}ms)`);
      if (!result.passed) {
        console.log(`  Metrics: ${JSON.stringify(result.metrics, null, 2).split('\n').join('\n  ')}`);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      errors.push(error);
      console.error(`  ✗ ${benchmarkName}: ${error.message}`);
    }
  }

  // Cache results
  lastBenchmarkResults = results;
  lastBenchmarkTimestamp = new Date().toISOString();

  // Generate report
  if (results.length > 0) {
    const reportOptions: ReportOptions = {
      outputDir: options.outputDir || "./results",
      format: options.format || "both",
      baseline: options.baseline,
    };

    ResultReporter.generate(results, reportOptions);
  }

  // Report errors
  if (errors.length > 0) {
    console.error(`\n${errors.length} benchmark(s) failed with errors.`);
  }

  return results;
}

/**
 * CLI entry point.
 */
export async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const options: RunOptions = {};

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === "--name" && args[i + 1]) {
      options.name = args[++i];
    } else if (arg === "--seed" && args[i + 1]) {
      options.seed = parseInt(args[++i], 10);
    } else if (arg === "--format" && args[i + 1]) {
      options.format = args[++i] as "json" | "markdown" | "both";
    } else if (arg === "--baseline" && args[i + 1]) {
      options.baseline = args[++i];
    } else if (arg === "--output" && args[i + 1]) {
      options.outputDir = args[++i];
    } else if (arg === "--fact-count" && args[i + 1]) {
      options.factCount = parseInt(args[++i], 10);
    } else if (arg === "--query-count" && args[i + 1]) {
      options.queryCount = parseInt(args[++i], 10);
    } else if (arg === "--help") {
      console.log(`
claw-mem Benchmark Suite v${getVersion()}

Usage: npm run benchmark [options]

Options:
  --name <benchmark>     Run specific benchmark only
  --seed <number>        Random seed for reproducibility (default: 42)
  --format <format>      Output format: json, markdown, both (default: both)
  --baseline <file>      Compare against baseline JSON file
  --output <dir>         Output directory (default: ./results)
  --fact-count <n>       Number of facts to generate (default: 100)
  --query-count <n>      Number of queries to run (default: 20)
  --help                 Show this help message
      `);
      process.exit(0);
    }
  }

  console.log(`claw-mem Benchmark Suite v${getVersion()}`);
  console.log(`Seed: ${options.seed || 42}`);
  console.log("");

  const startTime = Date.now();
  const results = await runAll(options);
  const totalDuration = Date.now() - startTime;

  console.log("");
  console.log(`Total: ${results.length} benchmarks, ${totalDuration}ms`);
  console.log(`Passed: ${results.filter(r => r.passed).length}/${results.length}`);
}

// Run main if executed directly
if (require.main === module) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}
