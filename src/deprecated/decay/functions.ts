// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Decay functions and configuration for the Oblivion forgetting mechanism.
 *
 * Core formula: weight(t) = base * exp(-lambda * days)
 *   lambda = ln(2) / half_life_days
 */

// ── Half-life constants (days) ─────────────────────────────────────────

export const HALF_LIFE: Record<string, number> = {
  episodic: 7.0,
  semantic: 90.0,
  procedural: 180.0,
  temporal: 7.0,
  causal: 14.0,
  entity: 30.0,
  fact_node: 90.0,
  episode_node: 7.0,
};

const LN2 = Math.LN2;

// Decay rate lambda = ln(2) / half_life
export const LAMBDA: Record<string, number> = {};
for (const [k, v] of Object.entries(HALF_LIFE)) {
  LAMBDA[k] = LN2 / v;
}

// ── Core decay function ────────────────────────────────────────────────

/**
 * Compute exponential decay weight.
 *
 * @param base - Initial weight (typically 1.0).
 * @param daysElapsed - Days since creation/last-update.
 * @param halfLifeDays - Half-life in days.
 * @returns Decayed weight in [0.0, 1.0].
 */
export function exponentialDecay(
  base: number,
  daysElapsed: number,
  halfLifeDays: number,
): number {
  if (daysElapsed <= 0) return base;
  if (halfLifeDays <= 0) return 0.0;
  const decayRate = LN2 / halfLifeDays;
  return base * Math.exp(-decayRate * daysElapsed);
}

/**
 * Calculate decayed weight for a given category.
 *
 * @param initialWeight - Starting weight (default 1.0).
 * @param daysElapsed - Days since creation.
 * @param category - Half-life category name ("temporal", "semantic", etc.).
 * @returns Decayed weight.
 */
export function calculateWeight(
  initialWeight: number,
  daysElapsed: number,
  category: string,
): number {
  const halfLife = HALF_LIFE[category] ?? 30.0;
  return exponentialDecay(initialWeight, daysElapsed, halfLife);
}

/**
 * Infer half-life from observed decay (for adaptive tuning).
 *
 * Uses the formula: t_half = -ln(2) * days / ln(weight / initial)
 */
export function halfLifeToDays(
  weight: number,
  initial: number,
  daysElapsed: number,
): number {
  if (weight >= initial || weight <= 0 || daysElapsed <= 0) return 30.0;
  return (-LN2 * daysElapsed) / Math.log(weight / initial);
}

// ── Configuration ──────────────────────────────────────────────────────

/** Decay configuration, tunable via MemoryManager constructor. */
export interface DecayConfig {
  /** Half-life per category (days) */
  halfLifeTemporal: number;
  halfLifeCausal: number;
  halfLifeSemantic: number;
  halfLifeEntity: number;
  halfLifeEpisodeNode: number;
  halfLifeFactNode: number;

  /** Weight thresholds */
  strongThreshold: number;
  archiveThreshold: number;
  expireThreshold: number;
  purgeThreshold: number;

  /** Scheduler settings */
  decayIntervalHours: number;
  batchSize: number;
  maxConcurrent: number;

  /** Protection */
  protectCritical: boolean;
  protectPinned: boolean;
}

/** Default decay configuration. */
export const DEFAULT_DECAY_CONFIG: DecayConfig = {
  halfLifeTemporal: 7.0,
  halfLifeCausal: 14.0,
  halfLifeSemantic: 90.0,
  halfLifeEntity: 30.0,
  halfLifeEpisodeNode: 7.0,
  halfLifeFactNode: 90.0,

  strongThreshold: 0.7,
  archiveThreshold: 0.3,
  expireThreshold: 0.1,
  purgeThreshold: 0.05,

  decayIntervalHours: 24,
  batchSize: 1000,
  maxConcurrent: 1,

  protectCritical: true,
  protectPinned: true,
};
