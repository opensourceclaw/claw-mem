// claw-mem v7.5.0 — Retention Score Engine (TypeScript)
//
// Usage-based retention scoring (ADR-002): memories are scored by selection
// events, not by wall-clock age. Selected -> boost + streak reset; candidate
// missed -> exponential decay by consecutive miss count.
//
// Licensed under the Apache License, Version 2.0

/** Per-memory retention state. */
export interface RetentionState {
  /** Utility score u ∈ [0,1], event-initialized (0.75/0.30/0.5). */
  score: number;
  /** Consecutive candidate-missed count m. */
  missedStreak: number;
  /** Last selected ISO timestamp (audit only, not part of computation). */
  lastSelected: string;
  /** State initialization timestamp. */
  initializedAt: string;
}

/** Tunable retention parameters (defaults mirror WMT paper values). */
export interface RetentionEngineConfig {
  /** Decay base ρ (0.85): per-miss retention factor. */
  rho: number;
  /** Missed-streak cap M (5): decay floor reached after M consecutive misses. */
  maxStreak: number;
  /** Score boost on selection (0.1). */
  selectedBoost: number;
  /** Initial score for store with outcome=success (0.75). */
  successScore: number;
  /** Initial score for store with outcome=failure (0.30). */
  failureScore: number;
  /** Neutral score for unknown ids / legacy data (0.5). */
  neutralScore: number;
}

export const DEFAULT_RETENTION_CONFIG: RetentionEngineConfig = {
  rho: 0.85,
  maxStreak: 5,
  selectedBoost: 0.1,
  successScore: 0.75,
  failureScore: 0.30,
  neutralScore: 0.5,
};

/** Retention distribution stats for memory_stats. */
export interface RetentionStats {
  count: number;
  mean: number;
  median: number;
  belowThreshold: number;
  /** Configurable threshold used for belowThreshold (default 0.3). */
  threshold: number;
}

/**
 * RetentionScoreEngine — in-memory retention state machine.
 *
 * Pure state machine, no I/O: MemoryManager hydrates states from
 * `metadata.retention` (lazy) and persists updates back after events.
 *
 * Note on decay formula: ADR-002 states `score^(ρ^min(m,M))`, but for
 * score∈(0,1) and ρ∈(0,1) that expression *raises* the score (0.75^0.44≈0.88
 * after 5 misses), contradicting the decay intent and the acceptance anchor
 * "5 missed → score ≤ 0.5·initial". Implemented as per-event geometric
 * decay `score · ρ^min(m,M)` (cumulative: 5 misses → 0.75·ρ^15≈0.066),
 * which satisfies the anchor.
 */
export class RetentionScoreEngine {
  private config: RetentionEngineConfig;
  private states = new Map<string, RetentionState>();

  constructor(config?: Partial<RetentionEngineConfig>) {
    this.config = { ...DEFAULT_RETENTION_CONFIG, ...config };
  }

  /** Initialize state; outcome=success→0.75, failure→0.30, none→0.5 (neutral). */
  initialize(id: string, outcome?: "success" | "failure"): RetentionState {
    const score =
      outcome === "success"
        ? this.config.successScore
        : outcome === "failure"
          ? this.config.failureScore
          : this.config.neutralScore;
    const state: RetentionState = {
      score,
      missedStreak: 0,
      lastSelected: "",
      initializedAt: new Date().toISOString(),
    };
    this.states.set(id, state);
    return state;
  }

  /** Selection event: boost score (cap 1.0) and reset missed streak. */
  onSelected(id: string): RetentionState {
    const base = this.states.get(id) ?? this.initialize(id);
    const state: RetentionState = {
      ...base,
      score: Math.min(1, base.score + this.config.selectedBoost),
      missedStreak: 0,
      lastSelected: new Date().toISOString(),
    };
    this.states.set(id, state);
    return state;
  }

  /** Candidate-missed event: increment streak, decay by ρ^min(m,M). */
  onCandidateMissed(id: string): RetentionState {
    const base = this.states.get(id) ?? this.initialize(id);
    const m = base.missedStreak + 1;
    const decay = Math.pow(this.config.rho, Math.min(m, this.config.maxStreak));
    const state: RetentionState = {
      ...base,
      score: this.clip01(base.score * decay),
      missedStreak: m,
    };
    this.states.set(id, state);
    return state;
  }

  /** Current score for ranking; unknown id → neutral 0.5. */
  getRetentionScore(id: string): number {
    return this.states.get(id)?.score ?? this.config.neutralScore;
  }

  /** Raw state (for persistence); null when uninitialized. */
  getState(id: string): RetentionState | null {
    return this.states.get(id) ?? null;
  }

  /** Hydrate state from persisted metadata (lazy restore). */
  setState(id: string, state: RetentionState): void {
    this.states.set(id, state);
  }

  /** Distribution stats for memory_stats (ids with live state only). */
  getStats(threshold = 0.3): RetentionStats {
    const scores = [...this.states.values()].map((s) => s.score).sort((a, b) => a - b);
    if (scores.length === 0) {
      return { count: 0, mean: 0, median: 0, belowThreshold: 0, threshold };
    }
    const mean = scores.reduce((a, b) => a + b, 0) / scores.length;
    const mid = Math.floor(scores.length / 2);
    const median = scores.length % 2 === 0 ? (scores[mid - 1] + scores[mid]) / 2 : scores[mid];
    const belowThreshold = scores.filter((s) => s < threshold).length;
    return { count: scores.length, mean, median, belowThreshold, threshold };
  }

  /** Number of live states. */
  size(): number {
    return this.states.size;
  }

  private clip01(v: number): number {
    return Math.max(0, Math.min(1, v));
  }
}
