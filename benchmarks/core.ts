// BenchmarkCore - Shared harness for all benchmarks (v6.32.0)

import * as fs from "fs";
import * as path from "path";
import { MemoryManager } from "../src/memory_manager.js";
import { SeededRandom } from "./random.js";
import { DataGenerator, BenchmarkData, FactRecord, QueryRecord } from "./data-generator.js";

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
export const DEFAULT_CONFIG: Required<Omit<BenchmarkConfig, 'name'>> = {
  factCount: 100,
  queryCount: 20,
  distractionCount: 50,
  seed: 42,
  memoryTypes: ["fact", "episodic", "preference"],
  timeoutMs: 60000,
  workspace: "",
  cleanup: true,
};

/**
 * Abstract base class for all benchmarks.
 * Provides lifecycle: init → generateData → loadFacts → runQueries → score → cleanup
 */
export abstract class BenchmarkCore {
  protected manager: MemoryManager | null = null;
  protected config: Required<BenchmarkConfig>;
  protected rng: SeededRandom;
  protected generator: DataGenerator;
  protected workspaceDir: string;

  constructor(config: BenchmarkConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config } as Required<BenchmarkConfig>;
    this.rng = new SeededRandom(this.config.seed);
    this.generator = new DataGenerator(this.config.seed);
    this.workspaceDir = this.config.workspace || `/tmp/claw-mem-bench-${this.config.name}-${Date.now()}`;
  }

  /**
   * Main entry point: run the complete benchmark.
   * Lifecycle: init → generateData → loadFacts → runQueries → score → cleanup
   */
  async run(): Promise<BenchmarkResult> {
    const startTime = performance.now();
    const timestamp = new Date().toISOString();

    try {
      // 1. Initialize MemoryManager
      await this.init();

      // 2. Generate synthetic test data
      const data = this.generateData();

      // 3. Load facts into memory
      await this.loadFacts(data);

      // 4. Run queries
      const details = await this.runQueries(data);

      // 5. Score results
      const metrics = this.score(details);

      // 6. Determine pass/fail
      const passed = this.checkPassFail(metrics);

      const durationMs = Math.round(performance.now() - startTime);

      return {
        name: this.config.name,
        config: this.config,
        metrics,
        details,
        timestamp,
        version: this.getVersion(),
        durationMs,
        passed,
      };
    } finally {
      // 7. Cleanup
      if (this.config.cleanup) {
        this.cleanup();
      }
    }
  }

  /**
   * Initialize MemoryManager with isolated workspace.
   */
  protected async init(): Promise<void> {
    // Create workspace directory
    fs.mkdirSync(this.workspaceDir, { recursive: true });
    fs.writeFileSync(
      path.join(this.workspaceDir, "MEMORY.md"),
      "# MEMORY.md\n\n",
      "utf-8"
    );

    // Create MemoryManager
    this.manager = new MemoryManager({
      workspace: this.workspaceDir,
      autoDetect: false,
      enableGating: false,
      enableDecay: false,
    });
  }

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
  protected cleanup(): void {
    if (!this.manager) return;

    try {
      // Remove workspace directory recursively
      fs.rmSync(this.workspaceDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  }

  // Scoring Helpers

  /**
   * Exact match scoring: 1.0 if strings are identical, 0.0 otherwise.
   */
  protected exactMatch(expected: string, actual: string): number {
    return expected.toLowerCase().trim() === actual.toLowerCase().trim() ? 1.0 : 0.0;
  }

  /**
   * Semantic match scoring using token overlap (Jaccard similarity).
   * Formula: |tokens(expected) ∩ tokens(actual)| / |tokens(expected) ∪ tokens(actual)|
   */
  protected semanticMatch(expected: string, actual: string): number {
    const expectedTokens = new Set(this.tokenize(expected));
    const actualTokens = new Set(this.tokenize(actual));

    if (expectedTokens.size === 0) return 0.0;

    const intersection = [...expectedTokens].filter(t => actualTokens.has(t));
    const union = new Set([...expectedTokens, ...actualTokens]);

    return union.size > 0 ? intersection.length / union.size : 0.0;
  }

  /**
   * Contains match: 1.0 if actual contains expected (case-insensitive), 0.0 otherwise.
   */
  protected containsMatch(expected: string, actual: string): number {
    return actual.toLowerCase().includes(expected.toLowerCase()) ? 1.0 : 0.0;
  }

  /**
   * Temporal ordering scoring: percentage of correctly ordered pairs.
   * Formula: correct_pairs / total_pairs
   */
  protected temporalOrder(events: { timestamp: string; content: string }[], expectedOrder: string[]): number {
    if (events.length < 2 || expectedOrder.length < 2) return 1.0;

    let correctPairs = 0;
    let totalPairs = 0;

    // Check all pairs in expectedOrder
    for (let i = 0; i < expectedOrder.length - 1; i++) {
      for (let j = i + 1; j < expectedOrder.length; j++) {
        const idxI = events.findIndex(e => e.content.includes(expectedOrder[i]));
        const idxJ = events.findIndex(e => e.content.includes(expectedOrder[j]));

        if (idxI !== -1 && idxJ !== -1) {
          totalPairs++;
          if (idxI < idxJ) correctPairs++;
        }
      }
    }

    return totalPairs > 0 ? correctPairs / totalPairs : 0.0;
  }

  /**
   * Completeness score: percentage of expected items found in retrieved.
   * Formula: |expected ∩ retrieved| / |expected|
   */
  protected completenessScore(retrieved: string[], expected: string[]): number {
    if (expected.length === 0) return 1.0;

    const retrievedSet = new Set(retrieved.map(r => r.toLowerCase()));
    const found = expected.filter(e => retrievedSet.has(e.toLowerCase()));

    return found.length / expected.length;
  }

  /**
   * Recall@K: percentage of queries where expected was in top K results.
   * Formula: queries_with_match / total_queries
   */
  protected recallAtK(details: BenchmarkDetail[], k: number): number {
    if (details.length === 0) return 0.0;

    const hits = details.filter(d => {
      const topK = d.retrievedResults?.slice(0, k) || [d.actual];
      return topK.some(r => this.semanticMatch(d.expected, r) >= 0.5);
    });

    return hits.length / details.length;
  }

  // Utility Methods

  /**
   * Tokenize string into lowercase words.
   */
  protected tokenize(text: string): string[] {
    if (typeof text !== "string") return [];
    return text.toLowerCase()
      .replace(/[^\w\s]/g, " ")
      .split(/\s+/)
      .filter(t => t.length > 0);
  }

  /**
   * Get claw-mem version from package.json.
   */
  protected getVersion(): string {
    try {
      const pkgPath = path.resolve(__dirname, "..", "package.json");
      const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf-8"));
      return pkg.version || "unknown";
    } catch {
      return "unknown";
    }
  }

  /**
   * Calculate statistics (avg, p50, p95, p99) from array of numbers.
   */
  protected stats(values: number[]): { avg: number; p50: number; p95: number; p99: number; min: number; max: number } {
    if (values.length === 0) {
      return { avg: 0, p50: 0, p95: 0, p99: 0, min: 0, max: 0 };
    }

    const sorted = [...values].sort((a, b) => a - b);
    const sum = values.reduce((s, v) => s + v, 0);

    return {
      avg: sum / values.length,
      p50: sorted[Math.floor(sorted.length * 0.5)],
      p95: sorted[Math.floor(sorted.length * 0.95)],
      p99: sorted[Math.floor(sorted.length * 0.99)],
      min: sorted[0],
      max: sorted[sorted.length - 1],
    };
  }

  /**
   * Calculate average score from details.
   */
  protected avgScore(details: BenchmarkDetail[]): number {
    if (details.length === 0) return 0;
    return details.reduce((sum, d) => sum + d.score, 0) / details.length;
  }
}

// Re-export types
export { BenchmarkData, FactRecord, QueryRecord } from "./data-generator.js";
