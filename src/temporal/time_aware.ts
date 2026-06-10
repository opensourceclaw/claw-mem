// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * claw-mem Time-Aware Search
 *
 * Calculates time-based weights for search results, boosting recent
 * memories and decaying older ones based on configurable parameters.
 *
 * Weight functions:
 *   - Exponential decay: w = e^(-age/half_life * ln(2))
 *   - Linear decay:     w = max(0, 1 - age/max_age)
 *   - Step decay:       w = 1.0 if age < recent_window else 0.5 if age < older_window else 0.1
 */

export interface TimeWeightConfigOptions {
  decayType?: "exponential" | "linear" | "step";
  halfLifeDays?: number;
  maxAgeDays?: number;
  recentWindowDays?: number;
  olderWindowDays?: number;
  baseWeight?: number;
  minWeight?: number;
}

export class TimeWeightConfig {
  decayType: "exponential" | "linear" | "step";
  halfLifeDays: number;
  maxAgeDays: number;
  recentWindowDays: number;
  olderWindowDays: number;
  baseWeight: number;
  minWeight: number;

  constructor(opts?: TimeWeightConfigOptions) {
    this.decayType = opts?.decayType ?? "exponential";
    this.halfLifeDays = opts?.halfLifeDays ?? 30.0;
    this.maxAgeDays = opts?.maxAgeDays ?? 365.0;
    this.recentWindowDays = opts?.recentWindowDays ?? 7.0;
    this.olderWindowDays = opts?.olderWindowDays ?? 90.0;
    this.baseWeight = opts?.baseWeight ?? 1.0;
    this.minWeight = opts?.minWeight ?? 0.1;
  }

  toDict(): Record<string, unknown> {
    return {
      decay_type: this.decayType,
      half_life_days: this.halfLifeDays,
      max_age_days: this.maxAgeDays,
    };
  }
}

export class TimeWeightCalculator {
  config: TimeWeightConfig;

  constructor(config?: TimeWeightConfig) {
    this.config = config ?? new TimeWeightConfig();
  }

  /**
   * Calculate time weight for a memory timestamp.
   *
   * @param timestamp - ISO format timestamp or date string
   * @param now       - Reference time (defaults to current UTC)
   * @returns Weight between minWeight and baseWeight
   */
  calculate(timestamp: string, now?: Date): number {
    const ageDays = this._ageDays(timestamp, now);

    let weight: number;
    if (this.config.decayType === "linear") {
      weight = Math.max(
        this.config.minWeight,
        this.config.baseWeight * (1 - ageDays / this.config.maxAgeDays),
      );
    } else if (this.config.decayType === "step") {
      weight = this._stepWeight(ageDays);
    } else {
      // exponential (default)
      weight =
        this.config.baseWeight *
        Math.exp((-ageDays / this.config.halfLifeDays) * Math.LN2);
    }

    return Math.max(this.config.minWeight, Math.min(weight, this.config.baseWeight));
  }

  /**
   * Apply time weights to a list of memory records.
   *
   * @param memories      - List of memory dicts with "timestamp" field
   * @param weightField   - Field name to store the weight (default "time_weight")
   * @param sortByWeight  - Sort results by weight descending (default true)
   * @returns Memories with time_weight field added, optionally sorted
   */
  applyWeights(
    memories: Record<string, unknown>[],
    weightField: string = "time_weight",
    sortByWeight: boolean = true,
  ): Record<string, unknown>[] {
    const now = new Date();
    for (const mem of memories) {
      const ts = (mem.timestamp as string) ?? "";
      mem[weightField] = this.calculate(ts, now);
    }

    if (sortByWeight) {
      memories.sort(
        (a, b) => ((b[weightField] as number) ?? 0) - ((a[weightField] as number) ?? 0),
      );
    }

    return memories;
  }

  /**
   * Suggest a time range based on query analysis.
   *
   * @param query - Search query
   * @returns Time range string (e.g. "7d", "30d", "90d") or null
   */
  getBestTimeRange(query: string): string | null {
    const lower = query.toLowerCase();

    // Parse explicit time range in query
    const match = lower.match(
      /((?:last|past|recent|近| most 近)\s*(\d+)\s*(?:day|week|month|year|天|周|月|年))/,
    );
    if (match) {
      return match[0];
    }

    // Heuristic time ranges
    if (["today", "今天", "now", "现 in "].some((kw) => lower.includes(kw))) {
      return "1d";
    }
    if (["recent", "this week", " most 近", "本周"].some((kw) => lower.includes(kw))) {
      return "7d";
    }
    if (["this month", " this 个月"].some((kw) => lower.includes(kw))) {
      return "30d";
    }

    return null;
  }

  /**
   * Calculate age in days from a timestamp string.
   */
  private _ageDays(timestamp: string, now?: Date): number {
    const ref = now ?? new Date();

    let ts: Date;
    try {
      ts = new Date(timestamp);
      if (isNaN(ts.getTime())) {
        // Try date-only format
        const parts = timestamp.slice(0, 10).split("-");
        if (parts.length === 3) {
          ts = new Date(`${parts[0]}-${parts[1]}-${parts[2]}T00:00:00Z`);
          if (isNaN(ts.getTime())) return this.config.maxAgeDays;
        } else {
          return this.config.maxAgeDays;
        }
      }
    } catch {
      return this.config.maxAgeDays;
    }

    const diffMs = ref.getTime() - ts.getTime();
    return Math.max(0, diffMs / 86400000); // Convert ms to days
  }

  /**
   * Step decay weight based on age thresholds.
   */
  private _stepWeight(ageDays: number): number {
    if (ageDays <= this.config.recentWindowDays) {
      return this.config.baseWeight;
    } else if (ageDays <= this.config.olderWindowDays) {
      return Math.max(this.config.minWeight, this.config.baseWeight * 0.5);
    } else {
      return this.config.minWeight;
    }
  }
}
