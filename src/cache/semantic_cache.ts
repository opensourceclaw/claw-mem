// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Semantic Approximate Cache (TS)
 *
 * Features:
 * - Keyword-based approximate matching using Jaccard similarity
 * - Configurable similarity threshold
 * - Access-count-based eviction
 * - No TTL (managed by MultiLevelCache)
 */

import type { SemanticCacheEntry } from "./types.js";

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

export class SemanticCache {
  private entries: SemanticCacheEntry[];
  private maxSize: number;
  private similarityThreshold: number;
  private hits: number;
  private misses: number;

  constructor(
    maxSize: number = 500,
    similarityThreshold: number = 0.8,
  ) {
    this.entries = [];
    this.maxSize = maxSize;
    this.similarityThreshold = similarityThreshold;
    this.hits = 0;
    this.misses = 0;
  }

  /** Find the best approximate match for a query. */
  find(query: string): { results: unknown[]; matchedQuery: string } | undefined {
    if (!query || query.trim().length === 0) {
      this.misses++;
      return undefined;
    }

    const keywords = this.extractKeywords(query);
    if (keywords.length === 0) {
      this.misses++;
      return undefined;
    }

    let bestMatch: { entry: SemanticCacheEntry; similarity: number } | undefined;

    for (const entry of this.entries) {
      const similarity = this.calcSimilarity(keywords, entry.keywords);
      if (similarity >= this.similarityThreshold && (!bestMatch || similarity > bestMatch.similarity)) {
        bestMatch = { entry, similarity };
      }
    }

    if (bestMatch) {
      bestMatch.entry.accessCount++;
      this.hits++;
      return {
        results: bestMatch.entry.results,
        matchedQuery: bestMatch.entry.query,
      };
    }

    this.misses++;
    return undefined;
  }

  /** Store a query-result pair in the semantic cache. */
  store(query: string, results: unknown[]): void {
    if (!query || query.trim().length === 0) return;

    const keywords = this.extractKeywords(query);
    const normalized = this.normalize(query);

    // Check if already exists (by normalized form)
    const existing = this.entries.find((e) => e.normalized === normalized);
    if (existing) {
      existing.results = results;
      existing.timestamp = Date.now();
      existing.accessCount++;
      return;
    }

    // Evict if at capacity
    if (this.entries.length >= this.maxSize) {
      this.evictLowestAccess();
    }

    this.entries.push({
      query,
      normalized,
      keywords,
      results,
      timestamp: Date.now(),
      accessCount: 1,
    });
  }

  /** Compute Jaccard similarity between two keyword sets. */
  private calcSimilarity(keywordsA: string[], keywordsB: string[]): number {
    const setA = new Set(keywordsA);
    const setB = new Set(keywordsB);
    let intersection = 0;
    for (const item of setA) {
      if (setB.has(item)) intersection++;
    }
    const union = new Set([...setA, ...setB]).size;
    return union === 0 ? 0 : intersection / union;
  }

  /** Normalize query. */
  private normalize(query: string): string {
    return query
      .toLowerCase()
      .replace(/[^\p{L}\p{N}\s]/gu, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  /** Extract keywords from query. */
  private extractKeywords(query: string): string[] {
    const normalized = this.normalize(query);
    const tokens = normalized.split(/\s+/).filter((t) => t.length > 0);
    const filtered = tokens.filter(
      (t) => t.length >= 2 && !STOP_WORDS.has(t),
    );
    return [...new Set(filtered)];
  }

  /** Evict the entry with the lowest access count. */
  private evictLowestAccess(): void {
    let minIndex = 0;
    let minAccess = this.entries[0]?.accessCount ?? 0;

    for (let i = 1; i < this.entries.length; i++) {
      if (this.entries[i].accessCount < minAccess) {
        minAccess = this.entries[i].accessCount;
        minIndex = i;
      }
    }

    this.entries.splice(minIndex, 1);
  }

  /** Clean up all entries (reset). */
  cleanup(): void {
    this.entries = [];
  }

  /** Remove a specific query from the cache. */
  remove(query: string): void {
    if (!query) return;
    const normalized = this.normalize(query);
    const idx = this.entries.findIndex((e) => e.normalized === normalized);
    if (idx >= 0) this.entries.splice(idx, 1);
  }

  /** Get cache statistics. */
  getStats(): Record<string, unknown> {
    const total = this.hits + this.misses;
    const hitRate = total > 0 ? (this.hits / total) * 100 : 0;

    return {
      size: this.entries.length,
      maxSize: this.maxSize,
      hits: this.hits,
      misses: this.misses,
      hitRate: Math.round(hitRate * 100) / 100,
      similarityThreshold: this.similarityThreshold,
    };
  }

  /** Get internal entries (for testing). */
  getEntries(): SemanticCacheEntry[] {
    return [...this.entries];
  }
}
