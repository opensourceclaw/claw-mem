import { describe, it, expect } from "vitest";
import { SemanticCache } from "../../src/cache/semantic_cache.js";

describe("SemanticCache", () => {
  describe("find", () => {
    it("should return cached result for similar query", () => {
      const cache = new SemanticCache(100, 0.3);
      cache.store("capital of France", ["Paris"]);
      // "capital of France" → keywords: ["capital", "france"]
      // "french capital" → keywords: ["french", "capital"]
      // Jaccard: 1/3 ≈ 0.33 >= 0.3
      const result = cache.find("french capital");
      expect(result).toBeDefined();
      expect(result!.results).toEqual(["Paris"]);
      expect(result!.matchedQuery).toBe("capital of France");
    });

    it("should return undefined for dissimilar query", () => {
      const cache = new SemanticCache(100, 0.8);
      cache.store("capital of France", ["Paris"]);
      const result = cache.find("quantum physics");
      expect(result).toBeUndefined();
    });

    it("should return undefined when no entries exist", () => {
      const cache = new SemanticCache();
      const result = cache.find("anything");
      expect(result).toBeUndefined();
    });

    it("should return undefined for empty query", () => {
      const cache = new SemanticCache();
      cache.store("test", ["result"]);
      expect(cache.find("")).toBeUndefined();
      expect(cache.find("   ")).toBeUndefined();
    });

    it("should return undefined when query has no keywords", () => {
      const cache = new SemanticCache();
      cache.store("test query", ["result"]);
      const result = cache.find("a an the is");
      expect(result).toBeUndefined();
    });
  });

  describe("store", () => {
    it("should update existing entry on re-store", () => {
      const cache = new SemanticCache(100, 0.5);
      cache.store("hello world", ["old"]);
      cache.store("hello world", ["new"]);
      const result = cache.find("hello world");
      expect(result!.results).toEqual(["new"]);
    });
  });

  describe("eviction", () => {
    it("should evict lowest-access entry when over maxSize", () => {
      const cache = new SemanticCache(2, 0.3);
      cache.store("Python programming", ["python"]);
      cache.store("JavaScript web", ["js"]);
      // Access "JavaScript web" twice
      cache.find("JavaScript web");
      cache.find("JavaScript web");
      // This should evict "Python programming" (lowest access count)
      cache.store("data science", ["data"]);

      expect(cache.find("Python programming")).toBeUndefined();
      const resultB = cache.find("JavaScript web");
      expect(resultB).toBeDefined();
    });
  });

  describe("calcSimilarity", () => {
    it("should return the best match among multiple entries", () => {
      const cache = new SemanticCache(100, 0.3);
      cache.store("Python programming language", ["python"]);
      cache.store("JavaScript web development", ["js"]);
      const result = cache.find("programming language");
      expect(result).toBeDefined();
      expect(result!.results).toEqual(["python"]);
    });
  });

  describe("getStats", () => {
    it("should return correct statistics", () => {
      const cache = new SemanticCache(100, 0.5);
      cache.store("query1", ["result1"]);
      cache.find("query1"); // hit
      cache.find("query2"); // miss

      const stats = cache.getStats();
      expect(stats.size).toBe(1);
      expect(stats.hits).toBe(1);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBe(50);
    });
  });

  describe("cleanup", () => {
    it("should clear all entries", () => {
      const cache = new SemanticCache(100, 0.5);
      cache.store("query1", ["result1"]);
      cache.store("query2", ["result2"]);
      cache.cleanup();
      expect(cache.getEntries()).toHaveLength(0);
    });
  });

  describe("remove", () => {
    it("should remove a specific query from cache", () => {
      const cache = new SemanticCache(100, 0.5);
      cache.store("query1", ["result1"]);
      cache.store("query2", ["result2"]);
      cache.remove("query1");
      expect(cache.find("query1")).toBeUndefined();
      expect(cache.find("query2")).toBeDefined();
    });
  });
});
