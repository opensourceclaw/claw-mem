// Preference Strategy Unit Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { PreferenceStrategy } from "../../src/storage/strategies/preference.js";
import { SemanticStorage } from "../../src/storage/semantic.js";
import { VersionChain } from "../../src/storage/version-chain.js";
import type { StrategyContext, MemoryRecord } from "../../src/storage/strategy-registry.js";

describe("PreferenceStrategy", () => {
  let tmpDir: string;
  let strategy: PreferenceStrategy;
  let context: StrategyContext;
  let semanticStorage: SemanticStorage;
  let versionChain: VersionChain;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-pref-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    semanticStorage = new SemanticStorage(tmpDir);
    versionChain = new VersionChain(tmpDir);
    strategy = new PreferenceStrategy();
    context = {
      episodic: {} as any,
      semantic: semanticStorage,
      procedural: {} as any,
      entityIndex: null,
      versionChain,
      workspace: tmpDir,
    };
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  function createPref(prefKey: string, value: string): MemoryRecord {
    return {
      id: `pref_${Date.now()}`,
      text: value,
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: { pref_key: prefKey },
      tags: ["preference"],
    };
  }

  it("stores new preference", () => {
    const record = createPref("theme", "dark");
    const result = strategy.store(record, context);

    expect(result.strategy).toBe("preference");
    expect(result.version).toBe(1);
  });

  it("overwrites existing preference with version chain", () => {
    strategy.store(createPref("theme", "light"), context);
    const result = strategy.store(createPref("theme", "dark"), context);

    expect(result.version).toBe(2);

    const history = versionChain.getHistory("theme");
    expect(history.length).toBe(2);
  });

  it("retrieves preference by pref_key", () => {
    strategy.store(createPref("editor", "vscode"), context);

    const results = strategy.retrieve("pref_key:editor", { limit: 10 }, context);
    expect(results.length).toBe(1);
    expect(results[0].text).toBe("vscode");
  });

  it("falls back to append without pref_key", () => {
    const record: MemoryRecord = {
      id: "pref_no_key",
      text: "No key",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {}, // No pref_key
      tags: ["preference"],
    };

    const result = strategy.store(record, context);
    expect(result.strategy).toBe("preference");
  });

  it("retrieves preferences by general query", () => {
    strategy.store(createPref("theme", "dark mode enabled"), context);
    strategy.store(createPref("editor", "vim keybindings"), context);

    const results = strategy.retrieve("dark", { limit: 10 }, context);
    expect(results.length).toBe(1);
    expect(results[0].text).toContain("dark");
  });

  it("returns stats", () => {
    strategy.store(createPref("theme", "dark"), context);
    strategy.store(createPref("editor", "vscode"), context);

    const stats = strategy.getStats(context);
    expect(stats.name).toBe("preference");
    expect(stats.memoryCount).toBeGreaterThanOrEqual(2);
  });
});