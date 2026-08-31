// claw-mem v6.29.0 — Hybrid Retriever (TypeScript)
//
// Combines semantic search, keyword search, structured filtering, and fusion reranking.
// Paper F8: balanced (50/50) > sparse-leaning (30/70) for fusion
// Paper F2: evidence completeness > first-hit accuracy
//
// Licensed under the Apache License, Version 2.0

import type { RetrievalResult, RetrievalDocument } from "./base.js";
import { KeywordRetriever } from "./keyword.js";
import { FusionReranker, type FusionConfig, DEFAULT_FUSION_CONFIG } from "./fusion-reranker.js";
import { StructuredFilter, type FilterCriteria } from "./structured-filter.js";
import { CompletenessScorer } from "./completeness-scorer.js";

/**
 * Options for hybrid search.
 */
export interface HybridSearchOptions {
  /** Maximum results to return (default: 10) */
  topK?: number;
  /** Minimum relevance score (default: 0.0) */
  minScore?: number;
  /** Structured filter criteria */
  filters?: FilterCriteria;
  /** Fusion configuration override */
  fusion?: Partial<FusionConfig>;
  /** Include completeness score in results (default: true) */
  includeCompleteness?: boolean;
}

/**
 * Hybrid search result with metadata.
 */
export interface HybridSearchResult {
  /** Ranked retrieval results */
  results: RetrievalResult[];
  /** Completeness score [0, 1] */
  completenessScore?: number;
  /** Search metadata */
  metadata: {
    semanticCount: number;
    keywordCount: number;
    afterFilterCount: number;
    latencyMs: number;
  };
}

/**
 * HybridRetriever — combines multiple retrieval strategies.
 *
 * Architecture:
 * 1. Parallel semantic + keyword search
 * 2. Merge and deduplicate
 * 3. Apply structured filters
 * 4. Fusion reranking
 * 5. Completeness scoring
 */
export class HybridRetriever {
  private keywordRetriever: KeywordRetriever;
  private fusionReranker: FusionReranker;
  private structuredFilter: StructuredFilter;
  private completenessScorer: CompletenessScorer;

  /** Callback to get semantic search results */
  private semanticSearchFn?: (query: string, limit: number) => RetrievalResult[];

  /** v7.5.0 (ADR-002): retention score provider (provided by MemoryManager) */
  private getRetentionScore?: (id: string) => number | undefined;

  /** v7.5.0: selection event sink (selected records / candidate-missed records) */
  private onEvents?: (selected: RetrievalResult[], missed: RetrievalResult[]) => void;

  constructor(options?: {
    fusion?: Partial<FusionConfig>;
    semanticSearchFn?: (query: string, limit: number) => RetrievalResult[];
    getRetentionScore?: (id: string) => number | undefined;
    onEvents?: (selected: RetrievalResult[], missed: RetrievalResult[]) => void;
  }) {
    this.keywordRetriever = new KeywordRetriever();
    this.fusionReranker = new FusionReranker(options?.fusion);
    this.structuredFilter = new StructuredFilter();
    this.completenessScorer = new CompletenessScorer();
    this.semanticSearchFn = options?.semanticSearchFn;
    this.getRetentionScore = options?.getRetentionScore;
    this.onEvents = options?.onEvents;
  }

  /**
   * Index documents for keyword retrieval.
   */
  index(documents: RetrievalDocument[]): void {
    this.keywordRetriever.index(documents);
  }

  /**
   * Add a single document to the index.
   */
  addDocument(id: string, text: string, metadata?: Record<string, unknown>): void {
    this.keywordRetriever.addDocument(id, text, metadata);
  }

  /**
   * Set semantic search callback.
   * The callback should return results sorted by relevance.
   */
  setSemanticSearchFn(fn: (query: string, limit: number) => RetrievalResult[]): void {
    this.semanticSearchFn = fn;
  }

  /**
   * Hybrid search: semantic + keyword + filter + rerank.
   *
   * @param query - Search query
   * @param options - Search options
   * @returns Hybrid search result with metadata
   */
  search(query: string, options?: HybridSearchOptions): HybridSearchResult {
    const startTime = Date.now();
    const topK = options?.topK ?? 10;
    const candidateMultiplier = 2;

    // 1. Parallel semantic + keyword search
    const candidateLimit = topK * candidateMultiplier;
    const semanticResults = this.semanticSearch(query, candidateLimit);
    const keywordResults = this.keywordSearch(query, candidateLimit);

    // 2. Merge and deduplicate by ID
    const merged = this.mergeAndDedupe(semanticResults, keywordResults);

    // 3. Apply structured filters
    const filtered = this.structuredFilter.apply(merged, options?.filters);

    // 4. v7.5.0 (ADR-002): carry retention scores on results for fusion
    const withRetention = this.getRetentionScore
      ? filtered.map((r) => {
          const retention = this.getRetentionScore!(r.id);
          return retention === undefined ? r : { ...r, retention };
        })
      : filtered;

    // 5. Fusion reranking (three-way: semantic + keyword + retention)
    const reranked = this.fusionReranker.rerank(withRetention, query, options?.fusion);

    // 6. Apply minScore filter
    const minScore = options?.minScore ?? 0;
    const scored = reranked.filter((r) => r.fusedScore >= minScore);

    // 7. v7.5.0: record selection events from the candidate pool
    // (mergeAndDedupe output = candidate pool; selected = topK actually returned)
    if (this.onEvents) {
      const selectedRecords = scored.slice(0, topK);
      const selectedIds = new Set(selectedRecords.map((r) => r.id));
      const missedRecords = filtered.filter((r) => !selectedIds.has(r.id));
      this.onEvents(selectedRecords, missedRecords);
    }

    // 8. Completeness scoring
    const completenessScore =
      options?.includeCompleteness !== false
        ? this.completenessScorer.score(scored.slice(0, topK), query)
        : undefined;

    // 9. Return topK
    const results = scored.slice(0, topK);

    return {
      results,
      completenessScore,
      metadata: {
        semanticCount: semanticResults.length,
        keywordCount: keywordResults.length,
        afterFilterCount: filtered.length,
        latencyMs: Date.now() - startTime,
      },
    };
  }

  /**
   * Perform semantic search via callback.
   */
  private semanticSearch(query: string, limit: number): RetrievalResult[] {
    if (!this.semanticSearchFn) return [];
    try {
      return this.semanticSearchFn(query, limit);
    } catch {
      return [];
    }
  }

  /**
   * Perform keyword search via KeywordRetriever.
   */
  private keywordSearch(query: string, limit: number): RetrievalResult[] {
    return this.keywordRetriever.search(query, limit);
  }

  /**
   * Merge and deduplicate results by ID.
   * Keeps the result with higher score when duplicates are found.
   */
  private mergeAndDedupe(
    semantic: RetrievalResult[],
    keyword: RetrievalResult[],
  ): RetrievalResult[] {
    const byId = new Map<string, RetrievalResult>();

    // Add semantic results
    for (const r of semantic) {
      const existing = byId.get(r.id);
      if (!existing || (r.score ?? 0) > (existing.score ?? 0)) {
        byId.set(r.id, r);
      }
    }

    // Add keyword results (may update existing if score is higher)
    for (const r of keyword) {
      const existing = byId.get(r.id);
      if (!existing) {
        byId.set(r.id, r);
      } else if ((r.score ?? 0) > (existing.score ?? 0)) {
        // Update score but preserve semantic source info
        byId.set(r.id, {
          ...existing,
          score: r.score,
          source: "hybrid", // Mark as hybrid source
        });
      }
    }

    return [...byId.values()];
  }

  /**
   * Clear all indexed documents.
   */
  clear(): void {
    this.keywordRetriever.clear();
  }

  /**
   * Get retriever statistics.
   */
  getStats(): Record<string, unknown> {
    return {
      keywordRetriever: this.keywordRetriever.getStats(),
      fusionConfig: this.fusionReranker.getConfig(),
    };
  }
}
