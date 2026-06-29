// claw-mem v6.29.0 — Completeness Scorer (TypeScript)
//
// Evaluates retrieval result completeness.
// Paper F2: Evidence completeness > first-hit accuracy
//
// Licensed under the Apache License, Version 2.0

import type { RetrievalResult } from "./base.js";
import { tokenize } from "./keyword.js";

/**
 * Completeness score breakdown.
 */
export interface CompletenessBreakdown {
  /** Coverage: how many query keywords are covered by results */
  coverage: number;
  /** Diversity: how different are the results from each other */
  diversity: number;
  /** Confidence: average score of results */
  confidence: number;
}

/**
 * Detailed completeness score result.
 */
export interface CompletenessScore {
  /** Overall completeness score [0, 1] */
  score: number;
  /** Recall@10 estimate */
  recallAt10: number;
  /** Score breakdown */
  breakdown: CompletenessBreakdown;
}

/**
 * CompletenessScorer — evaluates how complete the retrieval results are.
 *
 * Paper F2: Evidence completeness (coverage + diversity) > first-hit accuracy.
 * Uses coverage (40%), diversity (30%), and confidence (30%) weighted scoring.
 */
export class CompletenessScorer {
  /**
   * Compute completeness score for retrieval results.
   *
   * @param results - Retrieval results to score
   * @param query - Original query
   * @returns Overall completeness score [0, 1]
   */
  score(results: RetrievalResult[], query: string): number {
    return this.scoreDetailed(results, query).score;
  }

  /**
   * Get detailed completeness breakdown.
   *
   * @param results - Retrieval results to score
   * @param query - Original query
   * @returns Detailed completeness score
   */
  scoreDetailed(results: RetrievalResult[], query: string): CompletenessScore {
    if (results.length === 0) {
      return {
        score: 0,
        recallAt10: 0,
        breakdown: { coverage: 0, diversity: 0, confidence: 0 },
      };
    }

    // 1. Extract query keywords
    const queryKeywords = this.extractKeywords(query);

    // 2. Compute coverage: how many query keywords are covered
    const coverage = this.computeCoverage(results, queryKeywords);

    // 3. Compute diversity: how different are results from each other
    const diversity = this.computeDiversity(results);

    // 4. Compute confidence: average result score
    const confidence = this.computeConfidence(results);

    // 5. Overall score (weighted average)
    // Coverage is most important (paper F2), then diversity, then confidence
    const overall = 0.4 * coverage + 0.3 * diversity + 0.3 * confidence;

    // 6. Estimate Recall@10
    const recallAt10 = this.estimateRecallAt10(results, query);

    return {
      score: overall,
      recallAt10,
      breakdown: { coverage, diversity, confidence },
    };
  }

  /**
   * Extract keywords from query.
   */
  private extractKeywords(query: string): Set<string> {
    const tokens = tokenize(query);
    return new Set(tokens.map((t) => t.toLowerCase()));
  }

  /**
   * Compute keyword coverage score.
   * Measures how many query keywords appear in the results.
   */
  private computeCoverage(
    results: RetrievalResult[],
    queryKeywords: Set<string>,
  ): number {
    if (queryKeywords.size === 0) return 1.0; // No keywords = full coverage

    // Combine all result content
    const allContent = results
      .map((r) => (r.text ?? "").toLowerCase())
      .join(" ");

    // Count covered keywords
    let covered = 0;
    for (const kw of queryKeywords) {
      if (allContent.includes(kw)) {
        covered++;
      }
    }

    return covered / queryKeywords.size;
  }

  /**
   * Compute result diversity score.
   * Measures how different results are from each other (Jaccard distance).
   */
  private computeDiversity(results: RetrievalResult[]): number {
    if (results.length < 2) return 1.0; // Single result = max diversity

    // Limit to top 10 results for O(n²) bound
    const topResults = results.slice(0, 10);

    let totalDistance = 0;
    let pairs = 0;

    for (let i = 0; i < topResults.length; i++) {
      for (let j = i + 1; j < topResults.length; j++) {
        const words1 = new Set(
          (topResults[i].text ?? "").toLowerCase().split(/\s+/).filter(Boolean),
        );
        const words2 = new Set(
          (topResults[j].text ?? "").toLowerCase().split(/\s+/).filter(Boolean),
        );

        // Jaccard similarity
        const intersection = new Set([...words1].filter((w) => words2.has(w)));
        const union = new Set([...words1, ...words2]);
        const jaccard = union.size > 0 ? intersection.size / union.size : 0;

        // Distance = 1 - similarity
        totalDistance += 1 - jaccard;
        pairs++;
      }
    }

    return pairs > 0 ? totalDistance / pairs : 0;
  }

  /**
   * Compute confidence score from result scores.
   */
  private computeConfidence(results: RetrievalResult[]): number {
    if (results.length === 0) return 0;

    const sum = results.reduce((acc, r) => acc + (r.score ?? 0), 0);
    return sum / results.length;
  }

  /**
   * Estimate Recall@10 based on result distribution.
   *
   * This is a heuristic estimate:
   * - High coverage + high diversity + high confidence → high recall
   * - Low coverage or low diversity → lower recall
   */
  private estimateRecallAt10(
    results: RetrievalResult[],
    query: string,
  ): number {
    if (results.length === 0) return 0;

    const queryKeywords = this.extractKeywords(query);
    const coverage = this.computeCoverage(results, queryKeywords);
    const diversity = this.computeDiversity(results);

    // Heuristic: recall ≈ coverage * (1 + 0.2 * diversity)
    // More diverse results suggest better coverage of the query space
    const recall = Math.min(1.0, coverage * (1 + 0.2 * diversity));

    return recall;
  }
}
