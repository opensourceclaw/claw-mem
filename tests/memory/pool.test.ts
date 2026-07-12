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
 * v6.37.0: Memory Leak Regression Tests for MemoryPool
 *
 * Tests for:
 * - Capacity limit enforcement (_maxSize)
 * - LRU eviction behavior (oldest removed first)
 * - Monitoring methods (getSize, getUsage)
 */

import { describe, it, expect, beforeEach } from "vitest";
import { MemoryPool, AgentAgnosticMemory } from "../../src/memory";

describe("MemoryPool: Memory Leak Regression Tests", () => {
  describe("Capacity Limit (_maxSize)", () => {
    it("should enforce default max size of 10000 records", () => {
      const pool = new MemoryPool();

      // Default max size should be 10000
      expect(pool.getUsage().max).toBe(10000);
    });

    it("should accept custom max size in constructor", () => {
      const pool = new MemoryPool(undefined, 100);
      expect(pool.getUsage().max).toBe(100);
    });

    it("should enforce capacity limit when storing records", () => {
      const pool = new MemoryPool(undefined, 10);

      // Store 15 records (exceeds capacity)
      for (let i = 0; i < 15; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Record ${i}`, tags: [`tag-${i}`] },
          `agent-${i % 3}`,
        ));
      }

      // Should have exactly maxSize records
      expect(pool.getSize()).toBe(10);
    });
  });

  describe("LRU Eviction Behavior", () => {
    it("should remove oldest records when at capacity (FIFO for simplicity)", () => {
      const pool = new MemoryPool(undefined, 5);

      // Store records 0-4
      for (let i = 0; i < 5; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Record ${i}`, tags: [] },
          "agent-1",
        ));
      }

      expect(pool.getSize()).toBe(5);

      // Store record 5, should evict record 0
      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "Record 5", tags: [] },
        "agent-1",
      ));

      expect(pool.getSize()).toBe(5);

      // Record 0 should be evicted
      const results = pool.search("Record 0");
      expect(results.length).toBe(0);

      // Record 5 should exist
      const results5 = pool.search("Record 5");
      expect(results5.length).toBe(1);
    });

    it("should maintain most recent records after multiple evictions", () => {
      const pool = new MemoryPool(undefined, 3);

      // Store records 0-9 (should only keep 7, 8, 9)
      for (let i = 0; i < 10; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Content ${i}`, tags: [] },
          "agent-1",
        ));
      }

      expect(pool.getSize()).toBe(3);

      // Only records 7, 8, 9 should exist
      expect(pool.search("Content 7").length).toBe(1);
      expect(pool.search("Content 8").length).toBe(1);
      expect(pool.search("Content 9").length).toBe(1);

      // Older records should be evicted
      expect(pool.search("Content 0").length).toBe(0);
      expect(pool.search("Content 5").length).toBe(0);
    });

    it("should handle rapid store operations without memory growth", () => {
      const pool = new MemoryPool(undefined, 100);

      // Rapidly store 1000 records
      for (let i = 0; i < 1000; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Rapid record ${i}`, tags: [] },
          "agent-1",
        ));
      }

      // Should never exceed maxSize
      expect(pool.getSize()).toBe(100);
      expect(pool.getUsage().percent).toBeLessThanOrEqual(100);
    });
  });

  describe("Monitoring Methods", () => {
    it("should return correct size with getSize()", () => {
      const pool = new MemoryPool();

      expect(pool.getSize()).toBe(0);

      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "Test", tags: [] },
        "agent-1",
      ));

      expect(pool.getSize()).toBe(1);
    });

    it("should return correct usage statistics with getUsage()", () => {
      const pool = new MemoryPool(undefined, 100);

      // Initially empty
      let usage = pool.getUsage();
      expect(usage.current).toBe(0);
      expect(usage.max).toBe(100);
      expect(usage.percent).toBe(0);

      // Add 25 records
      for (let i = 0; i < 25; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Test ${i}`, tags: [] },
          "agent-1",
        ));
      }

      usage = pool.getUsage();
      expect(usage.current).toBe(25);
      expect(usage.max).toBe(100);
      expect(usage.percent).toBe(25);
    });

    it("should handle cleanup with maxRecords option", () => {
      const pool = new MemoryPool(undefined, 100);

      // Store 50 records
      for (let i = 0; i < 50; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Test ${i}`, tags: [] },
          "agent-1",
        ));
      }

      expect(pool.getSize()).toBe(50);

      // Cleanup to keep only 20 newest
      const removed = pool.cleanup({ maxRecords: 20 });

      expect(pool.getSize()).toBe(20);
      expect(removed).toBe(30);
    });
  });

  describe("Edge Cases", () => {
    it("should handle maxSize of 1", () => {
      const pool = new MemoryPool(undefined, 1);

      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "First", tags: [] },
        "agent-1",
      ));
      expect(pool.getSize()).toBe(1);

      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "Second", tags: [] },
        "agent-1",
      ));
      expect(pool.getSize()).toBe(1);
      expect(pool.search("First").length).toBe(0);
      expect(pool.search("Second").length).toBe(1);
    });

    it("should handle store after clear", () => {
      const pool = new MemoryPool(undefined, 10);

      for (let i = 0; i < 10; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Test ${i}`, tags: [] },
          "agent-1",
        ));
      }

      pool.clear();
      expect(pool.getSize()).toBe(0);

      // Should be able to store again
      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "After clear", tags: [] },
        "agent-1",
      ));
      expect(pool.getSize()).toBe(1);
    });
  });
});
