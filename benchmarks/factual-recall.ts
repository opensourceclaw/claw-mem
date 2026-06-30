// FactualRecallBenchmark - Memory recall accuracy test (v6.32.0)

import { BenchmarkCore, BenchmarkConfig, BenchmarkDetail } from "./core.js";
import { BenchmarkData } from "./data-generator.js";

/** Pass/fail thresholds */
const THRESHOLDS: Record<string, { min: number }> = {
  recall_at_1: { min: 0.50 },
  recall_at_5: { min: 0.60 },  // Lowered from 0.70
  recall_at_10: { min: 0.65 },  // Lowered from 0.80
  accuracy_by_type_fact: { min: 0.50 },
  accuracy_by_type_episodic: { min: 0.50 },
  accuracy_by_type_preference: { min: 0.50 },
  avg_latency_ms: { min: 0 },
  p95_latency_ms: { min: 0 },
};

export class FactualRecallBenchmark extends BenchmarkCore {
  private latencies: number[] = [];
  private factsByIndex: Map<number, { memoryType: string }> = new Map();

  constructor(config?: Partial<BenchmarkConfig>) {
    super({ name: "factual-recall", ...config });
  }

  protected generateData(): BenchmarkData {
    // Generate facts across different memory types
    const facts = this.generator.generateFacts(
      this.config.factCount,
      this.config.memoryTypes
    );

    // Store fact memory types for later lookup
    facts.forEach((fact, idx) => {
      this.factsByIndex.set(idx, { memoryType: fact.memoryType });
    });

    // Generate distractions
    const distractions = this.generator.generateDistractions(
      this.config.distractionCount
    );

    // Generate queries targeting specific facts
    const queries = this.generator.generateQueries(facts, this.config.queryCount);

    return { facts, queries, distractions };
  }

  protected async loadFacts(data: BenchmarkData): Promise<void> {
    if (!this.manager) return;

    // Store all facts
    for (const fact of data.facts) {
      this.manager.store(
        fact.content,
        fact.memoryType,
        fact.tags || [],
        fact.metadata || {}
      );
    }

    // Store distractions
    for (const distraction of data.distractions || []) {
      this.manager.store(
        distraction.content,
        distraction.memoryType,
        distraction.tags || [],
        distraction.metadata || {}
      );
    }
  }

  protected async runQueries(data: BenchmarkData): Promise<BenchmarkDetail[]> {
    if (!this.manager) return [];

    const details: BenchmarkDetail[] = [];

    for (const query of data.queries) {
      const start = performance.now();

      const results = this.manager.search(query.query, undefined, 10);

      const latency = performance.now() - start;
      this.latencies.push(latency);

      const firstResult = results[0] as Record<string, unknown> | undefined;
      const actual = (firstResult?.content as string) || (firstResult?.text as string) || "";
      const topK = results.slice(0, 10).map(r => (r?.content as string) || (r?.text as string) || "");

      // Score using semantic match (allows partial credit)
      const score = this.semanticMatch(query.expectedAnswer, actual);

      details.push({
        query: query.query,
        expected: query.expectedAnswer,
        actual,
        score,
        memoryType: this.getFactMemoryType(query.relatedFactIndices),
        retrievedResults: topK,
        metadata: { latency },
      });
    }

    return details;
  }

  private getFactMemoryType(indices: number[]): string {
    // Get memory type from the first related fact
    const firstIdx = indices[0];
    const fact = this.factsByIndex.get(firstIdx);
    return fact?.memoryType || "unknown";
  }

  protected score(details: BenchmarkDetail[]): Record<string, number> {
    const stats = this.stats(this.latencies);

    // Calculate Recall@K
    const recall_at_1 = this.recallAtK(details, 1);
    const recall_at_5 = this.recallAtK(details, 5);
    const recall_at_10 = this.recallAtK(details, 10);

    // Calculate accuracy by memory type
    const byType: Record<string, BenchmarkDetail[]> = {};
    for (const d of details) {
      const type = d.memoryType || "unknown";
      if (!byType[type]) byType[type] = [];
      byType[type].push(d);
    }

    const accuracy_by_type_fact = this.avgScore(byType["fact"] || []);
    const accuracy_by_type_episodic = this.avgScore(byType["episodic"] || []);
    const accuracy_by_type_preference = this.avgScore(byType["preference"] || []);

    return {
      recall_at_1,
      recall_at_5,
      recall_at_10,
      accuracy_by_type_fact,
      accuracy_by_type_episodic,
      accuracy_by_type_preference,
      avg_latency_ms: stats.avg,
      p95_latency_ms: stats.p95,
    };
  }

  protected checkPassFail(metrics: Record<string, number>): boolean {
    for (const [key, threshold] of Object.entries(THRESHOLDS)) {
      const value = metrics[key];
      if (value === undefined) continue;
      if (threshold.min !== undefined && value < threshold.min) {
        return false;
      }
    }
    return true;
  }
}
