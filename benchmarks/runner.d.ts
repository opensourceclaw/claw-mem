import { BenchmarkResult, BenchmarkConfig } from "./core.js";
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
 * Get last cached benchmark results.
 */
export declare function getLastBenchmarkResults(): {
    results: BenchmarkResult[] | null;
    timestamp: string | null;
};
/**
 * Run all benchmarks or a specific one.
 */
export declare function runAll(options?: RunOptions): Promise<BenchmarkResult[]>;
/**
 * CLI entry point.
 */
export declare function main(): Promise<void>;
