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
  /** Weight for semantic search results (default: 0.5) */
  semanticWeight: number;
  /** Weight for keyword search results (default: 0.5) */
  keywordWeight: number;
  /** Score normalization method (default: 'minmax') */
  normalization: "minmax" | "softmax" | "none";
}

/**
 * Default fusion configuration (balanced).
 */
export const DEFAULT_FUSION_CONFIG: FusionConfig = {
  semanticWeight: 0.5,
  keywordWeight: 0.5,
  normalization: "minmax",
};

/**
 * Scored result with fusion breakdown.
 */
export interface ScoredResult extends RetrievalResult {
  semanticScore?: number;
  keywordScore?: number;
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

      // Balanced fusion: weight_semantic * semantic + weight_keyword * keyword
      const fusedScore =
        cfg.semanticWeight * semScore + cfg.keywordWeight * kwScore;

      return {
        ...r,
        semanticScore: semScore,
        keywordScore: kwScore,
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
