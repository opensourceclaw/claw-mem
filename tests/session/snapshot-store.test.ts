// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import { SnapshotStore } from "../../src/session/snapshot-store.js";
import { SessionSnapshot } from "../../src/session/snapshot-types.js";

function makeSnapshot(overrides: Partial<SessionSnapshot> = {}): SessionSnapshot {
  const ts = Date.now();
  return {
    sessionId: "sess_test",
    startedAt: ts - 3600_000,
    lastActiveAt: ts,
    turnCount: 5,
    currentTopic: "Testing Session Snapshot",
    recentDecisions: ["Use vitest", "Add 10 tests"],
    pendingItems: ["Finish snapshot-store tests"],
    keyEntities: ["claw-mem", "session"],
    isClosed: false,
    ...overrides,
  };
}

describe("SnapshotStore", () => {
  let tmpDir: string;
  let manager: MemoryManager;
  let store: SnapshotStore;

  beforeEach(() => {
    resetMemoryManager();
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-snap-"));
    manager = new MemoryManager({ workspace: tmpDir });
    store = new SnapshotStore(manager, { maxAgeHours: 48 });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  // 1
  it("store() writes successfully, returns { stored:true, id }", () => {
    const snap = makeSnapshot();
    const result = store.store(snap);
    expect(result.stored).toBe(true);
    expect(result.id).toMatch(/^snap_\d+$/);
  });

  // 2
  it("getLatest(sessionId) returns latest by lastActiveAt after multiple writes", () => {
    const old = makeSnapshot({ lastActiveAt: Date.now() - 10000, turnCount: 1 });
    const recent = makeSnapshot({ lastActiveAt: Date.now(), turnCount: 10 });
    store.store(old);
    store.store(recent);
    const latest = store.getLatest("sess_test");
    expect(latest).not.toBeNull();
    expect(latest!.turnCount).toBe(10);
  });

  // 3
  it("getLatest() without sessionId returns global latest", () => {
    const sessA = makeSnapshot({ sessionId: "sess_a", lastActiveAt: Date.now() - 5000 });
    const sessB = makeSnapshot({ sessionId: "sess_b", lastActiveAt: Date.now() });
    store.store(sessA);
    store.store(sessB);
    const latest = store.getLatest();
    expect(latest).not.toBeNull();
    expect(latest!.sessionId).toBe("sess_b");
  });

  // 4
  it("getLatest() returns null for nonexistent session", () => {
    const result = store.getLatest("nonexistent");
    expect(result).toBeNull();
  });

  // 5
  it("close() marks latest snapshot isClosed=true", () => {
    store.store(makeSnapshot({ sessionId: "sess_c" }));
    const result = store.close("sess_c");
    expect(result.closed).toBe(true);
    const latest = store.getLatest("sess_c");
    expect(latest).not.toBeNull();
    expect(latest!.isClosed).toBe(true);
  });

  // 6
  it("close() returns { closed:false } for nonexistent session", () => {
    const result = store.close("nonexistent");
    expect(result.closed).toBe(false);
  });

  // 7
  it("getUnclosed() returns only unclosed, unexpired snapshots", () => {
    store.store(makeSnapshot({ sessionId: "open_a", isClosed: false, lastActiveAt: Date.now() }));
    store.store(makeSnapshot({ sessionId: "closed_b", isClosed: true, lastActiveAt: Date.now() }));
    const result = store.getUnclosed();
    const ids = result.map((s) => s.sessionId);
    expect(ids).toContain("open_a");
    expect(ids).not.toContain("closed_b");
  });

  // 8
  it("getUnclosed() returns only latest per session", () => {
    store.store(makeSnapshot({ sessionId: "dup", turnCount: 1, lastActiveAt: Date.now() - 1000 }));
    store.store(makeSnapshot({ sessionId: "dup", turnCount: 2, lastActiveAt: Date.now() }));
    const result = store.getUnclosed();
    const dupSessions = result.filter((s) => s.sessionId === "dup");
    expect(dupSessions.length).toBe(1);
    expect(dupSessions[0].turnCount).toBe(2);
  });

  // 9
  it("getUnclosed() excludes expired snapshots", () => {
    // Create a store with 1ms max age — everything should be expired
    const strictStore = new SnapshotStore(manager, { maxAgeHours: 0 });
    store.store(makeSnapshot({ sessionId: "fresh", isClosed: false }));
    strictStore.store(makeSnapshot({ sessionId: "fresh_expired", isClosed: false }));
    const result = strictStore.getUnclosed();
    // With maxAgeHours=0 (0ms), no snapshot should pass the cutoff
    expect(result.length).toBe(0);
  });

  // 10
  it("enforceSizeLimit truncates snapshots exceeding 2KB", () => {
    const huge = makeSnapshot({
      pendingItems: Array.from({ length: 50 }, (_, i) => `item ${i}`.padEnd(200, "x")),
      recentDecisions: Array.from({ length: 20 }, (_, i) => `decision ${i}`.padEnd(200, "y")),
      keyEntities: Array.from({ length: 30 }, (_, i) => `entity ${i}`.padEnd(200, "z")),
    });
    const result = store.store(huge);
    expect(result.stored).toBe(true);
    const saved = store.getLatest("sess_test");
    expect(saved).not.toBeNull();
    const size = Buffer.byteLength(JSON.stringify(saved), "utf-8");
    expect(size).toBeLessThanOrEqual(2048);
  });
});
