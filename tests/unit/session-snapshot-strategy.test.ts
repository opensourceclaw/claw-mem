// Session Snapshot Strategy Unit Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { SessionSnapshotStrategy } from "../../src/storage/strategies/session-snapshot.js";
import { EpisodicStorage } from "../../src/storage/episodic.js";
import { VersionChain } from "../../src/storage/version-chain.js";
import type { StrategyContext, MemoryRecord } from "../../src/storage/strategy-registry.js";

describe("SessionSnapshotStrategy", () => {
  let tmpDir: string;
  let strategy: SessionSnapshotStrategy;
  let context: StrategyContext;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-snapshot-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    strategy = new SessionSnapshotStrategy();
    context = {
      episodic: new EpisodicStorage(tmpDir),
      semantic: {} as any,
      procedural: {} as any,
      entityIndex: null,
      versionChain: new VersionChain(tmpDir),
      workspace: tmpDir,
    };
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  function createRecord(sessionId: string, content: string): MemoryRecord {
    return {
      id: `snap_${Date.now()}`,
      text: content,
      memory_type: "session_snapshot",
      created_at: new Date().toISOString(),
      metadata: { session_id: sessionId },
      tags: ["session_snapshot"],
    };
  }

  it("stores new session snapshot", () => {
    const record = createRecord("session_1", "Session summary 1");
    const result = strategy.store(record, context);

    expect(result.strategy).toBe("session-snapshot");
    expect(result.overwritten).toBe(false);
  });

  it("overwrites existing snapshot for same session", () => {
    const record1 = createRecord("session_1", "Session summary 1");
    strategy.store(record1, context);

    const record2 = createRecord("session_1", "Session summary 2");
    const result = strategy.store(record2, context);

    expect(result.overwritten).toBe(true);
  });

  it("stores different sessions separately", () => {
    const record1 = createRecord("session_1", "Session 1 summary");
    const record2 = createRecord("session_2", "Session 2 summary");

    strategy.store(record1, context);
    strategy.store(record2, context);

    const results = strategy.retrieve("", { limit: 10 }, context);
    expect(results.length).toBe(2);
  });

  it("falls back to append without session_id", () => {
    const record: MemoryRecord = {
      id: "snap_no_session",
      text: "No session ID",
      memory_type: "session_snapshot",
      created_at: new Date().toISOString(),
      metadata: {}, // No session_id
      tags: ["session_snapshot"],
    };

    const result = strategy.store(record, context);
    expect(result.strategy).toBe("session-snapshot");
  });

  it("retrieves snapshots by query", () => {
    strategy.store(createRecord("s1", "Important meeting notes"), context);
    strategy.store(createRecord("s2", "Random discussion"), context);

    const results = strategy.retrieve("meeting", { limit: 10 }, context);
    expect(results.length).toBe(1);
    expect(results[0].text).toContain("meeting");
  });
});