// Benchmark Suite - Barrel export (v6.32.0)

// Core
export { BenchmarkCore, DEFAULT_CONFIG } from "./core.js";
export type { BenchmarkConfig, BenchmarkDetail, BenchmarkResult } from "./core.js";

// Random
export { SeededRandom } from "./random.js";

// Data Generator
export { DataGenerator } from "./data-generator.js";
export type { FactRecord, QueryRecord, BenchmarkData } from "./data-generator.js";

// Individual Benchmarks
export { FactualRecallBenchmark } from "./factual-recall.js";
export { TemporalReasoningBenchmark } from "./temporal-reasoning.js";
export { LongHorizonBenchmark } from "./long-horizon.js";
export { UpdateRobustnessBenchmark } from "./update-robustness.js";
export { RetrievalFidelityBenchmark } from "./retrieval-fidelity.js";
export { OperationalCostBenchmark } from "./operational-cost.js";

// Reporter
export { ResultReporter } from "./reporter.js";
export type { ReportOptions, ComparisonReport } from "./reporter.js";

// Runner
export { runAll, main, getLastBenchmarkResults } from "./runner.js";
export type { RunOptions } from "./runner.js";
