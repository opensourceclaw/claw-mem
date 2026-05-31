// Copyright 2026 Peter Cheng
// v5.1.0 ConstitutionStore tests

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { ConstitutionStore } from "../../src/constitution";
import { MemoryManager } from "../../src/memory_manager";

describe("ConstitutionStore", () => {
  let tmpDir: string;
  let store: ConstitutionStore;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "const-"));
    store = new ConstitutionStore(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("loads L0 from AGENTS.md", () => {
    fs.writeFileSync(path.join(tmpDir, "AGENTS.md"), "# AGENTS\n\nJarvis: Coding Engineer for claw-mem project\n\n", "utf-8");
    const s2 = new ConstitutionStore(tmpDir);
    const entries = s2.assemble();
    const l0 = entries.filter(e => e.layer === 0);
    expect(l0.length).toBeGreaterThanOrEqual(1);
    expect(l0.some(e => e.content.includes("Jarvis"))).toBe(true);
  });

  it("promotes L2 entries and survives re-creation", () => {
    store.promoteToL2("Always use TypeScript for backend", ["tech_stack"]);
    store.promoteToL2("Communicate via Markdown in ~/comm/", ["protocol"]);

    const s2 = new ConstitutionStore(tmpDir);
    const entries = s2.assemble();
    const l2 = entries.filter(e => e.layer === 2);
    expect(l2.length).toBeGreaterThanOrEqual(2);
    expect(l2.some(e => e.content.includes("TypeScript"))).toBe(true);
  });

  it("empty workspace does not crash", () => {
    const entries = store.assemble();
    expect(Array.isArray(entries)).toBe(true);
  });

  it("scanAndSuggest detects tech stack decisions", () => {
    const suggestions = store.scanAndSuggest([
      { content: "Let's use TypeScript and FastAPI for this project" },
      { content: "We decided to use PostgreSQL as the database" },
    ]);
    expect(suggestions.length).toBeGreaterThanOrEqual(1);
  });

  it("deletes L2 entry", () => {
    const id = store.promoteToL2("Test rule content", ["test"]);
    expect(id).toBeTruthy();
    const deleted = store.delete(id!);
    expect(deleted).toBe(true);
    const after = store.getAll().filter(e => e.id === id);
    expect(after.length).toBe(0);
  });

  it("assembleText returns formatted block", () => {
    store.promoteToL2("Use TypeScript for backend", ["tech"]);
    const text = store.assembleText();
    expect(text).toContain("Constitution");
    expect(text).toContain("TypeScript");
  });
});

describe("MemoryManager Constitution Integration", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "mm-const-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\nUser prefers TypeScript\n\n", "utf-8");
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("initializes with ConstitutionStore", () => {
    const mm = new MemoryManager({ workspace: tmpDir, autoDetect: false });
    expect(mm.constitutionStore).toBeDefined();
    const stats = mm.constitutionStore.getStats();
    expect(stats.totalEntries).toBeGreaterThanOrEqual(0);
  });

  it("migrates legacy critical_rules.json", () => {
    const rulesPath = path.join(tmpDir, "critical_rules.json");
    fs.writeFileSync(rulesPath, JSON.stringify({
      r1: { id: "r1", content: "Always use Python for data processing", metadata: {} },
      r2: { id: "r2", content: "Code review before merge", metadata: {} },
    }), "utf-8");

    const mm = new MemoryManager({ workspace: tmpDir, autoDetect: false });
    // After migration, rules should be in constitutionStore
    const entries = mm.constitutionStore.getAll().filter(e =>
      e.tags?.includes("migrated_v5.1"));
    expect(entries.length).toBeGreaterThanOrEqual(1);

    // Migration flag should exist
    const flagPath = rulesPath + ".migrated_to_constitution";
    expect(fs.existsSync(flagPath)).toBe(true);
  });
});
