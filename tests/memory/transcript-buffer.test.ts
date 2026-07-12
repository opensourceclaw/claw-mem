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
 * v6.37.0: Memory Leak Regression Tests for TranscriptStorage
 *
 * Tests for:
 * - Buffer capacity limit (MAX_ENTRIES_BUFFER = 500)
 * - Buffer trimming behavior
 * - Monitoring methods (getBufferSize, clearBuffer, flush)
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import { TranscriptStorage } from "../../src/transcript/storage";
import type { TranscriptEntry } from "../../src/transcript/formatter";

describe("TranscriptStorage: Memory Leak Regression Tests", () => {
  const testWorkspace = "/tmp/claw-mem-test-transcript-buffer";
  let storage: TranscriptStorage;

  beforeEach(() => {
    // Clean up and create test workspace
    if (fs.existsSync(testWorkspace)) {
      fs.rmSync(testWorkspace, { recursive: true, force: true });
    }
    fs.mkdirSync(testWorkspace, { recursive: true });
    storage = new TranscriptStorage(testWorkspace);
  });

  afterEach(() => {
    // Clean up test workspace
    if (fs.existsSync(testWorkspace)) {
      fs.rmSync(testWorkspace, { recursive: true, force: true });
    }
  });

  function createEntry(role: "user" | "assistant", content: string): TranscriptEntry {
    return {
      role,
      content,
      timestamp: new Date().toISOString(),
    };
  }

  describe("Buffer Capacity Limit", () => {
    it("should enforce MAX_ENTRIES_BUFFER limit (500)", () => {
      storage.startSession("test-session-1");

      // The limit is 500, but we'll test with fewer for speed
      // Verify initial buffer is empty
      expect(storage.getBufferSize()).toBe(0);

      // Add entries up to the limit
      for (let i = 0; i < 500; i++) {
        storage.appendMessage(createEntry("user", `Message ${i}`));
      }

      expect(storage.getBufferSize()).toBe(500);
    });

    it("should trim buffer when exceeding limit", () => {
      storage.startSession("test-session-2");

      // Add more entries than the limit
      for (let i = 0; i < 600; i++) {
        storage.appendMessage(createEntry("user", `Message ${i}`));
      }

      // Buffer should be trimmed to 500 (most recent)
      expect(storage.getBufferSize()).toBe(500);
    });

    it("should keep most recent entries when trimming", () => {
      storage.startSession("test-session-3");

      // Add 600 entries
      for (let i = 0; i < 600; i++) {
        storage.appendMessage(createEntry("user", `Unique content ${i}`));
      }

      // Get entries and verify the most recent are kept
      const entries = storage.getEntries();
      expect(entries.length).toBe(500);

      // First entry should be "Unique content 100" (oldest kept)
      // Last entry should be "Unique content 599" (newest)
      expect(entries[0].content).toBe("Unique content 100");
      expect(entries[entries.length - 1].content).toBe("Unique content 599");
    });
  });

  describe("Monitoring Methods", () => {
    it("should return correct buffer size with getBufferSize()", () => {
      storage.startSession("test-session-4");

      expect(storage.getBufferSize()).toBe(0);

      storage.appendMessage(createEntry("user", "Hello"));
      expect(storage.getBufferSize()).toBe(1);

      storage.appendMessage(createEntry("assistant", "Hi there"));
      expect(storage.getBufferSize()).toBe(2);
    });

    it("should clear buffer with clearBuffer()", () => {
      storage.startSession("test-session-5");

      for (let i = 0; i < 10; i++) {
        storage.appendMessage(createEntry("user", `Message ${i}`));
      }

      expect(storage.getBufferSize()).toBe(10);

      storage.clearBuffer();
      expect(storage.getBufferSize()).toBe(0);
    });

    it("should flush and optionally clear buffer", () => {
      storage.startSession("test-session-6");

      for (let i = 0; i < 10; i++) {
        storage.appendMessage(createEntry("user", `Message ${i}`));
      }

      expect(storage.getBufferSize()).toBe(10);

      // Flush without clearing
      storage.flush(false);
      expect(storage.getBufferSize()).toBe(10);

      // Flush with clearing
      storage.flush(true);
      expect(storage.getBufferSize()).toBe(0);
    });
  });

  describe("Session Management", () => {
    it("should reset buffer when starting new session", () => {
      storage.startSession("test-session-7");

      for (let i = 0; i < 50; i++) {
        storage.appendMessage(createEntry("user", `Message ${i}`));
      }

      expect(storage.getBufferSize()).toBe(50);

      // Start a new session
      storage.startSession("test-session-8");
      expect(storage.getBufferSize()).toBe(0);
    });

    it("should clear buffer on endSession", () => {
      storage.startSession("test-session-9");

      for (let i = 0; i < 30; i++) {
        storage.appendMessage(createEntry("user", `Message ${i}`));
      }

      expect(storage.getBufferSize()).toBe(30);

      storage.endSession();
      expect(storage.getBufferSize()).toBe(0);
    });
  });

  describe("Edge Cases", () => {
    it("should handle rapid append operations", () => {
      storage.startSession("test-session-10");

      // Rapidly append 1000 messages
      for (let i = 0; i < 1000; i++) {
        storage.appendMessage(createEntry("user", `Rapid message ${i}`));
      }

      // Should never exceed MAX_ENTRIES_BUFFER
      expect(storage.getBufferSize()).toBeLessThanOrEqual(500);
    });

    it("should handle mixed user/assistant messages", () => {
      storage.startSession("test-session-11");

      for (let i = 0; i < 100; i++) {
        storage.appendMessage(createEntry("user", `User message ${i}`));
        storage.appendMessage(createEntry("assistant", `Assistant response ${i}`));
      }

      expect(storage.getBufferSize()).toBe(200);
    });

    it("should handle disabled storage gracefully", () => {
      const disabledStorage = new TranscriptStorage(testWorkspace, { enabled: false });

      disabledStorage.startSession("disabled-session");
      disabledStorage.appendMessage(createEntry("user", "This should be ignored"));

      expect(disabledStorage.getBufferSize()).toBe(0);
      expect(disabledStorage.isEnabled()).toBe(false);
    });
  });
});
