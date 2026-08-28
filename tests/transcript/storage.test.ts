// Copyright 2026 OpenSourceClaw Contributors
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { TranscriptStorage, type TranscriptConfig } from "../../src/transcript/storage";
import { TranscriptFormatter, type TranscriptEntry, type TranscriptMetadata } from "../../src/transcript/formatter";

describe("TranscriptFormatter", () => {
  const formatter = new TranscriptFormatter();

  describe("formatMessage", () => {
    it("formats user message with timestamp and role", () => {
      const entry: TranscriptEntry = {
        role: "user",
        content: "Hello, world!",
        timestamp: "2026-06-29T10:30:45.000Z",
      };
      const result = formatter.formatMessage(entry);
      expect(result).toContain("[User]");
      expect(result).toContain("Hello, world!");
      expect(result).toMatch(/## \d{2}:\d{2}:\d{2} \[User\]/);
    });

    it("formats assistant message correctly", () => {
      const entry: TranscriptEntry = {
        role: "assistant",
        content: "Hi there!",
        timestamp: "2026-06-29T10:31:00.000Z",
      };
      const result = formatter.formatMessage(entry);
      expect(result).toContain("[Assistant]");
      expect(result).toContain("Hi there!");
    });
  });

  describe("buildHeader", () => {
    it("builds header with metadata", () => {
      const metadata: TranscriptMetadata = {
        session: "test-session-123",
        started: "2026-06-29T10:00:00.000Z",
        channel: "webchat",
      };
      const result = formatter.buildHeader(metadata);
      expect(result).toContain("session: test-session-123");
      expect(result).toContain("started: 2026-06-29T10:00:00.000Z");
      expect(result).toContain("channel: webchat");
    });
  });

  describe("formatTranscript", () => {
    it("formats full transcript with header and messages", () => {
      const metadata: TranscriptMetadata = {
        session: "test-session",
        started: "2026-06-29T10:00:00.000Z",
        channel: "cli",
      };
      const entries: TranscriptEntry[] = [
        { role: "user", content: "Question", timestamp: "2026-06-29T10:01:00.000Z" },
        { role: "assistant", content: "Answer", timestamp: "2026-06-29T10:02:00.000Z" },
      ];
      const result = formatter.formatTranscript(metadata, entries);
      expect(result).toContain("session: test-session");
      expect(result).toContain("[User]");
      expect(result).toContain("Question");
      expect(result).toContain("[Assistant]");
      expect(result).toContain("Answer");
    });
  });
});

describe("TranscriptStorage", () => {
  let tmpDir: string;
  let storage: TranscriptStorage;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-transcript-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe("initialization", () => {
    it("creates transcripts directory on init", () => {
      storage = new TranscriptStorage(tmpDir);
      expect(fs.existsSync(path.join(tmpDir, "transcripts"))).toBe(true);
    });

    it("respects enabled=false config", () => {
      storage = new TranscriptStorage(tmpDir, { enabled: false });
      expect(storage.isEnabled()).toBe(false);
    });

    it("uses default config when not specified", () => {
      storage = new TranscriptStorage(tmpDir);
      expect(storage.isEnabled()).toBe(true);
    });

    it("accepts custom TTL config", () => {
      storage = new TranscriptStorage(tmpDir, { ttlDays: 7 });
      // TTL is internal, we verify through cleanup behavior
      expect(storage.isEnabled()).toBe(true);
    });
  });

  describe("session management", () => {
    beforeEach(() => {
      storage = new TranscriptStorage(tmpDir);
    });

    it("starts session and creates file", () => {
      storage.startSession("test-session-123", "webchat");
      const today = new Date().toISOString().slice(0, 10);
      const filePath = path.join(tmpDir, "transcripts", today, "session-test-session-123.md");
      expect(fs.existsSync(filePath)).toBe(true);
    });

    it("ends session and clears state", () => {
      storage.startSession("test-session", "cli");
      storage.endSession();
      // After end, appending should not throw
      storage.appendMessage({
        role: "user",
        content: "Should be ignored",
        timestamp: new Date().toISOString(),
      });
      // No file should be created for this message
      const transcript = storage.getTranscript("test-session");
      expect(transcript).not.toContain("Should be ignored");
    });

    it("handles missing sessionId gracefully", () => {
      // Start session, then try to get non-existent session
      storage.startSession("session-a", "api");
      const result = storage.getTranscript("non-existent-session");
      expect(result).toBeNull();
    });
  });

  describe("message appending", () => {
    beforeEach(() => {
      storage = new TranscriptStorage(tmpDir);
    });

    it("appends user message", () => {
      storage.startSession("test-session", "api");
      storage.appendMessage({
        role: "user",
        content: "Hello from user",
        timestamp: new Date().toISOString(),
      });

      const transcript = storage.getTranscript("test-session");
      expect(transcript).toContain("[User]");
      expect(transcript).toContain("Hello from user");
    });

    it("appends assistant message", () => {
      storage.startSession("test-session", "api");
      storage.appendMessage({
        role: "assistant",
        content: "Hello from assistant",
        timestamp: new Date().toISOString(),
      });

      const transcript = storage.getTranscript("test-session");
      expect(transcript).toContain("[Assistant]");
      expect(transcript).toContain("Hello from assistant");
    });

    it("formats timestamps correctly", () => {
      storage.startSession("test-session", "api");
      const timestamp = "2026-06-29T15:30:45.000Z";
      storage.appendMessage({
        role: "user",
        content: "Test",
        timestamp,
      });

      const transcript = storage.getTranscript("test-session");
      expect(transcript).toMatch(/\d{2}:\d{2}:\d{2}/);
    });

    it("handles empty content", () => {
      storage.startSession("test-session", "api");
      storage.appendMessage({
        role: "user",
        content: "",
        timestamp: new Date().toISOString(),
      });

      const transcript = storage.getTranscript("test-session");
      expect(transcript).toContain("[User]");
    });
  });

  describe("querying", () => {
    beforeEach(() => {
      storage = new TranscriptStorage(tmpDir);
    });

    it("retrieves transcript by sessionId", () => {
      storage.startSession("session-retrieve", "api");
      storage.appendMessage({
        role: "user",
        content: "Retrieve test",
        timestamp: new Date().toISOString(),
      });

      const transcript = storage.getTranscript("session-retrieve");
      expect(transcript).toBeTruthy();
      expect(transcript).toContain("Retrieve test");
    });

    it("returns null for missing sessionId", () => {
      const result = storage.getTranscript("non-existent");
      expect(result).toBeNull();
    });

    it("searches transcripts by keyword", () => {
      storage.startSession("search-test-1", "api");
      storage.appendMessage({
        role: "user",
        content: "This is about TypeScript programming",
        timestamp: new Date().toISOString(),
      });

      storage.startSession("search-test-2", "api");
      storage.appendMessage({
        role: "user",
        content: "This is about Python programming",
        timestamp: new Date().toISOString(),
      });

      const results = storage.searchTranscripts("TypeScript");
      expect(results.length).toBeGreaterThan(0);
      expect(results[0].sessionId).toBe("search-test-1");
    });

    it("respects search limit", () => {
      // Create multiple matching transcripts
      for (let i = 0; i < 5; i++) {
        storage.startSession(`limit-test-${i}`, "api");
        storage.appendMessage({
          role: "user",
          content: `UniqueKeyword match number ${i}`,
          timestamp: new Date().toISOString(),
        });
      }

      const results = storage.searchTranscripts("UniqueKeyword", { limit: 2 });
      expect(results.length).toBe(2);
    });

    it("returns empty array when no matches found", () => {
      storage.startSession("no-match", "api");
      storage.appendMessage({
        role: "user",
        content: "Some content here",
        timestamp: new Date().toISOString(),
      });

      const results = storage.searchTranscripts("NonExistentKeyword12345");
      expect(results).toEqual([]);
    });
  });

  describe("cleanup", () => {
    it("removes expired directories", () => {
      storage = new TranscriptStorage(tmpDir, { ttlDays: 7 });

      // Create an old directory
      const oldDate = new Date();
      oldDate.setDate(oldDate.getDate() - 10);
      const oldDateStr = oldDate.toISOString().slice(0, 10);
      const oldDir = path.join(tmpDir, "transcripts", oldDateStr);
      fs.mkdirSync(oldDir, { recursive: true });
      fs.writeFileSync(path.join(oldDir, "session-old.md"), "old content");

      const deleted = storage.cleanupExpired();
      expect(deleted).toBe(1);
      expect(fs.existsSync(oldDir)).toBe(false);
    });

    it("keeps directories within TTL", () => {
      storage = new TranscriptStorage(tmpDir, { ttlDays: 30 });

      // Create a recent directory
      const recentDate = new Date().toISOString().slice(0, 10);
      const recentDir = path.join(tmpDir, "transcripts", recentDate);
      fs.mkdirSync(recentDir, { recursive: true });

      const deleted = storage.cleanupExpired();
      expect(deleted).toBe(0);
      expect(fs.existsSync(recentDir)).toBe(true);
    });

    it("handles missing transcripts directory", () => {
      // Remove transcripts directory
      const transcriptsDir = path.join(tmpDir, "transcripts");
      if (fs.existsSync(transcriptsDir)) {
        fs.rmSync(transcriptsDir, { recursive: true, force: true });
      }

      storage = new TranscriptStorage(tmpDir);
      const deleted = storage.cleanupExpired();
      expect(deleted).toBe(0);
    });
  });

  describe("getTranscriptPath", () => {
    beforeEach(() => {
      storage = new TranscriptStorage(tmpDir);
    });

    it("returns path for existing transcript", () => {
      storage.startSession("path-test", "api");
      const result = storage.getTranscriptPath("path-test");
      expect(result).toBeTruthy();
      expect(result).toContain("session-path-test.md");
    });

    it("returns null for non-existent transcript", () => {
      const result = storage.getTranscriptPath("non-existent");
      expect(result).toBeNull();
    });

    it("finds transcript when date not specified", () => {
      storage.startSession("date-test", "api");
      const today = new Date().toISOString().slice(0, 10);
      const result = storage.getTranscriptPath("date-test");
      expect(result).toContain(today);
    });
  });
});
