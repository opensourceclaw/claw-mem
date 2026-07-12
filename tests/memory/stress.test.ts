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
 * v6.37.0: Memory Stress Tests
 *
 * Tests for:
 * - Large volume writes to MemoryPool (verifies LRU keeps memory bounded)
 * - Long-running TranscriptStorage operations (verifies buffer stays limited)
 * - Multi-session QueryCache (verifies proper cleanup)
 * - Memory stability under load
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import { MemoryPool, AgentAgnosticMemory } from "../../src/memory";
import { TranscriptStorage } from "../../src/transcript/storage";
import { QueryCache, createQueryCache, clearGlobalQueryCache } from "../../src/retrieval/query_cache";
import type { TranscriptEntry } from "../../src/transcript/formatter";

describe("Memory Stress Tests", () => {
  const testWorkspace = "/tmp/claw-mem-stress-test";

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
    clearGlobalQueryCache();
  });

  describe("MemoryPool: Large Volume Writes", () => {
    it("should maintain stable memory with 10000+ writes", () => {
      const pool = new MemoryPool(undefined, 1000);

      // Write 10000 records (10x capacity)
      for (let i = 0; i < 10000; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          {
            content: `Large volume record ${i} with some additional content to make it more realistic`,
            tags: [`tag-${i % 100}`, `category-${i % 10}`],
          },
          `agent-${i % 5}`,
        ));
      }

      // Should never exceed maxSize
      expect(pool.getSize()).toBe(1000);
      expect(pool.getUsage().percent).toBe(100);
    });

    it("should handle concurrent-like store operations", () => {
      const pool = new MemoryPool(undefined, 100);

      // Simulate rapid concurrent writes
      for (let i = 0; i < 5000; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Concurrent ${i}`, tags: [] },
          "agent-1",
        ));
      }

      expect(pool.getSize()).toBe(100);
    });

    it("should maintain search performance under load", () => {
      const pool = new MemoryPool(undefined, 500);

      // Fill pool
      for (let i = 0; i < 1000; i++) {
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Searchable content ${i}`, tags: [] },
          "agent-1",
        ));
      }

      // Search should still work
      const results = pool.search("Searchable");
      expect(results.length).toBeGreaterThan(0);
      expect(results.length).toBeLessThanOrEqual(500);
    });
  });

  describe("TranscriptStorage: Long-Running Operations", () => {
    it("should maintain buffer limit with 1000+ messages", () => {
      const storage = new TranscriptStorage(testWorkspace);
      storage.startSession("stress-session-1");

      // Add 1000 messages (exceeds MAX_ENTRIES_BUFFER of 500)
      for (let i = 0; i < 1000; i++) {
        const entry: TranscriptEntry = {
          role: i % 2 === 0 ? "user" : "assistant",
          content: `Message ${i} with some content`,
          timestamp: new Date().toISOString(),
        };
        storage.appendMessage(entry);
      }

      // Buffer should be trimmed to 500
      expect(storage.getBufferSize()).toBe(500);
    });

    it("should handle multiple sessions without memory accumulation", () => {
      const storage = new TranscriptStorage(testWorkspace);

      // Create multiple sessions
      for (let session = 0; session < 10; session++) {
        storage.startSession(`stress-session-${session}`);

        for (let i = 0; i < 100; i++) {
          const entry: TranscriptEntry = {
            role: "user",
            content: `Session ${session} message ${i}`,
            timestamp: new Date().toISOString(),
          };
          storage.appendMessage(entry);
        }

        storage.endSession();
        expect(storage.getBufferSize()).toBe(0);
      }
    });
  });

  describe("QueryCache: Multi-Session Operations", () => {
    it("should handle multiple sessions with proper cleanup", () => {
      for (let session = 0; session < 5; session++) {
        const sessionCache = createQueryCache(100, 300);

        for (let i = 0; i < 50; i++) {
          sessionCache.put(`session-${session}-query-${i}`, [`result-${i}`]);
        }

        // Session cache should have correct size
        expect(sessionCache.getStats().size).toBe(50);

        // Clear session cache
        sessionCache.clear();
        expect(sessionCache.getStats().size).toBe(0);
      }
    });

    it("should not accumulate memory across sessions", () => {
      // Create and destroy multiple caches
      for (let i = 0; i < 10; i++) {
        const cache = createQueryCache(50, 300);

        for (let j = 0; j < 100; j++) {
          cache.put(`query-${i}-${j}`, [`result-${j}`]);
        }

        // Should be capped at 50
        expect(cache.getStats().size).toBe(50);
      }
    });
  });

  describe("Combined Stress Test", () => {
    it("should maintain memory stability with all components under load", () => {
      const pool = new MemoryPool(undefined, 200);
      const storage = new TranscriptStorage(testWorkspace);
      const cache = createQueryCache(100, 300);

      storage.startSession("combined-stress");

      // Combined operations
      for (let i = 0; i < 500; i++) {
        // MemoryPool
        pool.store(AgentAgnosticMemory.to_shared_format(
          { content: `Combined test ${i}`, tags: [] },
          "agent-1",
        ));

        // TranscriptStorage
        const entry: TranscriptEntry = {
          role: i % 2 === 0 ? "user" : "assistant",
          content: `Combined message ${i}`,
          timestamp: new Date().toISOString(),
        };
        storage.appendMessage(entry);

        // QueryCache
        cache.put(`combined-query-${i}`, [`result-${i}`]);
      }

      // All should be bounded
      expect(pool.getSize()).toBe(200);
      expect(storage.getBufferSize()).toBe(500);
      expect(cache.getStats().size).toBe(100);

      storage.endSession();
    });
  });
});