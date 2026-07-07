import { MemoryManager } from "../src/memory_manager.js";
import { SeededRandom } from "./random.js";
import { DataGenerator, BenchmarkData } from "./data-generator.js";
/** Benchmark configuration */
export interface BenchmarkConfig {
    /** Benchmark name (e.g., "factual-recall") */
    name: string;
    /** Number of facts to store (default: 100) */
    factCount?: number;
    /** Number of queries to run (default: 20) */
    queryCount?: number;
    /** Number of distraction facts (default: 50) */
    distractionCount?: number;
    /** Random seed for reproducibility (default: 42) */
    seed?: number;
    /** Memory types to test (default: ["fact", "episodic", "preference"]) */
    memoryTypes?: string[];
    /** Timeout per benchmark in ms (default: 60000) */
    timeoutMs?: number;
    /** Workspace directory for MemoryManager */
    workspace?: string;
    /** Clean up workspace after benchmark (default: true) */
    cleanup?: boolean;
}
/** Single benchmark detail result */
export interface BenchmarkDetail {
    /** Query string */
    query: string;
    /** Expected answer */
    expected: string;
    /** Actual retrieved content (first result) */
    actual: string;
    /** Score for this query (0.0 - 1.0) */
    score: number;
    /** Memory type of the query */
    memoryType?: string;
    /** All retrieved results (for Recall@K) */
    retrievedResults?: string[];
    /** Additional metadata */
    metadata?: Record<string, unknown>;
}
/** Complete benchmark result */
export interface BenchmarkResult {
    /** Benchmark name */
    name: string;
    /** Configuration used */
    config: Required<BenchmarkConfig>;
    /** Computed metrics */
    metrics: Record<string, number>;
    /** Per-query details */
    details: BenchmarkDetail[];
    /** ISO timestamp */
    timestamp: string;
    /** claw-mem version */
    version: string;
    /** Total benchmark duration in ms */
    durationMs: number;
    /** Pass/fail status */
    passed: boolean;
}
/** Default configuration values */
export declare const DEFAULT_CONFIG: Required<Omit<BenchmarkConfig, 'name'>>;
/**
 * Abstract base class for all benchmarks.
 * Provides lifecycle: init → generateData → loadFacts → runQueries → score → cleanup
 */
export declare abstract class BenchmarkCore {
    protected manager: MemoryManager | null;
    protected config: Required<BenchmarkConfig>;
    protected rng: SeededRandom;
    protected generator: DataGenerator;
    protected workspaceDir: string;
    constructor(config: BenchmarkConfig);
    /**
     * Main entry point: run the complete benchmark.
     * Lifecycle: init → generateData → loadFacts → runQueries → score → cleanup
     */
    run(): Promise<BenchmarkResult>;
    /**
     * Initialize MemoryManager with isolated workspace.
     */
    protected init(): Promise<void>;
    /**
     * Generate synthetic test data (implemented by each benchmark).
     */
    protected abstract generateData(): BenchmarkData;
    /**
     * Store generated facts into memory.
     */
    protected abstract loadFacts(data: BenchmarkData): Promise<void>;
    /**
     * Run queries and collect results.
     */
    protected abstract runQueries(data: BenchmarkData): Promise<BenchmarkDetail[]>;
    /**
     * Score results and compute metrics.
     */
    protected abstract score(details: BenchmarkDetail[]): Record<string, number>;
    /**
     * Check if benchmark passed based on thresholds.
     */
    protected abstract checkPassFail(metrics: Record<string, number>): boolean;
    /**
     * Clean up workspace directory.
     */
    protected cleanup(): void;
    /**
     * Exact match scoring: 1.0 if strings are identical, 0.0 otherwise.
     */
    protected exactMatch(expected: string, actual: string): number;
    /**
     * Semantic match scoring using token overlap (Jaccard similarity).
     * Formula: |tokens(expected) ∩ tokens(actual)| / |tokens(expected) ∪ tokens(actual)|
     */
    protected semanticMatch(expected: string, actual: string): number;
    /**
     * Contains match: 1.0 if actual contains expected (case-insensitive), 0.0 otherwise.
     */
    protected containsMatch(expected: string, actual: string): number;
    /**
     * Temporal ordering scoring: percentage of correctly ordered pairs.
     * Formula: correct_pairs / total_pairs
     */
    protected temporalOrder(events: {
        timestamp: string;
        content: string;
    }[], expectedOrder: string[]): number;
    /**
     * Completeness score: percentage of expected items found in retrieved.
     * Formula: |expected ∩ retrieved| / |expected|
     */
    protected completenessScore(retrieved: string[], expected: string[]): number;
    /**
     * Recall@K: percentage of queries where expected was in top K results.
     * Formula: queries_with_match / total_queries
     */
    protected recallAtK(details: BenchmarkDetail[], k: number): number;
    /**
     * Tokenize string into lowercase words.
     */
    protected tokenize(text: string): string[];
    /**
     * Get claw-mem version from package.json.
     */
    protected getVersion(): string;
    /**
     * Calculate statistics (avg, p50, p95, p99) from array of numbers.
     */
    protected stats(values: number[]): {
        avg: number;
        p50: number;
        p95: number;
        p99: number;
        min: number;
        max: number;
    };
    /**
     * Calculate average score from details.
     */
    protected avgScore(details: BenchmarkDetail[]): number;
}
export { BenchmarkData, FactRecord, QueryRecord } from "./data-generator.js";
