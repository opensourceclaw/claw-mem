// Version Chain Unit Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { VersionChain } from "../../src/storage/version-chain.js";
import { SemanticStorage } from "../../src/storage/semantic.js";

describe("VersionChain", () => {
  let tmpDir: string;
  let versionChain: VersionChain;
  let semanticStorage: SemanticStorage;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-version-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    versionChain = new VersionChain(tmpDir);
    semanticStorage = new SemanticStorage(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("archives versions", () => {
    const version = versionChain.archive("theme", {
      id: "pref_1",
      text: "dark",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    expect(version).toBe(1);

    const history = versionChain.getHistory("theme");
    expect(history.length).toBe(1);
    expect(history[0].content).toBe("dark");
  });

  it("gets version history", () => {
    versionChain.archive("theme", {
      id: "pref_1",
      text: "light",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    versionChain.archive("theme", {
      id: "pref_1",
      text: "dark",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    const history = versionChain.getHistory("theme");
    expect(history.length).toBe(2);
    expect(history[0].content).toBe("light");
    expect(history[1].content).toBe("dark");
  });

  it("gets specific version", () => {
    versionChain.archive("editor", {
      id: "pref_1",
      text: "vscode",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    const v1 = versionChain.getVersion("editor", 1);
    expect(v1?.content).toBe("vscode");
  });

  it("handles missing preference file", () => {
    const history = versionChain.getHistory("nonexistent");
    expect(history).toEqual([]);
  });

  it("sanitizes pref_key for file path", () => {
    versionChain.archive("theme/user preference", {
      id: "pref_1",
      text: "test",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    // Should create a sanitized file
    const history = versionChain.getHistory("theme/user preference");
    expect(history.length).toBe(1);
  });

  it("rollback creates new version with old content", () => {
    // Create version 1
    versionChain.archive("theme", {
      id: "pref_1",
      text: "light",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    // Create version 2
    versionChain.archive("theme", {
      id: "pref_1",
      text: "dark",
      memory_type: "preference",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: [],
    });

    // Store preference in semantic
    semanticStorage.store({
      content: "dark",
      tags: ["preference", "pref:theme"],
    });

    // Rollback to version 1
    const rolledBack = versionChain.rollback("theme", 1, { semantic: semanticStorage });

    expect(rolledBack.content).toBe("light");
    expect(rolledBack.version).toBe(3);
    expect(rolledBack.metadata?.rollback_from).toBe(1);

    // Verify semantic storage was updated
    const prefs = semanticStorage.searchByTag("pref:theme");
    expect(prefs[0]?.content).toBe("light");
  });
});