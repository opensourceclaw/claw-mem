// claw-mem v6.29.0 — Structured Filter (TypeScript)
//
// Provides in-memory filtering by tags, type, sessionId, and timeRange.
// Applied after semantic/keyword retrieval for deterministic filtering.
//
// Licensed under the Apache License, Version 2.0

import type { RetrievalResult } from "./base.js";

/**
 * Filter criteria for structured filtering.
 */
export interface FilterCriteria {
  /** Filter by tags (AND logic: result must have all specified tags) */
  tags?: string[];
  /** Filter by memory type: 'episodic' | 'semantic' | 'procedural' */
  type?: string;
  /** Filter by session ID */
  sessionId?: string;
  /** Filter by time range */
  timeRange?: {
    start?: string;  // ISO 8601
    end?: string;    // ISO 8601
  };
  /** Custom filter function */
  custom?: (result: RetrievalResult) => boolean;
}

/**
 * StructuredFilter — applies deterministic filters to retrieval results.
 *
 * Uses in-memory scanning, no index required.
 * Filters are applied in order: tags → type → sessionId → timeRange → custom.
 */
export class StructuredFilter {
  /**
   * Apply structured filters to retrieval results.
   *
   * @param results - Retrieval results to filter
   * @param criteria - Filter criteria
   * @returns Filtered results
   */
  apply(results: RetrievalResult[], criteria?: FilterCriteria): RetrievalResult[] {
    if (!criteria) return results;

    return results.filter((result) => {
      // 1. Tags filter (AND logic)
      if (criteria.tags && criteria.tags.length > 0) {
        if (!this.matchTags(result, criteria.tags)) return false;
      }

      // 2. Type filter
      if (criteria.type && result.memory_type !== criteria.type) {
        return false;
      }

      // 3. Session ID filter
      if (criteria.sessionId && result.metadata?.session_id !== criteria.sessionId) {
        return false;
      }

      // 4. Time range filter
      if (criteria.timeRange) {
        if (!this.matchTimeRange(result, criteria.timeRange)) return false;
      }

      // 5. Custom filter
      if (criteria.custom) {
        try {
          if (!criteria.custom(result)) return false;
        } catch {
          // Custom filter threw an error, exclude this result
          return false;
        }
      }

      return true;
    });
  }

  /**
   * Check if result has all required tags (AND logic).
   */
  private matchTags(result: RetrievalResult, requiredTags: string[]): boolean {
    const resultTags = new Set(result.tags ?? []);
    return requiredTags.every((tag) => resultTags.has(tag));
  }

  /**
   * Check if result is within time range.
   */
  private matchTimeRange(
    result: RetrievalResult,
    range: { start?: string; end?: string },
  ): boolean {
    const timestamp = result.timestamp;
    if (!timestamp) return true; // No timestamp = pass through

    const ts = new Date(timestamp).getTime();
    if (isNaN(ts)) return true; // Invalid timestamp = pass through

    if (range.start) {
      const start = new Date(range.start).getTime();
      if (!isNaN(start) && ts < start) return false;
    }

    if (range.end) {
      const end = new Date(range.end).getTime();
      if (!isNaN(end) && ts > end) return false;
    }

    return true;
  }
}
