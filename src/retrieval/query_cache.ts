// claw-mem v5.0.0 — LRU Query Cache (TypeScript)
//
// LRU cache with TTL for search results.
// Pure TypeScript implementation with no external dependencies.
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

import { createHash } from "crypto";

/** A single cache entry with metadata. */
interface CacheEntry {
  results: unknown[];
  timestamp: number;
  accessCount: number;
}

/**
 * LRU Cache with TTL for query results.
 *
 * Features:
 * - LRU eviction when max size is reached
 * - TTL expiration
 * - Access frequency tracking
 * - MD5-based cache keys
 */
export class QueryCache {
  private maxSize: number;
  private ttlSeconds: number;
  private minAccessCount: number;
  private cache: Map<string, CacheEntry> = new Map();
  private hits: number = 0;
  private misses: number = 0;

  constructor(maxSize: number = 1000, ttlSeconds: number = 300, minAccessCount: number = 2) {
    this.maxSize = maxSize;
    this.ttlSeconds = ttlSeconds;
    this.minAccessCount = minAccessCount;
  }

  /**
   * Generate a cache key from query and top_k.
   */
  private makeKey(query: string, topK: number = 10): string {
    const keyData = `${query.toLowerCase().trim()}:${topK}`;
    return createHash("md5").update(keyData).digest("hex");
  }

  /**
   * Get cached results for a query.
   *
   * @param query - Search query.
   * @param topK - Number of results.
   * @returns Cached results array, or undefined if cache miss / expired.
   */
  get(query: string, topK: number = 10): unknown[] | undefined {
    const key = this.makeKey(query, topK);
    const entry = this.cache.get(key);

    if (!entry) {
      this.misses++;
      return undefined;
    }

    // Check TTL
    if (Date.now() - entry.timestamp > this.ttlSeconds * 1000) {
      this.cache.delete(key);
      this.misses++;
      return undefined;
    }

    // LRU: delete and re-insert to move to end (most recently used)
    this.cache.delete(key);
    this.cache.set(key, entry);
    entry.accessCount++;

    this.hits++;
    return entry.results;
  }

  /**
   * Cache results for a query.
   *
   * @param query - Search query.
   * @param results - Search results to cache.
   * @param topK - Number of results.
   */
  put(query: string, results: unknown[], topK: number = 10): void {
    const key = this.makeKey(query, topK);

    // Evict LRU entries if at capacity
    while (this.cache.size >= this.maxSize) {
      const lruKey = this.cache.keys().next().value;
      if (lruKey !== undefined) {
        this.cache.delete(lruKey);
      } else {
        break;
      }
    }

    this.cache.set(key, {
      results,
      timestamp: Date.now(),
      accessCount: 1,
    });
  }

  /**
   * Invalidate cache entries.
   *
   * @param query - Specific query to invalidate, or undefined for all.
   */
  invalidate(query?: string): void {
    if (query === undefined) {
      this.cache.clear();
    } else {
      const key = this.makeKey(query);
      this.cache.delete(key);
    }
  }

  /**
   * Remove all expired entries.
   */
  cleanupExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttlSeconds * 1000) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Get cache statistics.
   */
  getStats(): Record<string, unknown> {
    const total = this.hits + this.misses;
    const hitRate = total > 0 ? (this.hits / total) * 100 : 0;

    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      hits: this.hits,
      misses: this.misses,
      hitRate: Math.round(hitRate * 100) / 100,
      ttlSeconds: this.ttlSeconds,
    };
  }

  /**
   * Clear all cache entries.
   * v6.36.0: Session-level cache management.
   */
  clear(): void {
    this.cache.clear();
    this.hits = 0;
    this.misses = 0;
  }
}

// Global cache instance (deprecated, use createQueryCache for session-level)
let globalCache: QueryCache | undefined;

/**
 * Get or create the global QueryCache singleton.
 * v6.36.0: Deprecated - use createQueryCache() for session-level cache.
 * @deprecated Use createQueryCache() for better memory management
 */
export function getQueryCache(maxSize: number = 1000, ttlSeconds: number = 300): QueryCache {
  if (!globalCache) {
    globalCache = new QueryCache(maxSize, ttlSeconds);
  }
  return globalCache;
}

/**
 * Create a new session-level QueryCache instance.
 * v6.36.0: Preferred way to create cache - avoids global singleton memory leak.
 */
export function createQueryCache(maxSize: number = 1000, ttlSeconds: number = 300): QueryCache {
  return new QueryCache(maxSize, ttlSeconds);
}

/**
 * Reset the global query cache instance (for testing).
 */
export function resetQueryCache(): void {
  globalCache = undefined;
}

/**
 * Clear the global query cache.
 * v6.36.0: Memory leak prevention - call on session end.
 */
export function clearGlobalQueryCache(): void {
  if (globalCache) {
    globalCache.clear();
  }
}
