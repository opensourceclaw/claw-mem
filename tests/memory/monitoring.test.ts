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
 * v6.37.0: Memory Monitoring Tests
 *
 * Tests for:
 * - getSize() / getUsage() on MemoryPool
 * - getBufferSize() / clearBuffer() on TranscriptStorage
 * - getStats() on QueryCache
 * - flush() operations
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import { MemoryPool, AgentAgnosticMemory } from "../../src/memory";
import { TranscriptStorage } from "../../src/transcript/storage";
import { QueryCache, createQueryCache } from "../../src/retrieval/query_cache";
import type { TranscriptEntry } from "../../src/transcript/formatter";

describe("Memory Monitoring Tests", () => {
  const testWorkspace = "/tmp/claw-mem-monitoring-test";

  beforeEach(() => {
    if (fs.existsSync(testWorkspace)) {
      fs.rmSync(testWorkspace, { recursive: true, force: true });
    }
    fs.mkdirSync(testWorkspace, { recursive: true });
  });

  afterEach(() => {
    if (fs.existsSync(testWorkspace)) {
      fs.rmSync(testWorkspace, { recursive: true, force: true });
    }
  });

  describe("MemoryPool Monitoring", () => {
    it("should return correct size with getSize()", () => {
      const pool = new MemoryPool();

      expect(pool.getSize()).toBe(0);

      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "Test 1", tags: [] },
        "agent-1",
      ));
      expect(pool.getSize()).toBe(1);

      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "Test 2", tags: [] },
        "agent-1",
      ));
      expect(pool.getSize()).toBe(2);
    });

    it("should return correct usage statistics with getUsage()", () => {
      const pool = new MemoryPool(undefined, 100);

      // Empty pool
      let usage = pool.getUsage();
      expect(usage.current).toBe(0);
      expect(usage.max).toBe(100);
      expect(usage.percent).toBe(0);

      // Partially filled
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

      // Fully filled
      for (let i = 25; i < 100; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Test ${i}`, tags: [] },
          "agent-1",
        ));
      }

      usage = pool.getUsage();
      expect(usage.current).toBe(100);
      expect(usage.percent).toBe(100);
    });

    it("should reflect eviction in usage statistics", () => {
      const pool = new MemoryPool(undefined, 10);

      // Fill to capacity
      for (let i = 0; i < 10; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Test ${i}`, tags: [] },
          "agent-1",
        ));
      }
      expect(pool.getUsage().current).toBe(10);

      // Add more, should trigger eviction
      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: "Overflow", tags: [] },
        "agent-1",
      ));
      expect(pool.getUsage().current).toBe(10);
    });
  });

  describe("TranscriptStorage Monitoring", () => {
    function createEntry(content: string): TranscriptEntry {
      return {
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
    }

    it("should return correct buffer size with getBufferSize()", () => {
      const storage = new TranscriptStorage(testWorkspace);
      storage.startSession("monitoring-session-1");

      expect(storage.getBufferSize()).toBe(0);

      storage.appendMessage(createEntry("Message 1"));
      expect(storage.getBufferSize()).toBe(1);

      storage.appendMessage(createEntry("Message 2"));
      expect(storage.getBufferSize()).toBe(2);
    });

    it("should clear buffer with clearBuffer()", () => {
      const storage = new TranscriptStorage(testWorkspace);
      storage.startSession("monitoring-session-2");

      for (let i = 0; i < 10; i++) {
        storage.appendMessage(createEntry(`Message ${i}`));
      }

      expect(storage.getBufferSize()).toBe(10);

      storage.clearBuffer();
      expect(storage.getBufferSize()).toBe(0);
    });

    it("should flush and optionally clear with flush()", () => {
      const storage = new TranscriptStorage(testWorkspace);
      storage.startSession("monitoring-session-3");

      for (let i = 0; i < 5; i++) {
        storage.appendMessage(createEntry(`Message ${i}`));
      }

      // Flush without clearing
      storage.flush(false);
      expect(storage.getBufferSize()).toBe(5);

      // Flush with clearing
      storage.flush(true);
      expect(storage.getBufferSize()).toBe(0);
    });

    it("should track buffer after session operations", () => {
      const storage = new TranscriptStorage(testWorkspace);

      // Session 1
      storage.startSession("monitoring-session-4a");
      for (let i = 0; i < 20; i++) {
        storage.appendMessage(createEntry(`Session 1 Message ${i}`));
      }
      expect(storage.getBufferSize()).toBe(20);

      // Start new session should reset
      storage.startSession("monitoring-session-4b");
      expect(storage.getBufferSize()).toBe(0);

      // End session should clear
      for (let i = 0; i < 10; i++) {
        storage.appendMessage(createEntry(`Session 2 Message ${i}`));
      }
      expect(storage.getBufferSize()).toBe(10);

      storage.endSession();
      expect(storage.getBufferSize()).toBe(0);
    });
  });

  describe("QueryCache Monitoring", () => {
    it("should return correct statistics with getStats()", () => {
      const cache = new QueryCache(50, 300);

      // Empty cache
      let stats = cache.getStats();
      expect(stats.size).toBe(0);
      expect(stats.maxSize).toBe(50);
      expect(stats.hits).toBe(0);
      expect(stats.misses).toBe(0);

      // Add entries
      for (let i = 0; i < 25; i++) {
        cache.put(`query ${i}`, [`result ${i}`]);
      }

      stats = cache.getStats();
      expect(stats.size).toBe(25);
      expect(stats.maxSize).toBe(50);

      // Access some entries
      cache.get("query 1");
      cache.get("query 2");
      cache.get("nonexistent");

      stats = cache.getStats();
      expect(stats.hits).toBe(2);
      expect(stats.misses).toBe(1);
      expect(stats.hitRate).toBeCloseTo(66.67, 1); // 2/3 * 100
    });

    it("should track eviction in statistics", () => {
      const cache = new QueryCache(10, 300);

      // Fill to capacity
      for (let i = 0; i < 10; i++) {
        cache.put(`query ${i}`, [`result ${i}`]);
      }
      expect(cache.getStats().size).toBe(10);

      // Add more, should trigger eviction
      for (let i = 10; i < 20; i++) {
        cache.put(`query ${i}`, [`result ${i}`]);
      }

      // Size should still be at max
      expect(cache.getStats().size).toBe(10);
    });

    it("should reset statistics on clear()", () => {
      const cache = new QueryCache(10, 300);

      cache.put("query 1", ["result 1"]);
      cache.get("query 1");
      cache.get("nonexistent");

      expect(cache.getStats().size).toBe(1);
      expect(cache.getStats().hits).toBe(1);
      expect(cache.getStats().misses).toBe(1);

      cache.clear();

      expect(cache.getStats().size).toBe(0);
      expect(cache.getStats().hits).toBe(0);
      expect(cache.getStats().misses).toBe(0);
    });
  });

  describe("Combined Monitoring", () => {
    function createEntry(content: string): TranscriptEntry {
      return {
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
    }

    it("should provide consistent monitoring across all components", () => {
      const pool = new MemoryPool(undefined, 50);
      const storage = new TranscriptStorage(testWorkspace);
      const cache = createQueryCache(20, 300);

      storage.startSession("combined-monitoring");

      // Add data to all components
      for (let i = 0; i < 30; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Test ${i}`, tags: [] },
          "agent-1",
        ));

        storage.appendMessage(createEntry(`Message ${i}`));

        cache.put(`query ${i}`, [`result ${i}`]);
      }

      // Check all sizes
      expect(pool.getSize()).toBe(30);
      expect(storage.getBufferSize()).toBe(30);
      expect(cache.getStats().size).toBe(20); // Limited by maxSize

      // Clear all
      pool.clear();
      storage.clearBuffer();
      cache.clear();

      expect(pool.getSize()).toBe(0);
      expect(storage.getBufferSize()).toBe(0);
      expect(cache.getStats().size).toBe(0);
    });
  });
});