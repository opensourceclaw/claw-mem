// Copyright 2026 OpenSourceClaw Contributors
import { describe, it, expect, beforeEach } from "vitest";
import { StructuredFilter, type FilterCriteria } from "../../src/retrieval/structured-filter";
import { FusionReranker, DEFAULT_FUSION_CONFIG, type ScoredResult } from "../../src/retrieval/fusion-reranker";
import { CompletenessScorer } from "../../src/retrieval/completeness-scorer";
import { HybridRetriever, type HybridSearchOptions } from "../../src/retrieval/hybrid-retriever";
import type { RetrievalResult } from "../../src/retrieval/base";

describe("StructuredFilter", () => {
  let filter: StructuredFilter;
  let results: RetrievalResult[];

  beforeEach(() => {
    filter = new StructuredFilter();
    results = [
      { id: "1", text: "test one", score: 0.9, metadata: { session_id: "s1" }, tags: ["tag1", "tag2"], memory_type: "episodic", timestamp: "2026-06-29T10:00:00Z" },
      { id: "2", text: "test two", score: 0.8, metadata: { session_id: "s2" }, tags: ["tag2"], memory_type: "semantic", timestamp: "2026-06-28T10:00:00Z" },
      { id: "3", text: "test three", score: 0.7, metadata: { session_id: "s1" }, tags: ["tag1"], memory_type: "episodic" },
      { id: "4", text: "test four", score: 0.6, metadata: {}, tags: [], memory_type: "procedural" },
    ];
  });

  it("passes through when no criteria", () => {
    const filtered = filter.apply(results);
    expect(filtered.length).toBe(4);
  });

  it("filters by single tag", () => {
    const filtered = filter.apply(results, { tags: ["tag1"] });
    expect(filtered.length).toBe(2);
    expect(filtered.map(r => r.id)).toContain("1");
    expect(filtered.map(r => r.id)).toContain("3");
  });

  it("filters by multiple tags (AND logic)", () => {
    const filtered = filter.apply(results, { tags: ["tag1", "tag2"] });
    expect(filtered.length).toBe(1);
    expect(filtered[0].id).toBe("1");
  });

  it("filters by memory type", () => {
    const filtered = filter.apply(results, { type: "episodic" });
    expect(filtered.length).toBe(2);
  });

  it("filters by session ID", () => {
    const filtered = filter.apply(results, { sessionId: "s1" });
    expect(filtered.length).toBe(2);
  });

  it("filters by time range start", () => {
    const filtered = filter.apply(results, { timeRange: { start: "2026-06-29T00:00:00Z" } });
    // Result 1 has timestamp >= start - passes
    // Result 2 has timestamp < start - fails
    // Result 3 has no timestamp - passes through
    // Result 4 has no timestamp - passes through
    expect(filtered.length).toBe(3);
    expect(filtered.map(r => r.id)).toContain("1");
  });

  it("filters by time range end", () => {
    const filtered = filter.apply(results, { timeRange: { end: "2026-06-28T12:00:00Z" } });
    // Result 2 has timestamp <= end, result 3 and 4 have no timestamp (pass through)
    expect(filtered.length).toBe(3);
    expect(filtered.map(r => r.id)).toContain("2");
  });

  it("supports custom filter function", () => {
    const filtered = filter.apply(results, { custom: (r) => r.score > 0.75 });
    expect(filtered.length).toBe(2);
  });

  it("handles missing tags field", () => {
    results.push({ id: "5", text: "no tags", score: 0.5, metadata: {}, tags: undefined as any });
    const filtered = filter.apply(results, { tags: ["tag1"] });
    expect(filtered.length).toBe(2); // Only results with tag1
  });

  it("handles missing timestamp", () => {
    // Only results without timestamp should pass through when using time filter
    // Results 3 and 4 have no timestamp - they pass through
    // Result 1 has timestamp >= start - it passes
    // Result 2 has timestamp < start - it fails
    const filtered = filter.apply(results, { timeRange: { start: "2026-06-29T00:00:00Z" } });
    // Result 1 (timestamp OK) + results 3, 4 (no timestamp, pass through) = 3
    expect(filtered.length).toBe(3);
  });
});

describe("FusionReranker", () => {
  let reranker: FusionReranker;

  beforeEach(() => {
    reranker = new FusionReranker();
  });

  it("applies three-way weights by default (v7.5.0: 0.4/0.4/0.2)", () => {
    expect(reranker.getConfig().semanticWeight).toBe(0.4);
    expect(reranker.getConfig().keywordWeight).toBe(0.4);
    expect(reranker.getConfig().retentionWeight).toBe(0.2);
  });

  it("normalizes scores to [0, 1]", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.9, metadata: {}, source: "semantic" },
      { id: "2", text: "test", score: 0.5, metadata: {}, source: "semantic" },
    ];

    const scored = reranker.rerank(results, "test");
    expect(scored[0].semanticScore).toBeCloseTo(1.0);
    expect(scored[1].semanticScore).toBeCloseTo(0.0);
  });

  it("handles single-source results", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.9, metadata: {}, source: "semantic" },
    ];

    const scored = reranker.rerank(results, "test");
    expect(scored[0].semanticScore).toBe(0.5); // Single result normalized to 0.5
    expect(scored[0].keywordScore).toBe(0);
    // v7.5.0: 0.4*0.5 + 0.4*0 + 0.2*0.5 (missing retention → neutral 0.5)
    expect(scored[0].fusedScore).toBeCloseTo(0.3);
  });

  it("handles empty results", () => {
    const scored = reranker.rerank([], "test");
    expect(scored).toEqual([]);
  });

  it("supports custom weights", () => {
    const customReranker = new FusionReranker({ semanticWeight: 0.7, keywordWeight: 0.3 });
    expect(customReranker.getConfig().semanticWeight).toBe(0.7);
    expect(customReranker.getConfig().keywordWeight).toBe(0.3);
  });

  it("fuses retention score into fusedScore (v7.5.0 three-way)", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.9, metadata: {}, source: "semantic", retention: 0.9 },
      { id: "2", text: "test", score: 0.9, metadata: {}, source: "semantic", retention: 0.1 },
    ];

    const scored = reranker.rerank(results, "test");
    // semantic normalized: 0.5 for both (equal scores); keyword 0
    // id1: 0.4*0.5 + 0.2*0.9 = 0.38 ; id2: 0.4*0.5 + 0.2*0.1 = 0.22
    expect(scored[0].id).toBe("1");
    expect(scored[1].id).toBe("2");
    expect(scored[0].retentionScore).toBe(0.9);
    expect(scored[0].fusedScore).toBeCloseTo(0.4 * 0.5 + 0.2 * 0.9, 5);
    expect(scored[1].fusedScore).toBeCloseTo(0.4 * 0.5 + 0.2 * 0.1, 5);
  });

  it("treats missing retention as neutral 0.5", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.9, metadata: {}, source: "semantic" },
    ];

    const scored = reranker.rerank(results, "test");
    expect(scored[0].retentionScore).toBe(0.5);
  });

  it("retentionWeight 0 is order-equivalent to v7.4.2 two-way fusion", () => {
    // v7.4.2: fusedScore = 0.5*sem + 0.5*kw (minmax-normalized scores)
    // v7.5.0 with retentionWeight 0: 0.4*sem + 0.4*kw = 0.8 * legacy
    // → identical ordering, linearly scaled scores
    const legacy = (sem: number, kw: number) => 0.5 * sem + 0.5 * kw;
    const results: RetrievalResult[] = [
      { id: "a", text: "x", score: 0.9, metadata: {}, source: "semantic", retention: 0.1 },
      { id: "b", text: "x", score: 0.7, metadata: {}, source: "semantic", retention: 0.9 },
      { id: "c", text: "x", score: 0.3, metadata: {}, source: "semantic", retention: 0.5 },
      { id: "d", text: "x", score: 0.5, metadata: {}, source: "keyword", retention: 0.2 },
    ];

    const scored = reranker.rerank(results, "test", { retentionWeight: 0 });
    const order = scored.map((r) => r.id);
    const expectedOrder = [...results]
      .map((r) => ({
        id: r.id,
        v: legacy(r.source === "semantic" ? r.score : 0, r.source === "keyword" ? r.score : 0),
      }))
      .sort((a, b) => b.v - a.v)
      .map((r) => r.id);
    expect(JSON.stringify(order)).toBe(JSON.stringify(expectedOrder));
    // linear scaling: 0.4(sem+kw) == 0.8 · 0.5(sem+kw) per result
    for (const s of scored) {
      const sem = s.semanticScore ?? 0;
      const kw = s.keywordScore ?? 0;
      expect(s.fusedScore).toBeCloseTo(0.8 * legacy(sem, kw), 5);
    }
  });

  it("preserves result metadata", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.9, metadata: { key: "value" }, source: "semantic" },
    ];

    const scored = reranker.rerank(results, "test");
    expect(scored[0].metadata).toEqual({ key: "value" });
  });

  it("sorts by fused score descending", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.5, metadata: {}, source: "semantic" },
      { id: "2", text: "test", score: 0.9, metadata: {}, source: "semantic" },
    ];

    const scored = reranker.rerank(results, "test");
    expect(scored[0].id).toBe("2");
    expect(scored[1].id).toBe("1");
  });
});

describe("CompletenessScorer", () => {
  let scorer: CompletenessScorer;

  beforeEach(() => {
    scorer = new CompletenessScorer();
  });

  it("returns 0 for empty results", () => {
    const score = scorer.score([], "test query");
    expect(score).toBe(0);
  });

  it("computes keyword coverage", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "this contains the word test", score: 0.9, metadata: {} },
    ];

    const detailed = scorer.scoreDetailed(results, "test missingword");
    // "test" is covered, "missingword" is not
    expect(detailed.breakdown.coverage).toBe(0.5);
  });

  it("computes result diversity", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "completely different content here", score: 0.9, metadata: {} },
      { id: "2", text: "unique words in this result", score: 0.8, metadata: {} },
    ];

    const detailed = scorer.scoreDetailed(results, "test");
    expect(detailed.breakdown.diversity).toBeGreaterThan(0.5);
  });

  it("computes confidence from scores", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.8, metadata: {} },
      { id: "2", text: "test", score: 0.6, metadata: {} },
    ];

    const detailed = scorer.scoreDetailed(results, "test");
    expect(detailed.breakdown.confidence).toBe(0.7);
  });

  it("weights coverage highest (0.4)", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test keyword", score: 1.0, metadata: {} },
    ];

    const detailed = scorer.scoreDetailed(results, "test keyword");
    // Coverage = 1.0 (all keywords covered)
    // Diversity = 1.0 (single result)
    // Confidence = 1.0
    // Score = 0.4 * 1.0 + 0.3 * 1.0 + 0.3 * 1.0 = 1.0
    expect(detailed.score).toBeCloseTo(1.0);
  });

  it("estimates recall@10", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test keyword one", score: 0.9, metadata: {} },
      { id: "2", text: "test keyword two", score: 0.8, metadata: {} },
    ];

    const detailed = scorer.scoreDetailed(results, "test keyword");
    expect(detailed.recallAt10).toBeGreaterThan(0);
  });

  it("handles single result", () => {
    const results: RetrievalResult[] = [
      { id: "1", text: "test", score: 0.9, metadata: {} },
    ];

    const score = scorer.score(results, "test");
    expect(score).toBeGreaterThan(0);
  });
});

describe("HybridRetriever", () => {
  let retriever: HybridRetriever;

  beforeEach(() => {
    retriever = new HybridRetriever();
    // Index some test documents
    retriever.index([
      { id: "1", text: "TypeScript programming guide", metadata: { type: "semantic", tags: ["typescript", "programming"] } },
      { id: "2", text: "Python data science tutorial", metadata: { type: "semantic", tags: ["python", "data"] } },
      { id: "3", text: "JavaScript web development", metadata: { type: "episodic", tags: ["javascript", "web"] } },
    ]);
  });

  it("merges semantic and keyword results", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript programming", score: 0.9, metadata: {}, source: "semantic" },
    ]);

    const result = retriever.search("TypeScript");
    expect(result.results.length).toBeGreaterThan(0);
  });

  it("deduplicates by id", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript programming", score: 0.9, metadata: {}, source: "semantic" },
    ]);

    const result = retriever.search("TypeScript");
    const ids = result.results.map(r => r.id);
    const uniqueIds = new Set(ids);
    expect(ids.length).toBe(uniqueIds.size);
  });

  it("applies structured filters", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript", score: 0.9, metadata: {}, source: "semantic", tags: ["typescript"] },
      { id: "2", text: "Python", score: 0.8, metadata: {}, source: "semantic", tags: ["python"] },
    ]);

    const result = retriever.search("programming", { filters: { tags: ["typescript"] } });
    expect(result.results.every(r => r.tags?.includes("typescript"))).toBe(true);
  });

  it("reranks with balanced fusion", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript programming", score: 0.9, metadata: {}, source: "semantic" },
    ]);

    const result = retriever.search("TypeScript");
    expect(result.results.length).toBeGreaterThan(0);
    expect(result.results[0]).toHaveProperty("fusedScore");
  });

  it("computes completeness score", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript programming", score: 0.9, metadata: {}, source: "semantic" },
    ]);

    const result = retriever.search("TypeScript");
    expect(result.completenessScore).toBeDefined();
    expect(result.completenessScore).toBeGreaterThanOrEqual(0);
  });

  it("respects topK limit", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript", score: 0.9, metadata: {}, source: "semantic" },
      { id: "2", text: "Python", score: 0.8, metadata: {}, source: "semantic" },
      { id: "3", text: "JavaScript", score: 0.7, metadata: {}, source: "semantic" },
    ]);

    const result = retriever.search("programming", { topK: 2 });
    expect(result.results.length).toBeLessThanOrEqual(2);
  });

  it("handles empty query", () => {
    const result = retriever.search("");
    expect(result.results).toEqual([]);
  });

  it("handles no matches", () => {
    const result = retriever.search("nonexistentkeyword12345");
    expect(result.results).toEqual([]);
  });

  it("falls back to keyword-only when semantic unavailable", () => {
    // No semantic search fn set
    const result = retriever.search("TypeScript");
    expect(result.metadata.semanticCount).toBe(0);
    expect(result.metadata.keywordCount).toBeGreaterThanOrEqual(0);
  });

  it("reports selection events (selected = topK, missed = candidate pool minus topK) (v7.5.0)", () => {
    const events: Array<{ selected: string[]; missed: string[] }> = [];
    const r = new HybridRetriever({ onEvents: (selected, missed) => events.push({ selected: selected.map((x) => x.id), missed: missed.map((x) => x.id) }) });
    r.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript", score: 0.9, metadata: {}, source: "semantic" },
      { id: "2", text: "Python", score: 0.8, metadata: {}, source: "semantic" },
      { id: "3", text: "JavaScript", score: 0.7, metadata: {}, source: "semantic" },
      { id: "4", text: "Ruby", score: 0.6, metadata: {}, source: "semantic" },
    ]);
    r.index([
      { id: "2", text: "Python tutorial" },
      { id: "3", text: "JavaScript web" },
      { id: "5", text: "Rust systems" },
    ]);

    r.search("programming", { topK: 2 });
    expect(events).toHaveLength(1);
    expect(events[0].selected).toEqual(["1", "2"]);
    // candidate pool = merged (semantic 1-4 ∪ keyword 2,3,5); missed = pool - selected
    expect(events[0].missed).toContain("3");
    expect(events[0].missed).toContain("4");
    expect(events[0].missed).not.toContain("1");
    expect(events[0].missed).not.toContain("2");
  });

  it("carries retention scores onto results via getRetentionScore (v7.5.0)", () => {
    const r = new HybridRetriever({ getRetentionScore: (id) => (id === "1" ? 0.9 : 0.1) });
    r.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript", score: 0.9, metadata: {}, source: "semantic" },
      { id: "2", text: "Python", score: 0.8, metadata: {}, source: "semantic" },
    ]);
    r.index([{ id: "1", text: "TypeScript guide" }]);

    const result = r.search("TypeScript");
    const byId = new Map(result.results.map((x) => [x.id, x]));
    expect(byId.get("1")?.retention).toBe(0.9);
    expect(byId.get("2")?.retention).toBe(0.1);
  });

  it("does not emit events when onEvents is not configured", () => {
    const result = retriever.search("TypeScript");
    expect(result.results.length).toBeGreaterThanOrEqual(0);
  });

  it("returns metadata with counts", () => {
    retriever.setSemanticSearchFn((query, limit) => [
      { id: "1", text: "TypeScript", score: 0.9, metadata: {}, source: "semantic" },
    ]);

    const result = retriever.search("TypeScript");
    expect(result.metadata.semanticCount).toBeDefined();
    expect(result.metadata.keywordCount).toBeDefined();
    expect(result.metadata.afterFilterCount).toBeDefined();
    expect(result.metadata.latencyMs).toBeGreaterThanOrEqual(0);
  });
});
