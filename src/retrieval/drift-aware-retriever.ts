// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * DriftAwareRetriever — drift-aware memory retrieval for claw-mem v6.3.0.
 *
 * Adjusts retrieval scoring weights based on context drift detected by
 * claw-ctx DriftDetector. High drift → prioritize recency over frequency.
 */

import type { RetrievalResult } from "./base.js";

// ── Types ─────────────────────────────────────────────────────────────────

export interface WeightConfig {
  normal: {
    recency: number;
    importance: number;
    frequency: number;
    relevance: number;
  };
  highDrift: {
    recency: number;
    importance: number;
    frequency: number;
    relevance: number;
  };
}

export const DEFAULT_WEIGHT_CONFIG: WeightConfig = {
  normal: {
    recency: 1.0,
    importance: 1.0,
    frequency: 1.0,
    relevance: 1.0,
  },
  highDrift: {
    recency: 1.5,
    importance: 0.8,
    frequency: 0.5,
    relevance: 1.2,
  },
};

export interface DriftAwareResult extends RetrievalResult {
  driftAdjustedScore: number;
  originalScore: number;
  driftLevel: "normal" | "elevated" | "high";
}

export type DriftMode = "auto" | "manual";

export interface DriftDetectorLike {
  getDriftScore(): number;
  getAlerts?(): Array<{ level: string; driftScore: number }>;
  getConfig?(): { alertLevels: { low: number; medium: number; high: number } };
}

export interface DriftAwareConfig {
  mode: DriftMode;
  manualDriftScore: number;
  weightConfig: WeightConfig;
  /** Auto mode only: how often to poll drift score (ms). */
  refreshIntervalMs: number;
}

export const DEFAULT_DRIFT_AWARE_CONFIG: DriftAwareConfig = {
  mode: "auto",
  manualDriftScore: 0,
  weightConfig: DEFAULT_WEIGHT_CONFIG,
  refreshIntervalMs: 30000,
};

// ── DriftAwareRetriever ────────────────────────────────────────────────────

export class DriftAwareRetriever {
  private driftDetector: DriftDetectorLike | null;
  private config: DriftAwareConfig;
  private cachedDriftScore = 0;
  private lastRefresh = 0;

  constructor(driftDetector?: DriftDetectorLike, config?: Partial<DriftAwareConfig>) {
    this.driftDetector = driftDetector ?? null;
    this.config = { ...DEFAULT_DRIFT_AWARE_CONFIG, ...config };
  }

  /** Set or replace the drift detector (from claw-ctx). */
  setDriftDetector(detector: DriftDetectorLike): void {
    this.driftDetector = detector;
    this.lastRefresh = 0;
  }

  /** Adjust scoring weights based on current drift level. */
  adjustWeights(driftScore: number): {
    recency: number;
    importance: number;
    frequency: number;
    relevance: number;
  } {
    const cfg = this.config.weightConfig;
    const driftLevel = this.classifyDrift(driftScore);

    if (driftLevel === "high") {
      return { ...cfg.highDrift };
    }

    if (driftLevel === "elevated") {
      // Blend between normal and highDrift
      const t = driftScore / 0.7;
      return {
        recency: cfg.normal.recency + (cfg.highDrift.recency - cfg.normal.recency) * t,
        importance: cfg.normal.importance + (cfg.highDrift.importance - cfg.normal.importance) * t,
        frequency: cfg.normal.frequency + (cfg.highDrift.frequency - cfg.normal.frequency) * t,
        relevance: cfg.normal.relevance + (cfg.highDrift.relevance - cfg.normal.relevance) * t,
      };
    }

    return { ...cfg.normal };
  }

  /** Retrieve with drift-adjusted scoring. */
  retrieve(
    query: string,
    baseResults: RetrievalResult[],
    options?: { mode?: DriftMode; manualScore?: number },
  ): DriftAwareResult[] {
    const driftScore = this.getCurrentDriftScore(options);
    const weights = this.adjustWeights(driftScore);
    const driftLevel = this.classifyDrift(driftScore);

    return baseResults
      .map((r) => {
        const baseScore = r.score ?? 0;
        const adjustedScore = this.computeAdjustedScore(r, weights);
        return {
          ...r,
          driftAdjustedScore: Math.round(adjustedScore * 1000) / 1000,
          originalScore: baseScore,
          driftLevel,
        };
      })
      .sort((a, b) => b.driftAdjustedScore - a.driftAdjustedScore);
  }

  /** Set operation mode. */
  setMode(mode: DriftMode): void {
    this.config.mode = mode;
  }

  /** Get current mode. */
  getMode(): DriftMode {
    return this.config.mode;
  }

  /** Get current drift score (manual or auto from detector). */
  getDriftScore(): number {
    return this.getCurrentDriftScore();
  }

  /** Update weight configuration. */
  updateWeightConfig(config: Partial<WeightConfig>): void {
    this.config.weightConfig = {
      normal: { ...this.config.weightConfig.normal, ...config.normal },
      highDrift: { ...this.config.weightConfig.highDrift, ...config.highDrift },
    };
  }

  /** Get current configuration. */
  getConfig(): DriftAwareConfig {
    return { ...this.config, weightConfig: { ...this.config.weightConfig } };
  }

  // ── Private ───────────────────────────────────────────────────────────

  private getCurrentDriftScore(options?: { mode?: DriftMode; manualScore?: number }): number {
    const mode = options?.mode ?? this.config.mode;

    if (mode === "manual") {
      return options?.manualScore ?? this.config.manualDriftScore;
    }

    // Auto mode: poll from detector
    if (this.driftDetector) {
      const now = Date.now();
      if (now - this.lastRefresh > this.config.refreshIntervalMs) {
        this.cachedDriftScore = this.driftDetector.getDriftScore();
        this.lastRefresh = now;
      }
      return this.cachedDriftScore;
    }

    return 0;
  }

  private classifyDrift(score: number): "normal" | "elevated" | "high" {
    if (score >= 0.7) return "high";
    if (score >= 0.4) return "elevated";
    return "normal";
  }

  private computeAdjustedScore(
    result: RetrievalResult,
    weights: ReturnType<DriftAwareRetriever["adjustWeights"]>,
  ): number {
    const base = result.score ?? 0;

    // Estimate component scores from metadata if available
    const meta = (result as any).metadata ?? {};
    const recencyComponent = (meta.recency_score as number) ?? base * 0.25;
    const importanceComponent = (meta.importance_score as number) ?? base * 0.25;
    const frequencyComponent = (meta.frequency_score as number) ?? base * 0.25;
    const relevanceComponent = (meta.relevance_score as number) ?? base * 0.25;

    return (
      recencyComponent * weights.recency +
      importanceComponent * weights.importance +
      frequencyComponent * weights.frequency +
      relevanceComponent * weights.relevance
    );
  }
}
