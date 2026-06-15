// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Optimized Query Cache (TS)
 *
 * Features:
 * - Smart key generation (normalized + keywords)
 * - 86400s TTL (configurable)
 * - Exact match via normalized query
 * - Approximate match via Jaccard keyword similarity
 * - LRU eviction
 */

import type { CacheEntry, CacheKey } from "./types.js";

const STOP_WORDS = new Set([
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

export class QueryCache {
  private maxSize: number;
  private ttlSeconds: number;
  private minAccessCount: number;
  private cache: Map<string, CacheEntry>;
  private keyMap: Map<string, string>; // normalized → cache key
  private hits: number;
  private misses: number;

  constructor(
    maxSize: number = 1000,
    ttlSeconds: number = 86400,
    minAccessCount: number = 2,
  ) {
    this.maxSize = maxSize;
    this.ttlSeconds = ttlSeconds;
    this.minAccessCount = minAccessCount;
    this.cache = new Map();
    this.keyMap = new Map();
    this.hits = 0;
    this.misses = 0;
  }

  /** Generate smart cache key from query. */
  makeKey(query: string, _topK?: number): CacheKey {
    const normalized = this.normalize(query);
    const keywords = this.extractKeywords(query);
    return { query, normalized, keywords };
  }

  /** Normalize query: lowercase, strip punctuation, collapse whitespace. */
  private normalize(query: string): string {
    return query
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  /** Extract keywords from query: normalize, tokenize, filter stop words and short tokens, deduplicate. */
  extractKeywords(query: string): string[] {
    const normalized = this.normalize(query);
    const tokens = normalized.split(/\s+/).filter((t) => t.length > 0);
    const filtered = tokens.filter(
      (t) => t.length >= 2 && !STOP_WORDS.has(t),
    );
    return [...new Set(filtered)];
  }

  /**
   * Get cached results for a query.
   * First tries exact match on normalized query, then falls through.
   */
  get(query: string, topK?: number): unknown[] | undefined {
    if (!query || query.trim().length === 0) {
      this.misses++;
      return undefined;
    }

    const key = this.makeKey(query, topK);

    // Try exact match via keyMap (normalized → cacheKey)
    const cacheKey = this.keyMap.get(key.normalized);
    if (cacheKey !== undefined) {
      const entry = this.cache.get(cacheKey);
      if (entry && !this.isExpired(entry)) {
        // LRU: delete and re-insert
        this.cache.delete(cacheKey);
        this.cache.set(cacheKey, entry);
        entry.accessCount++;
        this.hits++;
        return entry.results;
      }
      // Expired entry
      if (entry) {
        this.cache.delete(cacheKey);
        this.keyMap.delete(key.normalized);
      }
    }

    this.misses++;
    return undefined;
  }

  /** Exact match lookup (internal, for multi-level cache). */
  exactMatch(key: CacheKey): unknown[] | undefined {
    if (!key || !key.normalized) return undefined;

    const cacheKey = this.keyMap.get(key.normalized);
    if (cacheKey !== undefined) {
      const entry = this.cache.get(cacheKey);
      if (entry && !this.isExpired(entry)) {
        this.cache.delete(cacheKey);
        this.cache.set(cacheKey, entry);
        entry.accessCount++;
        this.hits++;
        return entry.results;
      }
      if (entry) {
        this.cache.delete(cacheKey);
        this.keyMap.delete(key.normalized);
      }
    }
    return undefined;
  }

  /**
   * Keyword approximate match using Jaccard similarity.
   * Returns the best match above threshold, if any.
   */
  keywordMatch(
    key: CacheKey,
    threshold: number,
  ): { results: unknown[]; matchedQuery: string } | undefined {
    if (!key || key.keywords.length === 0) return undefined;

    let bestMatch: { results: unknown[]; matchedQuery: string; similarity: number } | undefined;

    for (const [ck, entry] of this.cache.entries()) {
      if (this.isExpired(entry)) {
        // Clean up expired entries during scan
        this.cache.delete(ck);
        const normKey = this.findKeyByCacheKey(ck);
        if (normKey) this.keyMap.delete(normKey);
        continue;
      }

      // Reconstruct keywords from the stored entry
      // We need to get the original CacheKey for this entry
      // Since we store by cacheKey string, we reconstruct from the stored normalized
      const storedNorm = this.findKeyByCacheKey(ck);
      if (!storedNorm) continue;

      const storedKeywords = this.extractKeywords(storedNorm);
      const similarity = this.jaccardSimilarity(key.keywords, storedKeywords);

      if (similarity >= threshold && (!bestMatch || similarity > bestMatch.similarity)) {
        bestMatch = {
          results: entry.results,
          matchedQuery: storedNorm,
          similarity,
        };
      }
    }

    if (bestMatch) {
      this.hits++;
      return { results: bestMatch.results, matchedQuery: bestMatch.matchedQuery };
    }

    return undefined;
  }

  /** Compute Jaccard similarity between two keyword sets. */
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

  /** Find the normalized key that maps to a given cache key string. */
  private findKeyByCacheKey(cacheKey: string): string | undefined {
    for (const [norm, ck] of this.keyMap.entries()) {
      if (ck === cacheKey) return norm;
    }
    return undefined;
  }

  /** Check if an entry is expired. */
  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > this.ttlSeconds * 1000;
  }

  /** Store results in cache. */
  put(query: string, results: unknown[], topK?: number): void {
    if (!query || query.trim().length === 0) return;

    const key = this.makeKey(query, topK);
    const cacheKeyStr = key.normalized;

    // Update keyMap
    this.keyMap.set(key.normalized, cacheKeyStr);

    // If already exists, update in-place
    const existing = this.cache.get(cacheKeyStr);
    if (existing) {
      existing.results = results;
      existing.timestamp = Date.now();
      existing.accessCount++;
      // LRU touch
      this.cache.delete(cacheKeyStr);
      this.cache.set(cacheKeyStr, existing);
      return;
    }

    // Evict LRU if at capacity
    this.evictLRU();

    this.cache.set(cacheKeyStr, {
      results,
      timestamp: Date.now(),
      accessCount: 1,
    });
  }

  /** Evict least recently used entries until under maxSize. */
  private evictLRU(): void {
    while (this.cache.size >= this.maxSize) {
      const lruKey = this.cache.keys().next().value;
      if (lruKey === undefined) break;
      this.cache.delete(lruKey);
      // Clean up keyMap
      const normKey = this.findKeyByCacheKey(lruKey);
      if (normKey) this.keyMap.delete(normKey);
    }
  }

  /** Invalidate specific query or entire cache. */
  invalidate(query?: string): void {
    if (query === undefined) {
      this.cache.clear();
      this.keyMap.clear();
    } else {
      const key = this.makeKey(query);
      const cacheKeyStr = this.keyMap.get(key.normalized);
      if (cacheKeyStr) {
        this.cache.delete(cacheKeyStr);
        this.keyMap.delete(key.normalized);
      }
    }
  }

  /** Remove all expired entries. */
  cleanupExpired(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttlSeconds * 1000) {
        this.cache.delete(key);
        const normKey = this.findKeyByCacheKey(key);
        if (normKey) this.keyMap.delete(normKey);
      }
    }
  }

  /** Get cache statistics. */
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

  /** Get internal entries (for L3 serialization / testing). */
  getEntries(): Array<[string, CacheEntry]> {
    return [...this.cache.entries()];
  }
}
