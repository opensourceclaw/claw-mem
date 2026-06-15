import { describe, it, expect } from "vitest";
import { CacheManager } from "../../src/cache/index.js";

describe("CacheManager", () => {
  describe("get/set flow", () => {
    it("should store and retrieve results", () => {
      const cm = new CacheManager();
      cm.set("hello world", ["result1", "result2"]);
      const result = cm.get("hello world");
      expect(result).toEqual(["result1", "result2"]);
    });

    it("should return undefined for uncached query", () => {
      const cm = new CacheManager();
      const result = cm.get("nothing here");
      expect(result).toBeUndefined();
    });
  });

  describe("getStats", () => {
    it("should return valid cache statistics", () => {
      const cm = new CacheManager();
      cm.set("query1", ["result1"]);
      cm.get("query1"); // hit
      cm.get("query2"); // miss (3 levels = 3 misses)

      const stats = cm.getStats();
      expect(stats).toHaveProperty("l1");
      expect(stats).toHaveProperty("l2");
      expect(stats).toHaveProperty("l3");
      expect(stats).toHaveProperty("overall");
      expect(stats.overall.hits).toBe(1);
      expect(stats.overall.misses).toBe(3);
    });
  });

  describe("event subscription", () => {
    it("should trigger event listeners", () => {
      const cm = new CacheManager();
      const events: string[] = [];
      cm.onEvent((event) => events.push(event.type));

      cm.set("test", ["data"]);
      cm.get("test");

      expect(events.length).toBeGreaterThan(0);
    });
  });

  describe("reset", () => {
    it("should clear all caches and statistics", () => {
      const cm = new CacheManager();
      cm.set("hello", ["world"]);
      cm.get("hello");

      cm.reset();

      const stats = cm.getStats();
      expect(stats.overall.hits).toBe(0);
      expect(stats.overall.misses).toBe(0);
    });
  });

  describe("invalidate", () => {
    it("should invalidate specific query", () => {
      const cm = new CacheManager();
      cm.set("query1", ["result1"]);
      cm.set("query2", ["result2"]);

      cm.invalidate("query1");
      expect(cm.get("query1")).toBeUndefined();
      expect(cm.get("query2")).toEqual(["result2"]);
    });
  });

  describe("cleanup", () => {
    it("should clear all caches", () => {
      const cm = new CacheManager();
      cm.set("test", ["data"]);
      cm.cleanup();
      expect(cm.get("test")).toBeUndefined();
    });
  });

  describe("re-exports", () => {
    it("should export QueryCache, SemanticCache, MultiLevelCache", async () => {
      const mod = await import("../../src/cache/index.js");
      expect(mod.QueryCache).toBeDefined();
      expect(mod.SemanticCache).toBeDefined();
      expect(mod.MultiLevelCache).toBeDefined();
    });
  });
});
