// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.40.0 — MemoryGovernance
 *
 * Self-organizing memory decisions:
 * 1. SELECT: Should this memory be stored?
 * 2. MAINTAIN: Should this memory be kept/refreshed/forget?
 */

/**
 * Configuration for MemoryGovernance.
 */
export interface MemoryGovernanceConfig {
  /** Minimum importance to store (default: 0.3) */
  importanceThreshold: number;
  /** Minimum relevance to store (default: 0.2) */
  relevanceThreshold: number;
  /** Maximum age before forget (days, default: 30) */
  maxAge: number;
  /** Minimum access count to keep (default: 1) */
  minAccessCount: number;
  /** Access count threshold for refresh (default: 5) */
  refreshThreshold: number;
}

/**
 * Default configuration values.
 */
export const DEFAULT_GOVERNANCE_CONFIG: MemoryGovernanceConfig = {
  importanceThreshold: 0.3,
  relevanceThreshold: 0.2,
  maxAge: 30,
  minAccessCount: 1,
  refreshThreshold: 5,
};

/**
 * Maintain decision result.
 */
export type MaintainDecision = "keep" | "refresh" | "forget";

/**
 * Metrics tracking for governance decisions.
 */
export interface GovernanceMetrics {
  totalDecisions: number;
  stored: number;
  rejected: number;
  kept: number;
  refreshed: number;
  forgotten: number;
}

/**
 * MemoryGovernance — Self-organizing memory decisions.
 *
 * @example
 * ```typescript
 * const governance = new MemoryGovernance();
 *
 * // SELECT: Should we store this memory?
 * if (governance.select(0.8, 0.5)) {
 *   memoryManager.store(content);
 * }
 *
 * // MAINTAIN: What to do with existing memory?
 * const decision = governance.maintain(ageInDays, accessCount);
 * // decision: 'keep' | 'refresh' | 'forget'
 * ```
 */
export class MemoryGovernance {
  private config: MemoryGovernanceConfig;
  private metrics: GovernanceMetrics;

  constructor(config?: Partial<MemoryGovernanceConfig>) {
    this.config = { ...DEFAULT_GOVERNANCE_CONFIG, ...config };
    this.metrics = {
      totalDecisions: 0,
      stored: 0,
      rejected: 0,
      kept: 0,
      refreshed: 0,
      forgotten: 0,
    };
  }

  /**
   * SELECT: Decide whether to store a memory.
   *
   * @param importance - Intrinsic importance of the memory (0-1)
   * @param relevance - Relevance to current context (0-1)
   * @returns true if the memory should be stored
   */
  select(importance: number, relevance: number): boolean {
    this.metrics.totalDecisions++;

    // Weighted combination: importance weighted higher
    const score = importance * 0.6 + relevance * 0.4;
    const shouldStore = score >= this.config.importanceThreshold;

    if (shouldStore) {
      this.metrics.stored++;
    } else {
      this.metrics.rejected++;
    }

    return shouldStore;
  }

  /**
   * MAINTAIN: Decide what to do with existing memory.
   *
   * @param age - Age of the memory in days
   * @param accessCount - Number of times the memory has been accessed
   * @returns Decision: 'keep' | 'refresh' | 'forget'
   */
  maintain(age: number, accessCount: number): MaintainDecision {
    this.metrics.totalDecisions++;

    // Too old and not accessed → forget
    if (age > this.config.maxAge && accessCount < this.config.minAccessCount) {
      this.metrics.forgotten++;
      return "forget";
    }

    // High access count → refresh (boost importance)
    if (accessCount >= this.config.refreshThreshold) {
      this.metrics.refreshed++;
      return "refresh";
    }

    // Default → keep
    this.metrics.kept++;
    return "keep";
  }

  /**
   * Get governance metrics.
   */
  getMetrics(): GovernanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Reset metrics to zero.
   */
  resetMetrics(): void {
    this.metrics = {
      totalDecisions: 0,
      stored: 0,
      rejected: 0,
      kept: 0,
      refreshed: 0,
      forgotten: 0,
    };
  }

  /**
   * Update configuration.
   */
  updateConfig(config: Partial<MemoryGovernanceConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Get current configuration.
   */
  getConfig(): MemoryGovernanceConfig {
    return { ...this.config };
  }
}
