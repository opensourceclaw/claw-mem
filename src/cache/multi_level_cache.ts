// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Multi-Level Cache Manager (TS)
 *
 * Three-tier cache architecture:
 *   L1: Exact match (QueryCache) — fastest, strictest
 *   L2: Semantic approximate (SemanticCache) — keyword-based Jaccard similarity
 *   L3: History query — fallback, keyword similarity over larger pool
 *
 * Query flow: L1 → L2 → L3, with promote on hit.
 * Event system for monitoring and debugging.
 */

import { QueryCache } from "./query_cache.js";
import { SemanticCache } from "./semantic_cache.js";
import type { CacheConfig, CacheEntry, CacheEvent, CacheStats, CacheKey } from "./types.js";
import { DEFAULT_CACHE_CONFIG } from "./types.js";

export class MultiLevelCache {
  private l1Cache: QueryCache;
  private l2Cache: SemanticCache;
  private l3Entries: Map<string, CacheEntry>;
  private l3KeyMap: Map<string, string>; // normalized → key
  private config: CacheConfig;
  private eventListeners: Array<(event: CacheEvent) => void>;
  private l1Hits: number;
  private l1Misses: number;
  private l2Hits: number;
  private l2Misses: number;
  private l3Hits: number;
  private l3Misses: number;

  constructor(config?: Partial<CacheConfig>) {
    this.config = { ...DEFAULT_CACHE_CONFIG, ...config };
    this.l1Cache = new QueryCache(
      this.config.l1MaxSize,
      this.config.l1TtlSeconds,
    );
    this.l2Cache = new SemanticCache(
      this.config.l2MaxSize,
      this.config.l2SimilarityThreshold,
    );
    this.l3Entries = new Map();
    this.l3KeyMap = new Map();
    this.eventListeners = [];
    this.l1Hits = 0;
    this.l1Misses = 0;
    this.l2Hits = 0;
    this.l2Misses = 0;
    this.l3Hits = 0;
    this.l3Misses = 0;
  }

  /** Get cached results through multi-level cascade. */
  get(query: string, topK?: number): unknown[] | undefined {
    if (!query || query.trim().length === 0) {
      this.emitEvent({ type: "miss", query });
      return undefined;
    }

    // L1: Exact match
    if (this.config.enableL1) {
      const start = Date.now();
      const l1Key = this.l1Cache.makeKey(query, topK);
      const l1Result = this.l1Cache.exactMatch(l1Key);
      const latency = Date.now() - start;

      if (l1Result !== undefined) {
        this.l1Hits++;
        this.emitEvent({ type: "l1_hit", query, latencyMs: latency });
        return l1Result;
      }
      this.l1Misses++;
    }

    // L2: Semantic approximate
    if (this.config.enableL2) {
      const start = Date.now();
      const l2Result = this.l2Cache.find(query);
      const latency = Date.now() - start;

      if (l2Result !== undefined) {
        this.l2Hits++;
        this.emitEvent({ type: "l2_hit", query, matchedQuery: l2Result.matchedQuery, latencyMs: latency });
        // Promote to L1
        if (this.config.enableL1) {
          this.l1Cache.put(query, l2Result.results, topK);
        }
        return l2Result.results;
      }
      this.l2Misses++;
    }

    // L3: History query
    if (this.config.enableL3) {
      const start = Date.now();
      const l3Result = this.queryL3(query);
      const latency = Date.now() - start;

      if (l3Result !== undefined) {
        this.l3Hits++;
        this.emitEvent({ type: "l3_hit", query, matchedQuery: l3Result.matchedQuery, latencyMs: latency });
        // Promote to L1 and L2
        if (this.config.enableL1) {
          this.l1Cache.put(query, l3Result.results, topK);
        }
        if (this.config.enableL2) {
          this.l2Cache.store(query, l3Result.results);
        }
        return l3Result.results;
      }
      this.l3Misses++;
    }

    // Complete miss
    this.emitEvent({ type: "miss", query });
    return undefined;
  }

  /** Store results in all active cache levels. */
  set(query: string, results: unknown[], topK?: number): void {
    if (!query || query.trim().length === 0) return;

    if (this.config.enableL1) {
      this.l1Cache.put(query, results, topK);
      this.emitEvent({ type: "set", query, level: "l1" });
    }

    if (this.config.enableL2) {
      this.l2Cache.store(query, results);
      this.emitEvent({ type: "set", query, level: "l2" });
    }

    if (this.config.enableL3) {
      this.storeL3(query, results);
      this.emitEvent({ type: "set", query, level: "l3" });
    }
  }

  /** Query L3 history by keyword similarity. */
  private queryL3(
    query: string,
  ): { results: unknown[]; matchedQuery: string } | undefined {
    const key = this.makeL3Key(query);
    if (key.keywords.length === 0) return undefined;

    let bestMatch: { results: unknown[]; matchedQuery: string; similarity: number } | undefined;

    for (const [ck, entry] of this.l3Entries.entries()) {
      const storedNorm = this.l3KeyMap.get(ck);
      if (!storedNorm) continue;

      const storedKeywords = this.extractL3Keywords(storedNorm);
      const similarity = this.jaccardSimilarity(key.keywords, storedKeywords);

      if (similarity >= this.config.l2SimilarityThreshold && (!bestMatch || similarity > bestMatch.similarity)) {
        bestMatch = {
          results: entry.results,
          matchedQuery: storedNorm,
          similarity,
        };
      }
    }

    if (bestMatch) {
      return { results: bestMatch.results, matchedQuery: bestMatch.matchedQuery };
    }
    return undefined;
  }

  /** Store entry in L3. */
  private storeL3(query: string, results: unknown[]): void {
    const key = this.makeL3Key(query);
    const cacheKeyStr = key.normalized;

    // Update or insert
    const existing = this.l3Entries.get(cacheKeyStr);
    if (existing) {
      existing.results = results;
      existing.timestamp = Date.now();
      existing.accessCount++;
      return;
    }

    // Evict if at capacity
    while (this.l3Entries.size >= this.config.l3MaxSize) {
      this.evictL3LRU();
    }

    this.l3KeyMap.set(key.normalized, cacheKeyStr);
    this.l3Entries.set(cacheKeyStr, {
      results,
      timestamp: Date.now(),
      accessCount: 1,
    });
  }

  /** Evict LRU entry from L3. */
  private evictL3LRU(): void {
    const lruKey = this.l3Entries.keys().next().value;
    if (lruKey === undefined) return;
    this.l3Entries.delete(lruKey);
    // Clean up keyMap
    const normKey = this.findL3KeyByCacheKey(lruKey);
    if (normKey) this.l3KeyMap.delete(normKey);
    this.emitEvent({ type: "evict", query: lruKey, level: "l3", reason: "lru" });
  }

  /** Make an L3 cache key (simplified version of QueryCache.makeKey). */
  private makeL3Key(query: string): { normalized: string; keywords: string[] } {
    const normalized = this.normalize(query);
    const keywords = this.extractL3Keywords(query);
    return { normalized, keywords };
  }

  /** Normalize query string. */
  private normalize(query: string): string {
    return query
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  /** Extract keywords (same logic as QueryCache for consistency). */
  private extractL3Keywords(query: string): string[] {
    const normalized = this.normalize(query);
    const tokens = normalized.split(/\s+/).filter((t) => t.length > 0);
    const stopWords = new Set([
      "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
      "have", "has", "had", "do", "does", "did", "will", "would", "could",
      "should", "may", "might", "shall", "can", "need", "dare", "ought",
      "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
      "as", "into", "through", "during", "before", "after", "above", "below",
      "between", "out", "off", "over", "under", "again", "further", "then",
      "once", "here", "there", "when", "where", "why", "how", "all", "each",
      "every", "both", "few", "more", "most", "other", "some", "such", "no",
      "nor", "not", "only", "own", "same", "so", "than", "too", "very",
      "just", "because", "but", "and", "or", "if", "while", "although",
      "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
      "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
      "没有", "看", "好", "自己", "这", "他", "她", "它", "们",
    ]);
    const filtered = tokens.filter(
      (t) => t.length >= 2 && !stopWords.has(t),
    );
    return [...new Set(filtered)];
  }

  /** Compute Jaccard similarity. */
  private jaccardSimilarity(a: string[], b: string[]): number {
    const setA = new Set(a);
    const setB = new Set(b);
    let intersection = 0;
    for (const item of setA) {
      if (setB.has(item)) intersection++;
    }
    const union = new Set([...setA, ...setB]).size;
    return union === 0 ? 0 : intersection / union;
  }

  /** Find normalized key by cache key string in L3. */
  private findL3KeyByCacheKey(cacheKey: string): string | undefined {
    for (const [norm, ck] of this.l3KeyMap.entries()) {
      if (ck === cacheKey) return norm;
    }
    return undefined;
  }

  /** Invalidate cache entries. */
  invalidate(query?: string): void {
    if (this.config.enableL1) {
      this.l1Cache.invalidate(query);
    }
    if (query === undefined) {
      if (this.config.enableL2) {
        this.l2Cache.cleanup();
      }
      this.l3Entries.clear();
      this.l3KeyMap.clear();
    } else {
      // Remove from L2 and L3 as well for complete invalidation
      if (this.config.enableL2) {
        this.l2Cache.remove(query);
      }
      if (this.config.enableL3) {
        const normalized = this.normalize(query);
        this.l3Entries.delete(normalized);
        this.l3KeyMap.delete(normalized);
      }
    }
  }

  /** Clear all caches. */
  cleanup(): void {
    if (this.config.enableL1) {
      this.l1Cache.invalidate();
    }
    if (this.config.enableL2) {
      this.l2Cache.cleanup();
    }
    this.l3Entries.clear();
    this.l3KeyMap.clear();
  }

  /** Reset all caches and statistics. */
  reset(): void {
    if (this.config.enableL1) {
      this.l1Cache.invalidate();
    }
    if (this.config.enableL2) {
      this.l2Cache.cleanup();
    }
    this.l3Entries.clear();
    this.l3KeyMap.clear();
    this.l1Hits = 0;
    this.l1Misses = 0;
    this.l2Hits = 0;
    this.l2Misses = 0;
    this.l3Hits = 0;
    this.l3Misses = 0;
  }

  /** Get cache statistics. */
  getStats(): CacheStats {
    const l1Stats = this.config.enableL1
      ? this.l1Cache.getStats()
      : { size: 0, maxSize: this.config.l1MaxSize, hits: 0, misses: 0, hitRate: 0, ttlSeconds: this.config.l1TtlSeconds };

    const l2Stats = this.config.enableL2
      ? this.l2Cache.getStats()
      : { size: 0, maxSize: this.config.l2MaxSize, hits: 0, misses: 0, hitRate: 0 };

    const l3Total = this.l3Hits + this.l3Misses;
    const l3HitRate = l3Total > 0 ? (this.l3Hits / l3Total) * 100 : 0;

    const overallHits = this.l1Hits + this.l2Hits + this.l3Hits;
    const overallMisses = this.l1Misses + this.l2Misses + this.l3Misses;
    const overallTotal = overallHits + overallMisses;
    const overallHitRate = overallTotal > 0 ? (overallHits / overallTotal) * 100 : 0;

    return {
      l1: {
        size: (l1Stats as Record<string, unknown>).size as number,
        maxSize: this.config.l1MaxSize,
        hits: this.l1Hits,
        misses: this.l1Misses,
        hitRate: Math.round((this.l1Hits / Math.max(this.l1Hits + this.l1Misses, 1)) * 10000) / 100,
        ttlSeconds: this.config.l1TtlSeconds,
      },
      l2: {
        size: (l2Stats as Record<string, unknown>).size as number,
        maxSize: this.config.l2MaxSize,
        hits: this.l2Hits,
        misses: this.l2Misses,
        hitRate: Math.round((this.l2Hits / Math.max(this.l2Hits + this.l2Misses, 1)) * 10000) / 100,
      },
      l3: {
        size: this.l3Entries.size,
        maxSize: this.config.l3MaxSize,
        hits: this.l3Hits,
        misses: this.l3Misses,
        hitRate: Math.round(l3HitRate * 100) / 100,
      },
      overall: {
        hits: overallHits,
        misses: overallMisses,
        hitRate: Math.round(overallHitRate * 100) / 100,
      },
    };
  }

  /** Subscribe to cache events. */
  onEvent(listener: (event: CacheEvent) => void): void {
    this.eventListeners.push(listener);
  }

  /** Emit a cache event to all listeners. */
  private emitEvent(event: CacheEvent): void {
    for (const listener of this.eventListeners) {
      try {
        listener(event);
      } catch {
        // Silently ignore listener errors
      }
    }
  }
}
