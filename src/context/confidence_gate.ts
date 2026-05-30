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
 * F2: ConfidenceGate + GateResult + ConfidenceLevel
 *
 * Four-dimensional confidence scoring:
 *   1. Vector  - search-result score as proxy for embedding distance
 *   2. Time    - tier-based decay signal
 *   3. Conflict- memory in any conflict scores low
 *   4. Frequency- tag-driven heuristic
 */

// ── Enums / Data classes ──────────────────────────────────────────────

export enum ConfidenceLevel {
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

export interface GateResult {
  memory_id?: string;
  confidence_score: number;
  confidence_level: ConfidenceLevel;
  vector_score: number;
  time_score: number;
  conflict_score: number;
  frequency_score: number;
  reason: string;
  warning?: string;
}

// ── ConfidenceGate ────────────────────────────────────────────────────

export class ConfidenceGate {
  static DEFAULT_HIGH = 0.7;
  static DEFAULT_LOW = 0.4;
  static DEFAULT_W_VECTOR = 0.4;
  static DEFAULT_W_TIME = 0.3;
  static DEFAULT_W_CONFLICT = 0.2;
  static DEFAULT_W_FREQUENCY = 0.1;

  manager: any;
  high_threshold: number;
  low_threshold: number;
  weight_vector: number;
  weight_time: number;
  weight_conflict: number;
  weight_frequency: number;

  private _conflict_cache: Set<string> | null = null;
  private _conflict_cache_filled = false;

  constructor(
    manager?: any,
    high_threshold: number = ConfidenceGate.DEFAULT_HIGH,
    low_threshold: number = ConfidenceGate.DEFAULT_LOW,
    weight_vector: number = ConfidenceGate.DEFAULT_W_VECTOR,
    weight_time: number = ConfidenceGate.DEFAULT_W_TIME,
    weight_conflict: number = ConfidenceGate.DEFAULT_W_CONFLICT,
    weight_frequency: number = ConfidenceGate.DEFAULT_W_FREQUENCY,
  ) {
    this.manager = manager;
    this.high_threshold = high_threshold;
    this.low_threshold = low_threshold;
    this.weight_vector = weight_vector;
    this.weight_time = weight_time;
    this.weight_conflict = weight_conflict;
    this.weight_frequency = weight_frequency;
  }

  // ── Public API ─────────────────────────────────────────────────────

  evaluate(memory: Record<string, unknown>): GateResult {
    return this._score(memory);
  }

  evaluate_batch(memories: Record<string, unknown>[]): GateResult[] {
    this._fill_conflict_cache();
    const results = memories.map((m) => this._score(m));
    this._reset_conflict_cache();
    return results;
  }

  filter(memories: Record<string, unknown>[]): Record<string, unknown>[] {
    const results = this.evaluate_batch(memories);
    const kept: Record<string, unknown>[] = [];
    for (let i = 0; i < results.length; i++) {
      if (results[i].confidence_level !== ConfidenceLevel.LOW) {
        kept.push(memories[i]);
      }
    }
    return kept;
  }

  // ── Scoring ────────────────────────────────────────────────────────

  private _score(memory: Record<string, unknown>): GateResult {
    const memId = memory.id as string | undefined;

    const vs = this._compute_vector_score(memory);
    const ts = this._compute_time_score(memory);
    const cs = this._compute_conflict_score(memory);
    const fs = this._compute_frequency_score(memory);

    const available: Record<string, boolean> = {
      vector: vs != null,
      time: ts != null,
      conflict: cs != null,
      frequency: fs != null,
    };

    const effW = this._effective_weights(available);

    const vsVal = vs ?? 0.0;
    const tsVal = ts ?? 0.0;
    const csVal = cs ?? 0.0;
    const fsVal = fs ?? 0.0;

    const composite =
      vsVal * effW.vector +
      tsVal * effW.time +
      csVal * effW.conflict +
      fsVal * effW.frequency;

    let level: ConfidenceLevel;
    if (composite >= this.high_threshold) {
      level = ConfidenceLevel.HIGH;
    } else if (composite >= this.low_threshold) {
      level = ConfidenceLevel.MEDIUM;
    } else {
      level = ConfidenceLevel.LOW;
    }

    const warnings: string[] = [];
    if (!available.time) warnings.push("time_score_unavailable");
    if (!available.conflict) warnings.push("conflict_score_unavailable");

    const reason = `vec=${vsVal.toFixed(2)} t=${tsVal.toFixed(2)} c=${csVal.toFixed(2)} f=${fsVal.toFixed(2)} \u2192 ${composite.toFixed(2)} (${level})`;

    return {
      memory_id: memId,
      confidence_score: Math.round(composite * 10000) / 10000,
      confidence_level: level,
      vector_score: Math.round(vsVal * 10000) / 10000,
      time_score: Math.round(tsVal * 10000) / 10000,
      conflict_score: Math.round(csVal * 10000) / 10000,
      frequency_score: Math.round(fsVal * 10000) / 10000,
      reason,
      warning: warnings.length > 0 ? warnings.join("; ") : undefined,
    };
  }

  private _effective_weights(available: Record<string, boolean>): Record<string, number> {
    const w: Record<string, number> = {
      vector: this.weight_vector,
      time: this.weight_time,
      conflict: this.weight_conflict,
      frequency: this.weight_frequency,
    };

    let unavailableWeight = 0;
    let availableWeight = 0;
    for (const dim of Object.keys(available)) {
      if (available[dim]) {
        availableWeight += w[dim];
      } else {
        unavailableWeight += w[dim];
      }
    }

    if (unavailableWeight <= 0 || availableWeight <= 0) return w;

    const redistributed = unavailableWeight / availableWeight;
    for (const dim of Object.keys(w)) {
      if (available[dim]) {
        w[dim] += w[dim] * redistributed;
      } else {
        w[dim] = 0.0;
      }
    }
    return w;
  }

  // ── Dimension helpers ──────────────────────────────────────────────

  private _compute_vector_score(memory: Record<string, unknown>): number | null {
    const score = memory.score;
    if (score == null) return null;
    const n = Number(score);
    return isNaN(n) ? null : n;
  }

  private _compute_time_score(memory: Record<string, unknown>): number | null {
    if (this.manager == null) return null;
    const td = (this.manager as any).tiered_decay;
    if (td == null) return null;

    // Map tier to score: HOT=1.0, WARM=0.6, COLD=0.3
    const tier = td.classify(memory);
    switch (tier) {
      case "HOT":
        return 1.0;
      case "WARM":
        return 0.6;
      case "COLD":
        return 0.3;
      default:
        return 0.3;
    }
  }

  private _compute_conflict_score(memory: Record<string, unknown>): number | null {
    if (this.manager == null) return null;
    const cd = (this.manager as any).conflict_detector;
    if (cd == null) return null;

    const memId = memory.id as string | undefined;
    if (memId == null) return 0.5;

    if (this._conflict_cache != null) {
      return this._conflict_cache.has(memId) ? 0.3 : 1.0;
    }
    return 1.0;
  }

  private _compute_frequency_score(memory: Record<string, unknown>): number {
    const tags: string[] =
      (memory.tags as string[]) ??
      ((memory.metadata as any)?.tags as string[]) ??
      [];
    if (tags.length === 0) return 0.5;

    const criticalKeywords = [
      "critical",
      "important",
      "\u6c38\u4e45",
      "\u5173\u952e",
      "critical_rule",
    ];
    for (const t of tags) {
      if (typeof t === "string") {
        const lower = t.toLowerCase();
        if (criticalKeywords.some((kw) => lower.includes(kw))) return 1.0;
      }
    }
    return 0.8;
  }

  // ── Conflict cache ─────────────────────────────────────────────────

  private _fill_conflict_cache(): void {
    if (this._conflict_cache_filled) return;
    if (this.manager == null) {
      this._conflict_cache_filled = true;
      return;
    }
    const cd = (this.manager as any).conflict_detector;
    if (cd == null) {
      this._conflict_cache_filled = true;
      return;
    }
    try {
      const conflicts = cd.detect_conflicts();
      const ids = new Set<string>();
      for (const c of conflicts) {
        ids.add(c.memory_id_a);
        ids.add(c.memory_id_b);
      }
      this._conflict_cache = ids;
    } catch {
      this._conflict_cache = new Set();
    }
    this._conflict_cache_filled = true;
  }

  private _reset_conflict_cache(): void {
    this._conflict_cache = null;
    this._conflict_cache_filled = false;
  }
}
