// Copyright 2026 OpenSourceClaw Contributors
// v7.10.0 (ADR-007): id-based transcript retrieval — live, archive, miss,
// dedupe, empty and path-traversal cases.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { TranscriptStorage } from "../../src/transcript/storage";

describe("TranscriptStorage.getTranscriptByIds (v7.10.0, ADR-007)", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-transcript-byid-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("returns a live transcript by id with full content", () => {
    const storage = new TranscriptStorage(tmpDir);
    storage.startSession("session-alpha", "api");
    storage.appendMessage({
      role: "user",
      content: "The evidence sentence lives here.",
      timestamp: "2026-11-16T10:00:00.000Z",
    });

    const matches = storage.getTranscriptByIds(["session-alpha"]);

    expect(matches).toHaveLength(1);
    expect(matches[0].sessionId).toBe("session-alpha");
    expect(matches[0].content).toContain("The evidence sentence lives here.");
    expect(matches[0].snippet.length).toBeLessThanOrEqual(200);
    expect(matches[0].score).toBe(1);
  });

  it("skips unknown ids without throwing and preserves the hit order", () => {
    const storage = new TranscriptStorage(tmpDir);
    storage.startSession("session-one", "api");
    storage.appendMessage({ role: "user", content: "one", timestamp: new Date().toISOString() });
    storage.startSession("session-two", "api");
    storage.appendMessage({ role: "user", content: "two", timestamp: new Date().toISOString() });

    const matches = storage.getTranscriptByIds(["missing", "session-two", "session-one"]);

    expect(matches.map((m) => m.sessionId)).toEqual(["session-two", "session-one"]);
  });

  it("resolves transcripts moved to _archive by soft delete", () => {
    const storage = new TranscriptStorage(tmpDir, { ttlDays: 7 });
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 10);
    const oldDateStr = oldDate.toISOString().slice(0, 10);
    const oldDir = path.join(tmpDir, "transcripts", oldDateStr);
    fs.mkdirSync(oldDir, { recursive: true });
    fs.writeFileSync(
      path.join(oldDir, "session-archived.md"),
      "archived evidence body",
      "utf-8",
    );

    expect(storage.cleanupExpired()).toBe(1);
    expect(storage.getTranscript("archived")).toBeNull();

    const matches = storage.getTranscriptByIds(["archived"]);

    expect(matches).toHaveLength(1);
    expect(matches[0].date).toBe(oldDateStr);
    expect(matches[0].content).toBe("archived evidence body");
  });

  it("returns [] for an empty id list", () => {
    const storage = new TranscriptStorage(tmpDir);
    expect(storage.getTranscriptByIds([])).toEqual([]);
  });

  it("deduplicates repeated ids", () => {
    const storage = new TranscriptStorage(tmpDir);
    storage.startSession("session-dup", "api");
    storage.appendMessage({ role: "user", content: "dup", timestamp: new Date().toISOString() });

    const matches = storage.getTranscriptByIds(["session-dup", "session-dup", " session-dup "]);

    expect(matches).toHaveLength(1);
  });

  it("rejects path separators and traversal ids", () => {
    const storage = new TranscriptStorage(tmpDir);
    expect(storage.getTranscriptByIds(["../etc/passwd", "a/b", "..", ""])).toEqual([]);
  });

  it("returns [] when transcript storage is disabled", () => {
    const storage = new TranscriptStorage(tmpDir, { enabled: false });
    expect(storage.getTranscriptByIds(["anything"])).toEqual([]);
  });
});
