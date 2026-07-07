// claw-mem v6.35.0 — Index Evolver (TypeScript)
//
// Detects index evolution opportunities and generates suggestions.
// MVP: Only generates suggestions, does not auto-execute.
//
// Licensed under the Apache License, Version 2.0

import * as crypto from "crypto";
import {
  IndexStat,
  IndexType,
  OptimizeSuggestion,
  OptimizeSuggestionType,
  OptimizeSuggestionDetails,
  MissingIndexSuggestion,
  SuggestionReason,
  SuggestionPriority,
  QueryPattern,
  DEFAULT_OPTIMIZER_OPTIONS,
} from "./types.js";

/**
 * IndexEvolver — detects index evolution opportunities.
 */
export class IndexEvolver {
  private options: Required<typeof DEFAULT_OPTIMIZER_OPTIONS>;

  constructor(options?: typeof DEFAULT_OPTIMIZER_OPTIONS) {
    this.options = options ?? DEFAULT_OPTIMIZER_OPTIONS;
  }

  /**
   * Detect unused indexes and generate delete suggestions.
   */
  detectUnusedIndexSuggestions(
    indexStats: IndexStat[]
  ): OptimizeSuggestion[] {
    const suggestions: OptimizeSuggestion[] = [];
    const thresholdMs = this.options.unusedDaysThreshold * 24 * 60 * 60 * 1000;
    const now = Date.now();

    for (const stat of indexStats) {
      const ageMs = now - stat.createdAt;

      // Skip indexes created recently (< 24h)
      if (ageMs < 24 * 60 * 60 * 1000) continue;

      // Check if unused
      const unused = now - stat.lastUsed > thresholdMs || stat.queryCount === 0;

      if (unused) {
        const daysUnused = Math.floor((now - stat.lastUsed) / (24 * 60 * 60 * 1000));
        const confidence = Math.min(daysUnused / this.options.unusedDaysThreshold, 1.0);

        suggestions.push({
          id: crypto.randomUUID(),
          type: OptimizeSuggestionType.DELETE_INDEX,
          targetIndex: stat.name,
          description: `Index '${stat.name}' has not been used for ${daysUnused} days`,
          estimatedBenefit: Math.round(stat.size * 0.001), // KB saved
          estimatedRisk: stat.queryCount > 0 ? 0.3 : 0.1, // Lower risk if never used
          confidence,
          details: {
            indexes: [stat.name],
            steps: [
              `Verify no queries depend on '${stat.name}'`,
              `Backup index data if needed`,
              `Remove index '${stat.name}'`,
            ],
          },
          timestamp: now,
        });
      }
    }

    return suggestions;
  }

  /**
   * Detect missing indexes and generate create suggestions.
   * MVP: Based on low hit rate indexes.
   */
  detectMissingIndexSuggestions(
    indexStats: IndexStat[]
  ): MissingIndexSuggestion[] {
    const suggestions: MissingIndexSuggestion[] = [];

    for (const stat of indexStats) {
      if (stat.hitRate < this.options.minHitRateThreshold && stat.queryCount >= this.options.minQueryCount) {
        suggestions.push({
          id: crypto.randomUUID(),
          type: this.suggestIndexType(stat),
          reason: SuggestionReason.SLOW_PERFORMANCE,
          targetPatterns: [],
          estimatedImprovement: Math.round((this.options.minHitRateThreshold - stat.hitRate) * 100),
          confidence: 1 - stat.hitRate,
          priority: stat.hitRate < 0.2 ? SuggestionPriority.HIGH : SuggestionPriority.MEDIUM,
        });
      }
    }

    return suggestions;
  }

  /**
   * Detect merge candidates (indexes with overlapping data).
   * MVP: Placeholder - returns empty.
   */
  detectMergeSuggestions(_indexStats: IndexStat[]): OptimizeSuggestion[] {
    // MVP: Not implemented
    return [];
  }

  /**
   * Detect split candidates (oversized indexes).
   * MVP: Placeholder - returns empty.
   */
  detectSplitSuggestions(_indexStats: IndexStat[]): OptimizeSuggestion[] {
    // MVP: Not implemented
    return [];
  }

  /**
   * Generate all optimization suggestions.
   */
  generateAllSuggestions(indexStats: IndexStat[]): OptimizeSuggestion[] {
    const allSuggestions: OptimizeSuggestion[] = [
      ...this.detectUnusedIndexSuggestions(indexStats),
      ...this.detectMergeSuggestions(indexStats),
      ...this.detectSplitSuggestions(indexStats),
    ];

    // Sort by confidence * estimatedBenefit
    allSuggestions.sort((a, b) => {
      const scoreA = a.confidence * a.estimatedBenefit;
      const scoreB = b.confidence * b.estimatedBenefit;
      return scoreB - scoreA;
    });

    return allSuggestions.slice(0, this.options.maxSuggestions);
  }

  // ── Private Methods ─────────────────────────────────────────────────────

  private suggestIndexType(stat: IndexStat): IndexType {
    // Map existing index type to potential optimization
    switch (stat.type) {
      case IndexType.BM25:
        return IndexType.NGRAM; // Add ngram for prefix queries
      case IndexType.ENTITY_COOC:
        return IndexType.SEMANTIC; // Add semantic for entity similarity
      default:
        return IndexType.BM25;
    }
  }
}