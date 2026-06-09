// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Dreaming Engine -- Deep Phase (Candidate Scorer | v4.12.0)
 *
 * Six-dimensional heuristic scoring with weighted composite.
 * Scores normalized to 0.0-1.0, weighted by DreamingConfig.
 */

import { DEFAULT_DREAMING_CONFIG, type DreamingConfig } from "./config";
import type { Signal } from "./light";

// ── ScoredCandidate ──────────────────────────────────────────────────────

export interface ScoredCandidate {
  /** The original staged signal. */
  signal: Signal;
  /** 0.0-1.0, based on recall_count. */
  frequencyScore: number;
  /** 0.0-1.0, from prior relevance_scores. */
  relevanceScore: number;
  /** 0.0-1.0, based on unique_queries. */
  queryDiversityScore: number;
  /** 0.0-1.0, temporal freshness. */
  recencyScore: number;
  /** 0.0-1.0, integration with existing knowledge. */
  consolidationScore: number;
  /** 0.0-1.0, information density. */
  conceptualRichnessScore: number;
  /** Weighted sum of all six scores. */
  composite: number;
}

export function createScoredCandidate(
  signal: Signal,
  overrides?: Partial<Omit<ScoredCandidate, "signal">>,
): ScoredCandidate {
  return {
    signal,
    frequencyScore: 0,
    relevanceScore: 0,
    queryDiversityScore: 0,
    recencyScore: 0,
    consolidationScore: 0,
    conceptualRichnessScore: 0,
    composite: 0,
    ...overrides,
  };
}

export function scoredCandidateToDict(c: ScoredCandidate): Record<string, unknown> {
  return {
    signal: {
      memory_id: c.signal.memoryId,
      content: c.signal.content,
      memory_type: c.signal.memoryType,
      recall_count: c.signal.recallCount,
      unique_queries: c.signal.uniqueQueries,
      relevance_scores: c.signal.relevanceScores,
      tags: c.signal.tags,
      timestamp: c.signal.timestamp,
    },
    frequency_score: round3(c.frequencyScore),
    relevance_score: round3(c.relevanceScore),
    query_diversity_score: round3(c.queryDiversityScore),
    recency_score: round3(c.recencyScore),
    consolidation_score: round3(c.consolidationScore),
    conceptual_richness_score: round3(c.conceptualRichnessScore),
    composite: round3(c.composite),
  };
}

function round3(v: number): number {
  return Math.round(v * 1000) / 1000;
}

// ── CandidateScorer ──────────────────────────────────────────────────────

export class CandidateScorer {
  private _config: DreamingConfig;

  constructor(config?: DreamingConfig) {
    this._config = config ?? DEFAULT_DREAMING_CONFIG;
  }

  /**
   * Score all staged signals.
   *
   * @param signals - List of Signal objects from the light phase.
   * @returns List of ScoredCandidate sorted by composite descending.
   */
  scoreAll(signals: Signal[]): ScoredCandidate[] {
    const candidates: ScoredCandidate[] = [];

    for (const sig of signals) {
      const freq = this._scoreFrequency(sig);
      const rel = this._scoreRelevance(sig);
      const div = this._scoreQueryDiversity(sig);
      const rec = this._scoreRecency(sig);
      const con = this._scoreConsolidation(sig);
      const rich = this._scoreConceptualRichness(sig);

      const composite =
        freq * this._config.frequencyWeight +
        rel * this._config.relevanceWeight +
        div * this._config.queryDiversityWeight +
        rec * this._config.recencyWeight +
        con * this._config.consolidationWeight +
        rich * this._config.conceptualRichnessWeight;

      candidates.push({
        signal: sig,
        frequencyScore: freq,
        relevanceScore: rel,
        queryDiversityScore: div,
        recencyScore: rec,
        consolidationScore: con,
        conceptualRichnessScore: rich,
        composite,
      });
    }

    candidates.sort((a, b) => b.composite - a.composite);
    return candidates;
  }

  /**
   * Filter candidates by score threshold and top-k.
   *
   * @param candidates - Scored candidates (already sorted by composite).
   * @returns Filtered list of ScoredCandidate.
   */
  filter(candidates: ScoredCandidate[]): ScoredCandidate[] {
    const aboveThreshold = candidates.filter(
      (c) => c.composite >= this._config.scoreThreshold,
    );
    return aboveThreshold.slice(0, this._config.topKCandidates);
  }

  // ── dimension scorers ──────────────────────────────────────────────────

  /** Score based on recall_count. Saturates at ~10. */
  private _scoreFrequency(sig: Signal): number {
    return Math.min(sig.recallCount / 10.0, 1.0);
  }

  /** Average of existing relevance scores, defaulting to 0.5. */
  private _scoreRelevance(sig: Signal): number {
    const scores = sig.relevanceScores;
    if (!scores || scores.length === 0) return 0.5;
    return scores.reduce((a, b) => a + b, 0) / scores.length;
  }

  /** Score based on unique query count. Saturates at ~5. */
  private _scoreQueryDiversity(sig: Signal): number {
    return Math.min(sig.uniqueQueries / 5.0, 1.0);
  }

  /** Exponential decay from timestamp. Newer = higher score. */
  private _scoreRecency(sig: Signal): number {
    if (!sig.timestamp) return 0.5;
    try {
      const ts = new Date(sig.timestamp);
      const now = new Date();
      const ageMs = now.getTime() - ts.getTime();
      const ageHours = Math.max(0, ageMs / 3600000);
      // Half-life of 24 hours
      return Math.exp(-ageHours / 24.0);
    } catch {
      return 0.5;
    }
  }

  /** Proxy: higher tag count suggests better integration. */
  private _scoreConsolidation(sig: Signal): number {
    const tagCount = sig.tags?.length ?? 0;
    return Math.min(tagCount / 5.0, 1.0);
  }

  /**
   * Proxy: content length and capitalized-word count as information density.
   */
  private _scoreConceptualRichness(sig: Signal): number {
    const text = sig.content ?? "";
    // Length component
    const lengthScore = Math.min(text.length / 200.0, 1.0);
    // Named entity proxy: uppercase words as simple heuristic
    const entities = (text.match(/\b[A-Z][a-z]+\b/g) ?? []).length;
    const entityScore = Math.min(entities / 3.0, 1.0);
    return lengthScore * 0.6 + entityScore * 0.4;
  }
}
