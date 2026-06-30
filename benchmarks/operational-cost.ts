// OperationalCostBenchmark - Performance and cost measurement (v6.32.0)

import * as fs from "fs";
import * as path from "path";
import { BenchmarkCore, BenchmarkConfig, BenchmarkDetail } from "./core.js";
import { BenchmarkData } from "./data-generator.js";

/** Pass/fail thresholds */
const THRESHOLDS: Record<string, { min?: number; max?: number }> = {
  store_latency_avg: { max: 50 },
  store_latency_p95: { max: 100 },
  search_latency_avg: { max: 50 },
  search_latency_p95: { max: 100 },
  storage_size_kb_per_1k: { max: 500 },
  estimated_token_cost_per_search: { max: 500 },
};

export class OperationalCostBenchmark extends BenchmarkCore {
  private storeLatencies: number[] = [];
  private searchLatencies: number[] = [];
  private strategyLatencies: Map<string, number[]> = new Map();
  private initialStorageSize: number = 0;

  constructor(config?: Partial<BenchmarkConfig>) {
    super({ name: "operational-cost", ...config });
  }

  protected generateData(): BenchmarkData {
    return {
      facts: this.generator.generateFacts(this.config.factCount, this.config.memoryTypes),
      queries: this.generator.generateQueries([], this.config.queryCount),
    };
  }

  protected async loadFacts(data: BenchmarkData): Promise<void> {
    if (!this.manager) return;

    // Record initial storage size
    this.initialStorageSize = this.getStorageSize();

    // Store facts and measure latency per strategy
    for (const fact of data.facts) {
      const start = performance.now();

      this.manager.store(
        fact.content,
        fact.memoryType,
        fact.tags || [],
        fact.metadata || {}
      );

      const latency = performance.now() - start;
      this.storeLatencies.push(latency);

      // Track per-strategy latency
      const strategy = this.manager.getStoreStrategy?.(fact.memoryType);
      if (strategy) {
        if (!this.strategyLatencies.has(strategy)) {
          this.strategyLatencies.set(strategy, []);
        }
        this.strategyLatencies.get(strategy)!.push(latency);
      }
    }
  }

  protected async runQueries(data: BenchmarkData): Promise<BenchmarkDetail[]> {
    if (!this.manager) return [];

    const details: BenchmarkDetail[] = [];

    for (const query of data.queries) {
      const start = performance.now();
      const results = this.manager.search(query.query, undefined, 10);
      const latency = performance.now() - start;
      this.searchLatencies.push(latency);

      const typedResults = results as Array<Record<string, unknown>>;
      // Estimate token cost (rough approximation: chars / 4)
      const tokenCost = typedResults.reduce((sum, r) =>
        sum + Math.ceil(((r.content as string)?.length || (r.text as string)?.length || 0) / 4), 0
      );

      const firstResult = typedResults[0];
      details.push({
        query: query.query,
        expected: query.expectedAnswer,
        actual: (firstResult?.content as string) || (firstResult?.text as string) || "",
        score: 1.0,  // Not scoring accuracy here
        metadata: { latency, tokenCost },
      });
    }

    return details;
  }

  protected score(details: BenchmarkDetail[]): Record<string, number> {
    const storeStats = this.stats(this.storeLatencies);
    const searchStats = this.stats(this.searchLatencies);

    // Calculate storage size growth
    const finalStorageSize = this.getStorageSize();
    const storageGrowth = finalStorageSize - this.initialStorageSize;
    const storage_size_kb_per_1k = (storageGrowth / 1024) * (1000 / this.config.factCount);

    // Estimate token cost per search
    const avgTokenCost = details.length > 0
      ? details.reduce((sum, d) => sum + ((d.metadata?.tokenCost as number) || 0), 0) / details.length
      : 0;

    // Per-strategy breakdown
    const strategy_breakdown: Record<string, { latency_avg: number; storage_bytes: number }> = {};
    for (const [strategy, latencies] of this.strategyLatencies) {
      const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
      strategy_breakdown[strategy] = {
        latency_avg: avg,
        storage_bytes: Math.round(storageGrowth / Math.max(this.strategyLatencies.size, 1)),
      };
    }

    return {
      store_latency_avg: storeStats.avg,
      store_latency_p95: storeStats.p95,
      search_latency_avg: searchStats.avg,
      search_latency_p95: searchStats.p95,
      storage_size_kb_per_1k,
      estimated_token_cost_per_search: avgTokenCost,
      ...strategy_breakdown,  // Flatten strategy breakdown into metrics
    };
  }

  protected checkPassFail(metrics: Record<string, number>): boolean {
    for (const [key, threshold] of Object.entries(THRESHOLDS)) {
      const value = metrics[key];
      if (value === undefined) continue;
      if (threshold.min !== undefined && value < threshold.min) return false;
      if (threshold.max !== undefined && value > threshold.max) return false;
    }
    return true;
  }

  private getStorageSize(): number {
    if (!this.manager) return 0;

    const memoryDir = path.join(this.workspaceDir, "memory");

    if (!fs.existsSync(memoryDir)) return 0;

    let totalSize = 0;
    const files = fs.readdirSync(memoryDir);
    for (const file of files) {
      const filePath = path.join(memoryDir, file);
      const stat = fs.statSync(filePath);
      totalSize += stat.size;
    }

    return totalSize;
  }
}
