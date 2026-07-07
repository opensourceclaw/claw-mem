// claw-mem v6.35.0 — StructureOptimizer (TypeScript)
//
// Main orchestrator for structure optimization operations.
// Coordinates health assessment and optimization suggestions.
//
// Licensed under the Apache License, Version 2.0

import * as crypto from "crypto";
import {
  HealthReport,
  IndexStat,
  IndexType,
  OptimizeSuggestion,
  OptimizeResult,
  OptimizeRecord,
  OptimizeOptions,
  DEFAULT_OPTIMIZER_OPTIONS,
  DEFAULT_OPTIMIZE_OPTIONS,
  OptimizerStats,
  StructureOptimizerOptions,
} from "./types.js";
import { HealthReporter } from "./health-reporter.js";
import { IndexEvolver } from "./index-evolver.js";

/** Cached health report */
interface CachedAssessment {
  report: HealthReport;
  timestamp: number;
  ttl: number;
}

/** Query statistics collector */
interface QueryStats {
  totalQueries: number;
  indexHits: Map<string, number>;
  latencies: Map<string, number[]>;
}

/**
 * StructureOptimizer — orchestrates structure optimization.
 *
 * Usage:
 *   const optimizer = new StructureOptimizer();
 *   const report = await optimizer.assess();
 *   const suggestions = await optimizer.suggest();
 */
export class StructureOptimizer {
  private options: Required<StructureOptimizerOptions>;
  private healthReporter: HealthReporter;
  private indexEvolver: IndexEvolver;
  private cachedAssessment: CachedAssessment | null = null;
  private history: OptimizeRecord[] = [];
  private queryStats: QueryStats = {
    totalQueries: 0,
    indexHits: new Map(),
    latencies: new Map(),
  };
  private stats: OptimizerStats = {
    totalAssessments: 0,
    totalSuggestions: 0,
    avgAssessmentTimeMs: 0,
    avgHealthScore: 0,
    lastAssessmentTime: 0,
  };
  private totalAssessmentTime = 0;
  private totalHealthScore = 0;

  constructor(options?: StructureOptimizerOptions) {
    this.options = {
      ...DEFAULT_OPTIMIZER_OPTIONS,
      ...options,
    };
    this.healthReporter = new HealthReporter(this.options);
    this.indexEvolver = new IndexEvolver(this.options);
  }

  /**
   * Assess current index health status.
   */
  async assess(refresh: boolean = false): Promise<HealthReport> {
    const startTime = Date.now();

    // Check cache
    if (!refresh && this.options.enableCache && this.cachedAssessment) {
      const age = Date.now() - this.cachedAssessment.timestamp;
      if (age < this.cachedAssessment.ttl) {
        this.cachedAssessment.report.metadata.cacheHit = true;
        return this.cachedAssessment.report;
      }
    }

    // Collect index statistics (MVP: simulated)
    const indexStats = this.collectIndexStats();

    // Generate health report
    const report = this.healthReporter.generateReport(
      indexStats,
      this.queryStats.totalQueries
    );

    // Add missing index suggestions
    report.missingIndexes = this.indexEvolver.detectMissingIndexSuggestions(indexStats);

    // Cache result
    if (this.options.enableCache) {
      this.cachedAssessment = {
        report,
        timestamp: Date.now(),
        ttl: this.options.cacheTtlMs,
      };
    }

    // Update stats
    const assessmentTime = Date.now() - startTime;
    this.stats.totalAssessments++;
    this.totalAssessmentTime += assessmentTime;
    this.stats.avgAssessmentTimeMs = this.totalAssessmentTime / this.stats.totalAssessments;
    this.totalHealthScore += report.overallScore;
    this.stats.avgHealthScore = this.totalHealthScore / this.stats.totalAssessments;
    this.stats.lastAssessmentTime = Date.now();

    return report;
  }

  /**
   * Get optimization suggestions without execution.
   */
  async suggest(): Promise<OptimizeSuggestion[]> {
    const report = await this.assess();

    // Generate suggestions from evolver
    const suggestions = this.indexEvolver.generateAllSuggestions(report.indexStats);

    // Update stats
    this.stats.totalSuggestions += suggestions.length;

    return suggestions;
  }

  /**
   * Execute optimization (MVP: only returns suggestions).
   */
  async optimize(options?: OptimizeOptions): Promise<OptimizeResult> {
    const opts = { ...DEFAULT_OPTIMIZE_OPTIONS, ...options };
    const startTime = Date.now();

    // Get suggestions
    const allSuggestions = await this.suggest();

    // Filter by type if specified
    const filtered = opts.types.length > 0
      ? allSuggestions.filter((s) => opts.types.includes(s.type))
      : allSuggestions;

    // Limit changes
    const limited = filtered.slice(0, opts.maxChanges);

    // MVP: Never auto-apply, just return suggestions
    const result: OptimizeResult = {
      executed: false,
      suggestions: limited,
      duration: Date.now() - startTime,
      estimatedImprovement: this.calculateEstimatedImprovement(limited),
    };

    // Record in history
    const record: OptimizeRecord = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      suggestionsApplied: [],
      result: "skipped",
      duration: result.duration,
      healthBefore: (await this.assess()).overallScore,
    };
    this.history.push(record);

    return result;
  }

  /**
   * Get optimization history.
   */
  async getHistory(limit: number = 10): Promise<OptimizeRecord[]> {
    return this.history.slice(-limit);
  }

  /**
   * Get optimizer statistics.
   */
  getStats(): OptimizerStats {
    return { ...this.stats };
  }

  /**
   * Reset statistics.
   */
  resetStats(): void {
    this.stats = {
      totalAssessments: 0,
      totalSuggestions: 0,
      avgAssessmentTimeMs: 0,
      avgHealthScore: 0,
      lastAssessmentTime: 0,
    };
    this.totalAssessmentTime = 0;
    this.totalHealthScore = 0;
  }

  /**
   * Record a query for statistics.
   */
  recordQuery(indexUsed: string, latencyMs: number): void {
    this.queryStats.totalQueries++;

    const hits = this.queryStats.indexHits.get(indexUsed) ?? 0;
    this.queryStats.indexHits.set(indexUsed, hits + 1);

    const latencies = this.queryStats.latencies.get(indexUsed) ?? [];
    latencies.push(latencyMs);
    this.queryStats.latencies.set(indexUsed, latencies);
  }

  // ── Private Methods ─────────────────────────────────────────────────────

  private collectIndexStats(): IndexStat[] {
    const stats: IndexStat[] = [];
    const now = Date.now();

    // BM25 Index
    const bm25Hits = this.queryStats.indexHits.get("bm25") ?? 0;
    const bm25Latencies = this.queryStats.latencies.get("bm25") ?? [];
    stats.push({
      name: "bm25",
      type: IndexType.BM25,
      hitRate: this.queryStats.totalQueries > 0
        ? bm25Hits / this.queryStats.totalQueries
        : 0,
      avgLatency: bm25Latencies.length > 0
        ? bm25Latencies.reduce((a, b) => a + b, 0) / bm25Latencies.length
        : 10,
      size: 1024 * 1024, // 1MB placeholder
      lastUsed: bm25Hits > 0 ? now : now - 30 * 24 * 60 * 60 * 1000,
      queryCount: bm25Hits,
      createdAt: now - 60 * 24 * 60 * 60 * 1000, // 60 days ago
    });

    // Entity Co-occurrence Index
    const entityHits = this.queryStats.indexHits.get("entity_cooc") ?? 0;
    const entityLatencies = this.queryStats.latencies.get("entity_cooc") ?? [];
    stats.push({
      name: "entity_cooc",
      type: IndexType.ENTITY_COOC,
      hitRate: this.queryStats.totalQueries > 0
        ? entityHits / this.queryStats.totalQueries
        : 0,
      avgLatency: entityLatencies.length > 0
        ? entityLatencies.reduce((a, b) => a + b, 0) / entityLatencies.length
        : 5,
      size: 512 * 1024, // 512KB placeholder
      lastUsed: entityHits > 0 ? now : now - 30 * 24 * 60 * 60 * 1000,
      queryCount: entityHits,
      createdAt: now - 30 * 24 * 60 * 60 * 1000,
    });

    return stats;
  }

  private calculateEstimatedImprovement(suggestions: OptimizeSuggestion[]): number {
    if (suggestions.length === 0) return 0;

    return Math.round(
      suggestions.reduce((sum, s) => sum + s.estimatedBenefit, 0) /
        Math.max(suggestions.length, 1)
    );
  }
}