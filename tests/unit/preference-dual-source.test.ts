// Copyright 2026 OpenSourceClaw Contributors
// R2-T1/F2 — preference dual-source consistency. Semantic (`pref:<key>` tag)
// is the single live authority for current value AND enumeration; the version
// chain is append-only history only.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import { SemanticStorage } from "../../src/storage/semantic.js";
import { VersionChain } from "../../src/storage/version-chain.js";

describe("R2-T1 — preference dual-source consistency (F2)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-pref-dual-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  function prefIds(): string[] {
    return manager.listMemories({ layer: "preference" }).map((item) => item.id);
  }

  it("C2: update archives the NEW value — latest history equals the current value", () => {
    manager.store("light", "preference", [], { pref_key: "theme" });
    manager.store("dark", "preference", [], { pref_key: "theme" });

    const history = manager.getPreferenceHistory("theme");
    expect(history.map((v) => v.content)).toEqual(["light", "dark"]);
    expect(history[history.length - 1].content).toBe(manager.getPreference("theme")?.content);
  });

  it("C4: write → update → list / pref: get / history latest agree on content", () => {
    manager.store("light", "preference", [], { pref_key: "theme" });
    manager.store("dark", "preference", [], { pref_key: "theme" });

    expect(prefIds()).toContain("pref:theme");

    const viaGet = manager.getMemoryById("pref:theme");
    const history = manager.getPreferenceHistory("theme");
    const latest = history[history.length - 1];

    expect(viaGet?.text).toBe("dark");
    expect(latest.content).toBe("dark");
    expect(viaGet?.text).toBe(latest.content);
  });

  it("C3: every listed pref:<key> reads back through getMemoryById", () => {
    manager.store("dark", "preference", [], { pref_key: "theme" });
    manager.store("vim", "preference", [], { pref_key: "editor" });

    const ids = prefIds();
    expect(ids).toEqual(expect.arrayContaining(["pref:theme", "pref:editor"]));
    for (const id of ids) {
      const item = manager.getMemoryById(id);
      expect(item, id).not.toBeNull();
      expect(item!.text.length).toBeGreaterThan(0);
    }
  });

  it("C3 reverse: a semantic-only preference (no chain file) is listed and readable", () => {
    // Simulate a legacy/semantic-only record: MEMORY.md holds the value, the
    // version-chain directory has no file for the key.
    const semantic = new SemanticStorage(tmpDir);
    semantic.store({
      id: "sem_only_colors",
      timestamp: "2026-11-01T00:00:00.000Z",
      content: "solarized",
      tags: ["preference", "pref:colors"],
      metadata: { pref_key: "colors" },
    });

    expect(prefIds()).toContain("pref:colors");
    expect(manager.getMemoryById("pref:colors")?.text).toBe("solarized");
  });

  it("C3 reverse: a chain-only key is not listed and not readable (semantic authority)", () => {
    // Simulate split legacy data: the chain has a version, semantic has none.
    const chain = new VersionChain(tmpDir);
    chain.archive("orphan", {
      id: "pref_orphan",
      text: "ghost",
      memory_type: "preference",
      created_at: "2026-11-01T00:00:00.000Z",
      metadata: { pref_key: "orphan" },
      tags: ["preference"],
    });

    expect(prefIds()).not.toContain("pref:orphan");
    expect(manager.getMemoryById("pref:orphan")).toBeNull();
    // The chain stays readable as history — it is not a live read source.
    expect(manager.getPreferenceHistory("orphan")).toHaveLength(1);
  });

  it("rollback with a semantic record keeps live value and history in sync", () => {
    manager.store("light", "preference", [], { pref_key: "theme" });
    manager.store("dark", "preference", [], { pref_key: "theme" });

    const rolled = manager.rollbackPreference("theme", 1);
    expect(rolled?.content).toBe("light");
    expect(manager.getPreference("theme")?.content).toBe("light");
    expect(manager.getMemoryById("pref:theme")?.text).toBe("light");

    const history = manager.getPreferenceHistory("theme");
    expect(history[history.length - 1].content).toBe("light");
  });

  it("known boundary: rollback without a semantic record only appends history", () => {
    const chain = new VersionChain(tmpDir);
    chain.archive("ghost", {
      id: "pref_ghost",
      text: "v1",
      memory_type: "preference",
      created_at: "2026-11-01T00:00:00.000Z",
      metadata: { pref_key: "ghost" },
      tags: ["preference"],
    });

    const rolled = manager.rollbackPreference("ghost", 1);
    expect(rolled?.content).toBe("v1");
    expect(manager.getPreferenceHistory("ghost")).toHaveLength(2);
    // No semantic record → the live authority stays absent (documented boundary).
    expect(manager.getPreference("ghost")).toBeNull();
    expect(manager.getMemoryById("pref:ghost")).toBeNull();
    expect(prefIds()).not.toContain("pref:ghost");
  });

  it("memoryLinks('pref:<key>') is an explicit, documented exclusion (null)", () => {
    manager.store("dark", "preference", [], { pref_key: "theme" });
    expect(manager.memoryLinks("pref:theme")).toBeNull();
  });
});
