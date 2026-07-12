// Copyright 2026 Peter Cheng
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

/**
 * v6.37.0: Memory Leak Regression Tests for QueryCache
 *
 * Tests for:
 * - LRU eviction when at capacity
 * - Session-level cache creation (createQueryCache)
 * - Global cache cleanup (clearGlobalQueryCache)
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  QueryCache,
  getQueryCache,
  createQueryCache,
  clearGlobalQueryCache,
  resetQueryCache,
} from "../../src/retrieval/query_cache";

describe("QueryCache: Memory Leak Regression Tests", () => {
  afterEach(() => {
    // Reset global cache between tests
    resetQueryCache();
  });

  describe("LRU Eviction", () => {
    it("should enforce max size limit", () => {
      const cache = new QueryCache(5, 300);

      // Add 5 entries
      for (let i = 0; i < 5; i++) {
        cache.put(`query ${i}`, [`result ${i}`]);
      }

      expect(cache.getStats().size).toBe(5);

      // Add 6th entry, should evict LRU
      cache.put("query 6", ["result 6"]);
      expect(cache.getStats().size).toBe(5);
    });

    it("should evict least recently used entries", () => {
      const cache = new QueryCache(3, 300);

      cache.put("query a", ["result a"]);
      cache.put("query b", ["result b"]);
      cache.put("query c", ["result c"]);

      // Access "query a" to make it recently used
      cache.get("query a");

      // Add new entry, should evict "query b" (LRU)
      cache.put("query d", ["result d"]);

      expect(cache.get("query a")).toEqual(["result a"]);
      expect(cache.get("query b")).toBeUndefined(); // Evicted
      expect(cache.get("query c")).toEqual(["result c"]);
      expect(cache.get("query d")).toEqual(["result d"]);
    });

    it("should handle rapid put operations", () => {
      const cache = new QueryCache(100, 300);

      // Rapidly put 1000 entries
      for (let i = 0; i < 1000; i++) {
        cache.put(`rapid query ${i}`, [`rapid result ${i}`]);
      }

      // Should never exceed maxSize
      expect(cache.getStats().size).toBe(100);
    });
  });

  describe("TTL Expiration", () => {
    it("should respect TTL and remove expired entries", async () => {
      const cache = new QueryCache(10, 1); // 1 second TTL

      cache.put("expiring query", ["expiring result"]);

      // Should be present immediately
      expect(cache.get("expiring query")).toEqual(["expiring result"]);

      // Wait for TTL
      await new Promise((resolve) => setTimeout(resolve, 1100));

      // Should be expired
      expect(cache.get("expiring query")).toBeUndefined();
    });

    it("should cleanup expired entries on cleanupExpired()", async () => {
      const cache = new QueryCache(10, 1);

      cache.put("old query", ["old result"]);

      await new Promise((resolve) => setTimeout(resolve, 1100));

      cache.cleanupExpired();

      expect(cache.getStats().size).toBe(0);
    });
  });

  describe("Session-Level Cache (createQueryCache)", () => {
    it("should create independent cache instances", () => {
      const cache1 = createQueryCache(10, 300);
      const cache2 = createQueryCache(10, 300);

      cache1.put("shared query", ["result from cache1"]);
      cache2.put("shared query", ["result from cache2"]);

      expect(cache1.get("shared query")).toEqual(["result from cache1"]);
      expect(cache2.get("shared query")).toEqual(["result from cache2"]);
    });

    it("should allow clearing session cache independently", () => {
      const sessionCache = createQueryCache(10, 300);

      sessionCache.put("session query", ["session result"]);
      expect(sessionCache.get("session query")).toEqual(["session result"]);

      sessionCache.clear();
      expect(sessionCache.get("session query")).toBeUndefined();
    });

    it("should not affect global cache when clearing session cache", () => {
      const globalCache = getQueryCache();
      const sessionCache = createQueryCache(10, 300);

      globalCache.put("test query", ["global result"]);
      sessionCache.put("test query", ["session result"]);

      sessionCache.clear();

      // Global cache should still have the entry
      expect(globalCache.get("test query")).toEqual(["global result"]);
    });
  });

  describe("Global Cache Management", () => {
    it("should clear global cache with clearGlobalQueryCache()", () => {
      const globalCache = getQueryCache();

      globalCache.put("global query", ["global result"]);
      expect(globalCache.get("global query")).toEqual(["global result"]);

      clearGlobalQueryCache();
      expect(globalCache.get("global query")).toBeUndefined();
    });

    it("should reset global cache with resetQueryCache()", () => {
      const cache1 = getQueryCache();
      cache1.put("persistent query", ["persistent result"]);

      resetQueryCache();

      const cache2 = getQueryCache();
      expect(cache2.get("persistent query")).toBeUndefined();
    });
  });

  describe("Cache Statistics", () => {
    it("should track hits and misses", () => {
      const cache = new QueryCache(10, 300);

      cache.put("test query", ["test result"]);

      cache.get("test query"); // Hit
      cache.get("test query"); // Hit
      cache.get("nonexistent"); // Miss

      const stats = cache.getStats();
      expect(stats.hits).toBe(2);
      expect(stats.misses).toBe(1);
    });

    it("should calculate hit rate correctly", () => {
      const cache = new QueryCache(10, 300);

      cache.put("test", ["result"]);

      cache.get("test"); // Hit
      cache.get("test"); // Hit
      cache.get("miss"); // Miss
      cache.get("miss2"); // Miss

      const stats = cache.getStats();
      expect(stats.hitRate).toBe(50); // 2 hits out of 4 total
    });
  });
});
