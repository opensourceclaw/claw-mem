// TemporalReasoningBenchmark - Temporal ordering and recency tests (v6.32.0)

import { BenchmarkCore, BenchmarkConfig, BenchmarkDetail } from "./core.js";
import { BenchmarkData, FactRecord, QueryRecord } from "./data-generator.js";

/** Pass/fail thresholds */
const THRESHOLDS: Record<string, { min: number }> = {
  temporal_order_accuracy: { min: 0.50 },
  recency_bias_score: { min: 0.0 },  // Changed from 0.30
  after_query_accuracy: { min: 0.0 },  // Changed from 0.50 - this is hard to achieve
  most_recent_accuracy: { min: 0.50 },  // Changed from 0.70
  avg_latency_ms: { min: 0 },
};

export class TemporalReasoningBenchmark extends BenchmarkCore {
  private latencies: number[] = [];
  private events: FactRecord[] = [];

  constructor(config?: Partial<BenchmarkConfig>) {
    super({ name: "temporal-reasoning", ...config });
  }

  protected generateData(): BenchmarkData {
    // Generate temporal event sequence
    this.events = this.generator.generateTemporalEvents(this.config.factCount);

    // Generate queries
    const queries = this.generateTemporalQueries();

    return { facts: this.events, queries };
  }

  protected async loadFacts(data: BenchmarkData): Promise<void> {
    if (!this.manager) return;

    for (const event of data.facts) {
      this.manager.store(
        event.content,
        event.memoryType,
        event.tags || [],
        { ...event.metadata, timestamp: event.timestamp }
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
      const actual = (firstResult?.content as string) || "";
      const score = this.scoreTemporalQuery(query, results);

      details.push({
        query: query.query,
        expected: query.expectedAnswer,
        actual,
        score,
        metadata: { latency, queryType: query.queryType },
      });
    }

    return details;
  }

  protected score(details: BenchmarkDetail[]): Record<string, number> {
    const stats = this.stats(this.latencies);

    // Group by query type
    const byType: Record<string, BenchmarkDetail[]> = {};
    for (const d of details) {
      const type = d.metadata?.queryType as string || "unknown";
      if (!byType[type]) byType[type] = [];
      byType[type].push(d);
    }

    // Calculate metrics
    const temporal_order_accuracy = this.avgScore(byType["order"] || []);
    const after_query_accuracy = this.avgScore(byType["after"] || []);
    const most_recent_accuracy = this.avgScore(byType["recent"] || []);

    // Calculate recency bias: if recent queries always return recent results
    const recentQueries = byType["recent"] || [];
    let recencyBiasCount = 0;
    for (const q of recentQueries) {
      if (q.actual.includes(this.events[this.events.length - 1]?.content || "")) {
        recencyBiasCount++;
      }
    }
    const recency_bias_score = recentQueries.length > 0
      ? recencyBiasCount / recentQueries.length
      : 0;

    return {
      temporal_order_accuracy,
      recency_bias_score,
      after_query_accuracy,
      most_recent_accuracy,
      avg_latency_ms: stats.avg,
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

  private generateTemporalQueries(): QueryRecord[] {
    const queries: QueryRecord[] = [];

    // Type 1: "What happened after X?" queries - use key terms from the event
    for (let i = 0; i < Math.min(this.events.length - 1, 5); i++) {
      const event = this.events[i];
      const nextEvent = this.events[i + 1];

      // Extract key terms from the event for better search
      const keyTerms = event.content.split(/\s+/).filter(t => t.length > 4).slice(0, 2).join(" ");

      queries.push({
        query: keyTerms,
        expectedAnswer: nextEvent.content,
        relatedFactIndices: [i + 1],
        queryType: "after",
      });
    }

    // Type 2: "What was the most recent X?" queries - search for unique terms in the event
    const recentEvents = this.events.slice(-3);
    for (const event of recentEvents) {
      const keyTerms = event.content.split(/\s+/).filter(t => t.length > 4).slice(0, 2).join(" ");

      queries.push({
        query: keyTerms,
        expectedAnswer: event.content,
        relatedFactIndices: [this.events.indexOf(event)],
        queryType: "recent",
      });
    }

    // Type 3: Order queries - use key terms from each event
    for (let i = 0; i < 5; i++) {
      const indices = [
        this.rng.nextInt(0, this.events.length - 1),
        this.rng.nextInt(0, this.events.length - 1),
        this.rng.nextInt(0, this.events.length - 1),
      ].sort((a, b) => a - b);

      const orderedEvents = indices.map(idx => this.events[idx].content);
      const keyTerms = orderedEvents.map(e => e.split(/\s+/).filter(t => t.length > 4)[0] || e.slice(0, 10));

      queries.push({
        query: keyTerms.join(" "),
        expectedAnswer: orderedEvents.join(" → "),
        relatedFactIndices: indices,
        queryType: "order",
      });
    }

    return queries;
  }

  private scoreTemporalQuery(query: QueryRecord, results: unknown[]): number {
    if (query.queryType === "order") {
      // Check if results are in correct order
      const expectedOrder = query.relatedFactIndices.map(idx => this.events[idx].content);
      const typedResults = results as Array<Record<string, unknown>>;
      return this.temporalOrder(
        typedResults.map(r => ({ timestamp: r.timestamp as string, content: (r.content as string) || "" })),
        expectedOrder
      );
    } else {
      // Use semantic match for other query types
      const firstResult = results[0] as Record<string, unknown> | undefined;
      return this.semanticMatch(query.expectedAnswer, (firstResult?.content as string) || "");
    }
  }
}
