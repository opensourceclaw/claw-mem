// claw-mem v5.0.0 — Retrieval Module Tests (TypeScript)
//
// Tests cover: BM25 scoring, keyword search, three-tier search,
// hybrid routing, query cache, and synonym expansion.
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

import { describe, it, expect } from "vitest";
import { BM25 } from "../../src/retrieval/bm25";
import { KeywordRetriever, tokenize } from "../../src/retrieval/keyword";
import { ThreeTierRetriever, MemoryLayer } from "../../src/retrieval/three_tier";
import type { LayerRetrievalContext } from "../../src/retrieval/three_tier";
import { HybridRouter, QueryType } from "../../src/retrieval/hybrid_router";
import { QueryCache, getQueryCache, resetQueryCache } from "../../src/retrieval/query_cache";
import { SynonymExpander, BUILTIN_SYNONYMS } from "../../src/retrieval/synonym";
import type { RetrievalDocument } from "../../src/retrieval/base";

// ── BM25 Tests ──────────────────────────────────────────────────────────────

describe("BM25", () => {
  it("should compute scores for matching documents", () => {
    const bm25 = new BM25(1.5, 0.75);
    bm25.addDocument("doc1", ["hello", "world", "foo"]);
    bm25.addDocument("doc2", ["hello", "world", "bar", "baz"]);
    bm25.addDocument("doc3", ["goodbye", "cruel", "world"]);

    expect(bm25.documentCount).toBe(3);
    expect(bm25.averageDocumentLength).toBeCloseTo(10 / 3, 4);

    const scores = bm25.getScores(["hello"]);
    expect(scores).toHaveLength(3);
    // doc1 contains "hello" once, doc2 contains "hello" once, doc3 does not
    expect(scores[0]).toBeGreaterThan(0); // doc1
    expect(scores[1]).toBeGreaterThan(0); // doc2
    expect(scores[2]).toBe(0); // doc3 has no "hello"
  });

  it("should give higher scores to documents with more query term matches", () => {
    const bm25 = new BM25(1.5, 0.75);
    bm25.addDocument("doc1", ["hello", "world"]);
    bm25.addDocument("doc2", ["hello", "hello", "world", "world"]);
    bm25.addDocument("doc3", ["goodbye"]);

    const scores = bm25.getScores(["hello", "world"]);
    // doc2 has higher term frequency for both terms
    expect(scores[1]).toBeGreaterThan(scores[0]);
    expect(scores[2]).toBe(0);
  });

  it("should return 0 for nonexistent documents", () => {
    const bm25 = new BM25();
    bm25.addDocument("doc1", ["hello"]);
    expect(bm25.score(["hello"], "nonexistent")).toBe(0);
  });

  it("should handle empty tokens gracefully", () => {
    const bm25 = new BM25();
    bm25.addDocument("doc1", []);
    expect(bm25.getScores([])).toEqual([]);
    expect(bm25.score([], "doc1")).toBe(0);
  });

  it("should support document removal", () => {
    const bm25 = new BM25();
    bm25.addDocument("doc1", ["hello", "world"]);
    bm25.addDocument("doc2", ["hello"]);
    expect(bm25.documentCount).toBe(2);

    bm25.removeDocument("doc1");
    expect(bm25.documentCount).toBe(1);
    expect(bm25.hasDocument("doc1")).toBe(false);
    expect(bm25.hasDocument("doc2")).toBe(true);

    const scores = bm25.getScores(["hello"]);
    expect(scores).toHaveLength(1);
    expect(scores[0]).toBeGreaterThan(0);
  });

  it("should support clearing all data", () => {
    const bm25 = new BM25();
    bm25.addDocument("doc1", ["hello", "world"]);
    expect(bm25.documentCount).toBe(1);

    bm25.clear();
    expect(bm25.documentCount).toBe(0);
    expect(bm25.getScores(["hello"])).toEqual([]);
  });
});

// ── Tokenizer Tests ─────────────────────────────────────────────────────────

describe("tokenize", () => {
  it("should tokenize English text", () => {
    const tokens = tokenize("Hello World!");
    expect(tokens).toContain("hello");
    expect(tokens).toContain("world");
  });

  it("should extract CJK characters", () => {
    const tokens = tokenize("你好世界");
    expect(tokens).toContain("你");
    expect(tokens).toContain("好");
    expect(tokens).toContain("世");
    expect(tokens).toContain("界");
  });
});

// ── KeywordRetriever Tests ──────────────────────────────────────────────────

describe("KeywordRetriever", () => {
  it("should find documents by keyword match", () => {
    const retriever = new KeywordRetriever();
    retriever.addDocument("doc1", "The quick brown fox");
    retriever.addDocument("doc2", "jumps over the lazy dog");
    retriever.addDocument("doc3", "The fox is quick");

    const results = retriever.search("fox", 10);
    expect(results).toHaveLength(2); // doc1 and doc3
    expect(results.map((r) => r.id).sort()).toEqual(["doc1", "doc3"]);
    expect(results[0].source).toBe("keyword");
  });

  it("should return empty results for non-matching query", () => {
    const retriever = new KeywordRetriever();
    retriever.addDocument("doc1", "hello world");
    const results = retriever.search("zzz_nonexistent_zzz");
    expect(results).toHaveLength(0);
  });

  it("should return empty results for empty query", () => {
    const retriever = new KeywordRetriever();
    retriever.addDocument("doc1", "hello world");
    expect(retriever.search("")).toHaveLength(0);
    expect(retriever.search("   ")).toHaveLength(0);
  });

  it("should support index() with multiple documents", () => {
    const retriever = new KeywordRetriever();
    const docs: RetrievalDocument[] = [
      { id: "a", text: "alpha beta gamma" },
      { id: "b", text: "beta delta epsilon" },
      { id: "c", text: "zeta eta theta" },
    ];
    retriever.index(docs);

    const results = retriever.search("beta", 10);
    // n-gram matching also catches "eta" in doc c — it's a feature
    expect(results.length).toBeGreaterThanOrEqual(2);
    // a and b should be ranked highest
    expect(results[0].id).toBe("a");
    expect(results[1].id).toBe("b");
  });

  it("should perform exact substring match via searchExact", () => {
    const retriever = new KeywordRetriever();
    const docs: RetrievalDocument[] = [
      { id: "x", text: "memory system for AI" },
      { id: "y", text: "retrieval augmented generation" },
    ];
    const results = retriever.searchExact("memory", docs);
    expect(results).toHaveLength(1);
    expect(results[0].id).toBe("x");
  });

  it("should support clear()", () => {
    const retriever = new KeywordRetriever();
    retriever.addDocument("doc1", "hello");
    expect(retriever.search("hello")).toHaveLength(1);
    retriever.clear();
    expect(retriever.search("hello")).toHaveLength(0);
  });

  it("should report stats", () => {
    const retriever = new KeywordRetriever();
    retriever.addDocument("doc1", "hello world");
    const stats = retriever.getStats();
    expect(stats.documentCount).toBe(1);
    expect(stats.bm25DocCount).toBe(1);
  });
});

// ── ThreeTierRetriever Tests ─────────────────────────────────────────────────

describe("ThreeTierRetriever", () => {
  it("should search across all layers and return results", () => {
    const retriever = new ThreeTierRetriever();
    const context: LayerRetrievalContext = {
      getL1Memories: () => [
        { id: "l1_1", content: "Current session memory about AI", tags: ["ai"], type: "episodic" },
        { id: "l1_2", content: "User mentioned project preferences", tags: ["prefs"], type: "episodic" },
      ],
      getL2Memories: () => [
        { id: "l2_1", content: "Yesterday discussion about memory systems", tags: ["memory"], type: "semantic" },
      ],
      getL3Memories: () => [
        { id: "l3_1", content: "Long-term knowledge: AI architecture patterns", tags: ["ai", "architecture"], type: "semantic" },
      ],
    };

    const results = retriever.search("AI memory", context);
    expect(results.length).toBeGreaterThanOrEqual(1);
    // All results should have scores
    for (const r of results) {
      expect(r.score).toBeGreaterThanOrEqual(0);
      expect(r.memoryId).toBeTruthy();
      expect(r.content).toBeTruthy();
      expect(r.layer).toBeDefined();
    }
  });

  it("should return empty results when no context provided", () => {
    const retriever = new ThreeTierRetriever();
    const context: LayerRetrievalContext = {};
    const results = retriever.search("anything", context);
    expect(results).toHaveLength(0);
  });

  it("should search a single layer only", () => {
    const retriever = new ThreeTierRetriever();
    const context: LayerRetrievalContext = {
      getL1Memories: () => [
        { id: "l1_a", content: "Working memory item alpha", tags: [] },
      ],
      getL2Memories: () => [
        { id: "l2_a", content: "Short-term item about alpha", tags: [] },
      ],
    };

    const results = retriever.search("alpha", context, [MemoryLayer.L1], 10);
    expect(results).toHaveLength(1);
    expect(results[0].layer).toBe(MemoryLayer.L1);
  });

  it("should filter by memory type", () => {
    const retriever = new ThreeTierRetriever();
    const context: LayerRetrievalContext = {
      getL1Memories: () => [
        { id: "l1_e", content: "episodic event", tags: [], type: "episodic" },
        { id: "l1_s", content: "semantic fact", tags: [], type: "semantic" },
      ],
    };

    const results = retriever.search("event", context, [MemoryLayer.L1], 10, "episodic");
    expect(results).toHaveLength(1);
    expect(results[0].memoryType).toBe("episodic");
  });

  it("should deduplicate identical content across layers", () => {
    const retriever = new ThreeTierRetriever();
    const context: LayerRetrievalContext = {
      getL1Memories: () => [
        { id: "l1_dup", content: "Duplicate content here", tags: [] },
      ],
      getL2Memories: () => [
        { id: "l2_dup", content: "Duplicate content here", tags: [] },
      ],
    };

    const results = retriever.search("Duplicate content here", context);
    expect(results).toHaveLength(1);
  });
});

// ── HybridRouter Tests ───────────────────────────────────────────────────────

describe("HybridRouter", () => {
  const router = new HybridRouter();

  it("should classify fact queries", () => {
    expect(router.classify("who created Python")).toBe(QueryType.FACT);
    expect(router.classify("what is the config")).toBe(QueryType.FACT);
    expect(router.classify("where is the file")).toBe(QueryType.FACT);
    expect(router.classify("什么时候")).toBe(QueryType.FACT);
  });

  it("should classify semantic queries", () => {
    expect(router.classify("how does memory work")).toBe(QueryType.SEMANTIC);
    expect(router.classify("explain the architecture")).toBe(QueryType.SEMANTIC);
    expect(router.classify("why is it slow")).toBe(QueryType.SEMANTIC);
  });

  it("should classify relation queries", () => {
    expect(router.classify("compare A and B")).toBe(QueryType.RELATION);
    expect(router.classify("difference between X and Y")).toBe(QueryType.RELATION);
    expect(router.classify("A vs B")).toBe(QueryType.RELATION);
  });

  it("should route to the correct pipeline", () => {
    const factSpy = { called: false };
    const semanticSpy = { called: false };
    const relationSpy = { called: false };

    router.route(
      "what is the answer",
      (q, limit) => { factSpy.called = true; return [q]; },
      (q, limit) => { semanticSpy.called = true; return [q]; },
      (q, limit) => { relationSpy.called = true; return [q]; },
    );

    expect(factSpy.called).toBe(true);
    expect(semanticSpy.called).toBe(false);
    expect(relationSpy.called).toBe(false);
  });

  it("should return SEMANTIC for empty query", () => {
    expect(router.classify("")).toBe(QueryType.SEMANTIC);
    expect(router.classify("   ")).toBe(QueryType.SEMANTIC);
  });
});

// ── QueryCache Tests ─────────────────────────────────────────────────────────

describe("QueryCache", () => {
  it("should store and retrieve cached results", () => {
    const cache = new QueryCache(100, 60);
    const results = [{ id: "1", text: "hello" }];

    cache.put("test query", results);
    const cached = cache.get("test query");
    expect(cached).toEqual(results);
  });

  it("should return undefined for cache miss", () => {
    const cache = new QueryCache(100, 60);
    expect(cache.get("nonexistent")).toBeUndefined();
  });

  it("should evict LRU entries when full", () => {
    const cache = new QueryCache(2, 60);
    cache.put("query1", [{ id: "1" }]);
    cache.put("query2", [{ id: "2" }]);
    cache.put("query3", [{ id: "3" }]); // should evict query1

    expect(cache.get("query1")).toBeUndefined();
    expect(cache.get("query2")).toBeDefined();
    expect(cache.get("query3")).toBeDefined();
  });

  it("should invalidate all entries", () => {
    const cache = new QueryCache(100, 60);
    cache.put("q1", []);
    cache.put("q2", []);
    cache.invalidate();
    expect(cache.get("q1")).toBeUndefined();
    expect(cache.get("q2")).toBeUndefined();
  });

  it("should invalidate a single entry", () => {
    const cache = new QueryCache(100, 60);
    cache.put("q1", [{ id: "1" }]);
    cache.put("q2", [{ id: "2" }]);
    cache.invalidate("q1");
    expect(cache.get("q1")).toBeUndefined();
    expect(cache.get("q2")).toBeDefined();
  });

  it("should report stats", () => {
    const cache = new QueryCache(100, 300);
    cache.put("query", [{ id: "1" }]);
    cache.get("query"); // hit
    cache.get("nonexistent"); // miss
    cache.get("nonexistent2"); // miss

    const stats = cache.getStats();
    expect(stats.hits).toBe(1);
    expect(stats.misses).toBe(2);
    expect(stats.hitRate).toBeCloseTo(33.33, 1);
    expect(stats.size).toBe(1);
  });

  it("should expire entries after TTL", async () => {
    const cache = new QueryCache(100, 0); // 0 second TTL = immediate expiry
    cache.put("query", [{ id: "1" }]);

    // Wait a tick so the TTL check passes
    await new Promise((resolve) => setTimeout(resolve, 10));

    const result = cache.get("query");
    expect(result).toBeUndefined();
  });
});

describe("getQueryCache singleton", () => {
  it("should return the same instance", () => {
    const a = getQueryCache();
    const b = getQueryCache();
    expect(a).toBe(b);
  });

  it("should reset correctly", () => {
    const a = getQueryCache();
    resetQueryCache();
    const b = getQueryCache();
    expect(a).not.toBe(b);
  });
});

// ── SynonymExpander Tests ────────────────────────────────────────────────────

describe("SynonymExpander", () => {
  it("should expand known terms with synonyms", () => {
    const expander = new SynonymExpander();
    const expanded = expander.expand("AI search");
    expect(expanded).not.toBe("AI search"); // should have additional terms
    expect(expanded.length).toBeGreaterThan("AI search".length);
    // Should include synonyms
    expect(expanded.toLowerCase()).toContain("人工智能".toLowerCase());
  });

  it("should return original query if no synonyms found", () => {
    const expander = new SynonymExpander();
    const query = "xyzzy_nonexistent_42";
    expect(expander.expand(query)).toBe(query);
  });

  it("should respect maxExpansions limit", () => {
    const expander = new SynonymExpander(undefined, true, 2);
    const expanded = expander.expand("memory");
    // "memory" has many synonyms (记忆, storage, cache, etc.)
    // but should be limited to 2 expansions
    const original = "memory";
    const extra = expanded.slice(original.length).trim().split(/\s+/);
    expect(extra.length).toBeLessThanOrEqual(2);
  });

  it("should return original query when disabled", () => {
    const expander = new SynonymExpander(undefined, false);
    expect(expander.expand("AI search")).toBe("AI search");
  });

  it("should support custom synonyms", () => {
    const expander = new SynonymExpander({ "custom_term": ["custom_syn"] });
    const syns = expander.getSynonyms("custom_term");
    expect(syns).toContain("custom_syn");
  });

  it("should support addSynonyms", () => {
    const expander = new SynonymExpander();
    expander.addSynonyms("foo", ["bar", "baz"]);
    const syns = expander.getSynonyms("foo");
    expect(syns).toContain("bar");
    expect(syns).toContain("baz");
  });

  it("should have BUILTIN_SYNONYMS defined", () => {
    expect(BUILTIN_SYNONYMS).toBeDefined();
    expect(Object.keys(BUILTIN_SYNONYMS).length).toBeGreaterThan(50);
    expect(BUILTIN_SYNONYMS["memory"]).toBeDefined();
    expect(BUILTIN_SYNONYMS["ai"]).toBeDefined();
  });

  it("should return empty array for unknown keyword", () => {
    const expander = new SynonymExpander();
    expect(expander.getSynonyms("nonexistent_xyzzy")).toEqual([]);
  });
});
