// MemoryManager Strategy Integration Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";

describe("MemoryManager Strategy Integration", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-strat-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("stores with episodic strategy by default", () => {
    const success = manager.store("Test episodic content", "episodic");
    expect(success).toBe(true);
    expect(manager.getStoreStrategy("episodic")).toBe("episodic");
  });

  it("stores session_snapshot with overwrite strategy", () => {
    const success = manager.store(
      "Session snapshot content",
      "session_snapshot",
      [],
      { session_id: "session_123" }
    );
    expect(success).toBe(true);
    expect(manager.getStoreStrategy("session_snapshot")).toBe("session-snapshot");
  });

  it("stores fact with entity indexing", () => {
    const success = manager.store(
      "claw-mem v6.31.0 adds strategies",
      "fact",
      ["dev"]
    );
    expect(success).toBe(true);
    expect(manager.getStoreStrategy("fact")).toBe("fact");

    // Entity should be indexed
    const result = manager.entitySearch("clawmem");
    expect(result).not.toBeNull();
  });

  it("stores preference with version chain", () => {
    const success = manager.store(
      "dark",
      "preference",
      [],
      { pref_key: "theme" }
    );
    expect(success).toBe(true);
    expect(manager.getStoreStrategy("preference")).toBe("preference");

    const history = manager.getPreferenceHistory("theme");
    expect(history.length).toBe(1);
  });

  it("falls back to episodic for unknown type", () => {
    const success = manager.store("Unknown type content", "unknown_type");
    expect(success).toBe(true);
    expect(manager.getStoreStrategy("unknown_type")).toBe("episodic");
  });

  it("lists all strategies", () => {
    const strategies = manager.listStrategies();
    expect(strategies.length).toBeGreaterThan(0);
    expect(strategies.find(s => s.name === "episodic")).toBeDefined();
    expect(strategies.find(s => s.name === "fact")).toBeDefined();
    expect(strategies.find(s => s.name === "preference")).toBeDefined();
  });

  it("gets preference history", () => {
    manager.store("light", "preference", [], { pref_key: "theme" });
    manager.store("dark", "preference", [], { pref_key: "theme" });

    const history = manager.getPreferenceHistory("theme");
    expect(history.length).toBe(2);
  });

  it("rollbacks preference", () => {
    manager.store("light", "preference", [], { pref_key: "theme" });
    manager.store("dark", "preference", [], { pref_key: "theme" });

    const rolledBack = manager.rollbackPreference("theme", 1);
    expect(rolledBack).not.toBeNull();
    expect(rolledBack?.content).toBe("light");
    expect(rolledBack?.metadata?.rollback_from).toBe(1);
  });
});