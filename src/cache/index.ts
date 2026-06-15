// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — CacheManager Facade (TS)
 *
 * Public facade over MultiLevelCache. Main entry point for cache operations.
 */

import { MultiLevelCache } from "./multi_level_cache.js";
import type { CacheConfig, CacheEvent, CacheStats } from "./types.js";

export class CacheManager {
  private multiLevelCache: MultiLevelCache;

  constructor(config?: Partial<CacheConfig>) {
    this.multiLevelCache = new MultiLevelCache(config);
  }

  /** Get cached results. */
  get(query: string, topK?: number): unknown[] | undefined {
    return this.multiLevelCache.get(query, topK);
  }

  /** Store results in cache. */
  set(query: string, results: unknown[], topK?: number): void {
    this.multiLevelCache.set(query, results, topK);
  }

  /** Invalidate cache entries. */
  invalidate(query?: string): void {
    this.multiLevelCache.invalidate(query);
  }

  /** Clean up all caches. */
  cleanup(): void {
    this.multiLevelCache.cleanup();
  }

  /** Get cache statistics. */
  getStats(): CacheStats {
    return this.multiLevelCache.getStats();
  }

  /** Subscribe to cache events. */
  onEvent(listener: (event: CacheEvent) => void): void {
    this.multiLevelCache.onEvent(listener);
  }

  /** Reset all caches and statistics. */
  reset(): void {
    this.multiLevelCache.reset();
  }
}

// Re-exports
export { QueryCache } from "./query_cache.js";
export { SemanticCache } from "./semantic_cache.js";
export { MultiLevelCache } from "./multi_level_cache.js";
export type {
  CacheEntry,
  SemanticCacheEntry,
  CacheKey,
  CacheStats,
  CacheConfig,
  CacheEvent,
} from "./types.js";
