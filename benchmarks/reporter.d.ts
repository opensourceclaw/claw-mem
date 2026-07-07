import { BenchmarkResult } from "./core.js";
export interface ReportOptions {
    /** Output directory */
    outputDir: string;
    /** Format: json, markdown, both */
    format: "json" | "markdown" | "both";
    /** Baseline file for comparison */
    baseline?: string;
    /** Thresholds for pass/fail */
    thresholds?: Record<string, Record<string, {
        min?: number;
        max?: number;
    }>>;
}
export interface ComparisonReport {
    benchmark: string;
    metric: string;
    current: number;
    baseline: number;
    change: number;
    changePercent: number;
    improved: boolean;
}
export declare class ResultReporter {
    /**
     * Generate reports for all benchmark results.
     */
    static generate(results: BenchmarkResult[], options: ReportOptions): void;
    /**
     * Compare current results against baseline.
     */
    static compare(current: BenchmarkResult[], baseline: BenchmarkResult[]): ComparisonReport[];
    /**
     * Get version from package.json.
     */
    private static getVersion;
    /**
     * Format as JSON.
     */
    private static toJSON;
    /**
     * Format as Markdown.
     */
    private static toMarkdown;
    /**
     * Check if metric passes threshold.
     */
    private static checkThreshold;
}
