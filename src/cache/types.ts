// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Cache Type Definitions (TS)
 */

/** Cache entry for exact-match cache (L1). */
export interface CacheEntry {
  results: unknown[];
  timestamp: number;
  accessCount: number;
}

/** Cache entry for semantic approximate cache (L2). */
export interface SemanticCacheEntry {
  query: string;
  normalized: string;
  keywords: string[];
  results: unknown[];
  timestamp: number;
  accessCount: number;
}

/** Intelligent cache key with normalized query and keywords. */
export interface CacheKey {
  query: string;
  normalized: string;
  keywords: string[];
}

/** Cache statistics for all three levels. */
export interface CacheStats {
  l1: {
    size: number;
    maxSize: number;
    hits: number;
    misses: number;
    hitRate: number;
    ttlSeconds: number;
  };
  l2: {
    size: number;
    maxSize: number;
    hits: number;
    misses: number;
    hitRate: number;
  };
  l3: {
    size: number;
    maxSize: number;
    hits: number;
    misses: number;
    hitRate: number;
  };
  overall: {
    hits: number;
    misses: number;
    hitRate: number;
  };
}

/** Cache configuration. */
export interface CacheConfig {
  enableL1: boolean;
  l1MaxSize: number;
  l1TtlSeconds: number;

  enableL2: boolean;
  l2MaxSize: number;
  l2SimilarityThreshold: number;

  enableL3: boolean;
  l3MaxSize: number;
}

/** Cache events for monitoring and debugging. */
export type CacheEvent =
  | { type: 'l1_hit'; query: string; latencyMs: number }
  | { type: 'l2_hit'; query: string; matchedQuery: string; latencyMs: number }
  | { type: 'l3_hit'; query: string; matchedQuery: string; latencyMs: number }
  | { type: 'miss'; query: string }
  | { type: 'set'; query: string; level: 'l1' | 'l2' | 'l3' }
  | { type: 'evict'; query: string; level: 'l1' | 'l2' | 'l3'; reason: string };

/** Default cache configuration. */
export const DEFAULT_CACHE_CONFIG: CacheConfig = {
  enableL1: true,
  l1MaxSize: 1000,
  l1TtlSeconds: 86400,

  enableL2: true,
  l2MaxSize: 500,
  l2SimilarityThreshold: 0.8,

  enableL3: true,
  l3MaxSize: 2000,
};
