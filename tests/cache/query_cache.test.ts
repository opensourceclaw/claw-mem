import { describe, it, expect } from "vitest";
import { QueryCache } from "../../src/cache/query_cache.js";

describe("QueryCache", () => {
  describe("makeKey", () => {
    it("should generate normalized and keywords correctly", () => {
      const cache = new QueryCache();
      const key = cache.makeKey("What is the capital of France?");
      expect(key.normalized).toBe("what is the capital of france");
      expect(key.keywords).toContain("capital");
      expect(key.keywords).toContain("france");
      expect(key.keywords).not.toContain("the");
      expect(key.keywords).not.toContain("of");
    });

    it("should extract non-stop-word tokens from CJK queries", () => {
      const cache = new QueryCache();
      // CJK text without spaces is one token, so stop word filtering applies by token length
      const key = cache.makeKey("法国的首都是什么");
      expect(key.normalized).toBe("法国的首都是什么");
      // "法国" and "首都" are substrings of the full token, not separate tokens
      // The full token "法国的首都是什么" has length > 2 and is not a stop word
      expect(key.keywords.length).toBeGreaterThan(0);
      // CJK with spaces should tokenize properly
      const spacedKey = cache.makeKey("法国 首都 是什么");
      expect(spacedKey.keywords).toContain("法国");
      expect(spacedKey.keywords).toContain("首都");
    });
  });

  describe("get/put exact match", () => {
    it("should return cached results for the same query", () => {
      const cache = new QueryCache(100, 86400);
      const results = [{ id: 1 }, { id: 2 }];
      cache.put("What is AI?", results);
      const cached = cache.get("What is AI?");
      expect(cached).toEqual(results);
    });

    it("should return undefined for a different query", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("What is AI?", [{ id: 1 }]);
      const cached = cache.get("What is ML?");
      expect(cached).toBeUndefined();
    });

    it("should handle empty query", () => {
      const cache = new QueryCache();
      const result = cache.get("");
      expect(result).toBeUndefined();

      const result2 = cache.get("   ");
      expect(result2).toBeUndefined();
    });
  });

  describe("exactMatch", () => {
    it("should find exact match by normalized key", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("Hello World", [{ data: "test" }]);
      const key = cache.makeKey("Hello World");
      const result = cache.exactMatch(key);
      expect(result).toEqual([{ data: "test" }]);
    });

    it("should return undefined for non-existent key", () => {
      const cache = new QueryCache(100, 86400);
      const key = cache.makeKey("Nothing Here");
      const result = cache.exactMatch(key);
      expect(result).toBeUndefined();
    });
  });

  describe("keywordMatch (Jaccard similarity)", () => {
    it("should find approximate match with sufficient keyword overlap", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("capital of France", ["Paris"]);
      // "capital of France" → keywords: ["capital", "france"]
      // "french capital" → keywords: ["french", "capital"]
      // Jaccard: intersection=["capital"] / union=["capital","france","french"] = 1/3 ≈ 0.33
      const key = cache.makeKey("french capital");
      const result = cache.keywordMatch(key, 0.3);
      expect(result).toBeDefined();
      expect(result!.results).toEqual(["Paris"]);
    });

    it("should return undefined for low keyword overlap", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("capital of France", ["Paris"]);
      const key = cache.makeKey("quantum physics");
      const result = cache.keywordMatch(key, 0.5);
      expect(result).toBeUndefined();
    });

    it("should return undefined when query has no keywords", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("capital of France", ["Paris"]);
      const key = cache.makeKey("a an the");
      const result = cache.keywordMatch(key, 0.5);
      expect(result).toBeUndefined();
    });
  });

  describe("TTL expiry", () => {
    it("should return undefined after TTL expires", async () => {
      const cache = new QueryCache(100, 0); // 0s TTL = instant expiry
      cache.put("test query", ["result"]);
      await new Promise((r) => setTimeout(r, 10));
      const result = cache.get("test query");
      expect(result).toBeUndefined();
    });
  });

  describe("LRU eviction", () => {
    it("should evict oldest entries when over maxSize", () => {
      const cache = new QueryCache(2, 86400);
      cache.put("query1", ["result1"]);
      cache.put("query2", ["result2"]);
      cache.put("query3", ["result3"]); // should evict query1

      expect(cache.get("query1")).toBeUndefined();
      expect(cache.get("query2")).toEqual(["result2"]);
      expect(cache.get("query3")).toEqual(["result3"]);
    });
  });

  describe("invalidate", () => {
    it("should invalidate specific query", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("query1", ["result1"]);
      cache.put("query2", ["result2"]);
      cache.invalidate("query1");
      expect(cache.get("query1")).toBeUndefined();
      expect(cache.get("query2")).toEqual(["result2"]);
    });

    it("should clear all when no query specified", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("query1", ["result1"]);
      cache.put("query2", ["result2"]);
      cache.invalidate();
      expect(cache.get("query1")).toBeUndefined();
      expect(cache.get("query2")).toBeUndefined();
    });
  });

  describe("getStats", () => {
    it("should return correct statistics", () => {
      const cache = new QueryCache(100, 86400);
      cache.put("query1", ["result1"]);
      cache.get("query1"); // hit
      cache.get("query2"); // miss

      const stats = cache.getStats();
      expect(stats.size).toBe(1);
      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBe(50);
    });
  });
});
