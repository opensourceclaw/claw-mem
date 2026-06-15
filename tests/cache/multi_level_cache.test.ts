import { describe, it, expect } from "vitest";
import { MultiLevelCache } from "../../src/cache/multi_level_cache.js";

describe("MultiLevelCache", () => {
  describe("get L1 hit", () => {
    it("should return result from L1 on exact match", () => {
      const cache = new MultiLevelCache();
      cache.set("hello world", ["result"]);
      const result = cache.get("hello world");
      expect(result).toEqual(["result"]);
    });
  });

  describe("get L2 hit", () => {
    it("should return result from L2 when L1 misses but L2 matches", () => {
      const cache = new MultiLevelCache({
        l2SimilarityThreshold: 0.3,
      });
      cache.set("capital of France", ["Paris"]);
      // "french capital" has keywords ["french", "capital"]
      // "capital of France" has keywords ["capital", "france"]
      // Jaccard: 1/3 ≈ 0.33 >= 0.3
      const result = cache.get("french capital");
      expect(result).toEqual(["Paris"]);
    });
  });

  describe("get L3 hit", () => {
    it("should return result from L3 when L1 and L2 both miss", () => {
      const cache = new MultiLevelCache({
        enableL2: false,
        l2SimilarityThreshold: 0.3,
      });
      cache.set("Python programming", ["python_result"]);
      cache.set("JavaScript web", ["js_result"]);
      // L3 match via "programming" keyword overlap
      const result = cache.get("programming language");
      expect(result).toEqual(["python_result"]);
    });
  });

  describe("complete miss", () => {
    it("should return undefined when all levels miss", () => {
      const cache = new MultiLevelCache();
      cache.set("hello world", ["result"]);
      const result = cache.get("something completely different");
      expect(result).toBeUndefined();
    });
  });

  describe("empty query", () => {
    it("should return undefined for empty query", () => {
      const cache = new MultiLevelCache();
      expect(cache.get("")).toBeUndefined();
      expect(cache.get("   ")).toBeUndefined();
    });
  });

  describe("promote to L1", () => {
    it("should promote L2 hit results to L1", () => {
      const cache = new MultiLevelCache({
        l2SimilarityThreshold: 0.3,
      });
      cache.set("capital of France", ["Paris"]);

      // L2 hit (L1 miss)
      cache.get("french capital");

      // Now L1 should have it (promoted)
      const result = cache.get("french capital");
      expect(result).toEqual(["Paris"]);
    });
  });

  describe("event system", () => {
    it("should emit L1 hit event on L1 hit", () => {
      const cache = new MultiLevelCache();
      const events: string[] = [];
      cache.onEvent((event) => events.push(event.type));

      cache.set("hello", ["world"]);
      cache.get("hello");

      expect(events).toContain("l1_hit");
    });

    it("should emit miss event on complete miss", () => {
      const cache = new MultiLevelCache();
      const events: string[] = [];
      cache.onEvent((event) => events.push(event.type));

      cache.get("nothing");

      expect(events).toContain("miss");
    });

    it("should emit set event on set", () => {
      const cache = new MultiLevelCache();
      const events: string[] = [];
      cache.onEvent((event) => events.push(event.type));

      cache.set("hello", ["world"]);

      expect(events).toContain("set");
    });
  });

  describe("all levels disabled", () => {
    it("should return undefined when all levels disabled", () => {
      const cache = new MultiLevelCache({
        enableL1: false,
        enableL2: false,
        enableL3: false,
      });
      cache.set("hello", ["world"]);
      const result = cache.get("hello");
      expect(result).toBeUndefined();
    });
  });

  describe("reset", () => {
    it("should clear all caches and statistics", () => {
      const cache = new MultiLevelCache();
      cache.set("hello", ["world"]);
      cache.get("hello"); // L1 hit

      cache.reset();

      // Check stats before any new get calls
      const stats = cache.getStats();
      expect(stats.overall.hits).toBe(0);
      expect(stats.overall.misses).toBe(0);
    });
  });

  describe("getStats", () => {
    it("should return correct cache statistics", () => {
      const cache = new MultiLevelCache();
      cache.set("hello", ["world"]);
      cache.get("hello"); // L1 hit
      // "nothing" cascades L1→L2→L3 → 3 misses
      cache.get("nothing");

      const stats = cache.getStats();
      expect(stats.l1.hits).toBe(1);
      // 3 levels miss = 3 overall misses
      expect(stats.overall.misses).toBe(3);
      expect(stats.overall.hits).toBe(1);
    });
  });

  describe("cleanup", () => {
    it("should clear all caches", () => {
      const cache = new MultiLevelCache();
      cache.set("hello", ["world"]);
      cache.set("test", ["data"]);
      cache.cleanup();
      expect(cache.get("hello")).toBeUndefined();
      expect(cache.get("test")).toBeUndefined();
    });
  });
});
