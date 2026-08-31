// claw-mem v6.29.0 — Fusion Reranker (TypeScript)
//
// Balanced fusion strategy for combining semantic and keyword search results.
// Paper F8: balanced (50/50) > sparse-leaning (30/70)
//
// Licensed under the Apache License, Version 2.0

import type { RetrievalResult } from "./base.js";

/**
 * Fusion configuration.
 */
export interface FusionConfig {
  /** Weight for semantic search results (default: 0.4, v7.5.0) */
  semanticWeight: number;
  /** Weight for keyword search results (default: 0.4, v7.5.0) */
  keywordWeight: number;
  /** Weight for retention score (default: 0.2, v7.5.0; 0 = rollback to two-way fusion) */
  retentionWeight: number;
  /** Score normalization method (default: 'minmax') */
  normalization: "minmax" | "softmax" | "none";
}

/**
 * Default fusion configuration (three-way: semantic + keyword + retention).
 */
export const DEFAULT_FUSION_CONFIG: FusionConfig = {
  semanticWeight: 0.4,
  keywordWeight: 0.4,
  retentionWeight: 0.2,
  normalization: "minmax",
};

/**
 * Scored result with fusion breakdown.
 */
export interface ScoredResult extends RetrievalResult {
  semanticScore?: number;
  keywordScore?: number;
  /** Retention score used in fusion (v7.5.0) */
  retentionScore?: number;
  fusedScore: number;
}

/**
 * FusionReranker — combines and reranks results from multiple sources.
 *
 * Uses balanced fusion with configurable weights.
 * Paper F8 finding: balanced (50/50) outperforms sparse-leaning (30/70).
 */
export class FusionReranker {
  private config: FusionConfig;

  constructor(config?: Partial<FusionConfig>) {
    this.config = { ...DEFAULT_FUSION_CONFIG, ...config };
  }

  /**
   * Rerank results using balanced fusion.
   *
   * @param results - Combined results from semantic and keyword search
   * @param _query - Original query (for future relevance scoring)
   * @param configOverride - Override fusion config for this call
   * @returns Reranked results with fusion scores
   */
  rerank(
    results: RetrievalResult[],
    _query: string,
    configOverride?: Partial<FusionConfig>,
  ): ScoredResult[] {
    if (results.length === 0) return [];

    const cfg = configOverride ? { ...this.config, ...configOverride } : this.config;

    // 1. Separate semantic and keyword results
    const semanticResults = results.filter((r) => r.source === "semantic");
    const keywordResults = results.filter((r) => r.source === "keyword");

    // 2. Normalize scores to [0, 1] range
    const semanticNorm = this.normalizeScores(semanticResults, cfg.normalization);
    const keywordNorm = this.normalizeScores(keywordResults, cfg.normalization);

    // 3. Compute fused scores
    const scored: ScoredResult[] = results.map((r) => {
      const semScore = semanticNorm.get(r.id) ?? 0;
      const kwScore = keywordNorm.get(r.id) ?? 0;
      // v7.5.0 (ADR-002): retention carried on the result by HybridRetriever;
      // missing → neutral 0.5 so ranking is unaffected by uninitialized memories
      const retentionScore = typeof r.retention === "number" ? r.retention : 0.5;

      // Three-way fusion: semantic + keyword + retention
      const fusedScore =
        cfg.semanticWeight * semScore +
        cfg.keywordWeight * kwScore +
        cfg.retentionWeight * retentionScore;

      return {
        ...r,
        semanticScore: semScore,
        keywordScore: kwScore,
        retentionScore,
        fusedScore,
      };
    });

    // 4. Sort by fused score descending
    scored.sort((a, b) => b.fusedScore - a.fusedScore);

    return scored;
  }

  /**
   * Normalize scores to [0, 1] range.
   *
   * @param results - Results from a single source
   * @param method - Normalization method
   * @returns Map of result ID to normalized score
   */
  private normalizeScores(
    results: RetrievalResult[],
    method: "minmax" | "softmax" | "none",
  ): Map<string, number> {
    const normalized = new Map<string, number>();

    if (results.length === 0) return normalized;

    // Extract scores
    const scores = results.map((r) => r.score ?? 0);
    const min = Math.min(...scores);
    const max = Math.max(...scores);

    for (const r of results) {
      const score = r.score ?? 0;

      let norm: number;
      switch (method) {
        case "none":
          norm = score;
          break;

        case "softmax": {
          // Softmax would require all scores, simplified here
          const exp = Math.exp(score);
          const sumExp = scores.reduce((s, v) => s + Math.exp(v), 0);
          norm = sumExp > 0 ? exp / sumExp : 0;
          break;
        }

        case "minmax":
        default:
          if (max === min) {
            // All scores are equal
            norm = 0.5;
          } else {
            norm = (score - min) / (max - min);
          }
          break;
      }

      normalized.set(r.id, norm);
    }

    return normalized;
  }

  /**
   * Get current fusion configuration.
   */
  getConfig(): FusionConfig {
    return { ...this.config };
  }

  /**
   * Update fusion configuration.
   */
  setConfig(config: Partial<FusionConfig>): void {
    this.config = { ...this.config, ...config };
  }
}
