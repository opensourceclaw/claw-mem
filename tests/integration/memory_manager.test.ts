// Copyright 2026 Peter Cheng
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager } from "../../src/memory_manager";

describe("MemoryManager Integration", () => {
  let tmpDir: string;
  let mm: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-mm-"));
    // Create MEMORY.md so autoDetect finds it
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    mm = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("should initialize with correct workspace", () => {
    expect(mm.workspace).toBe(tmpDir);
  });

  it("should store and retrieve episodic memory", () => {
    mm.store("User prefers Python", "episodic", ["preference"]);
    const results = mm.search("Python");
    expect(results.length).toBe(1);
    expect(results[0].content).toBe("User prefers Python");
    expect((results[0].tags as string[])).toContain("preference");
  });

  it("should store and retrieve semantic memory", () => {
    mm.store("Python is the primary language", "semantic", ["tech"]);
    const results = mm.search("Python");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });

  it("should store and retrieve procedural memory", () => {
    mm.store("Deploy using Docker Compose", "procedural", ["deployment", "docker"]);
    const results = mm.search("Docker");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });

  it("should return empty for no-match search", () => {
    const results = mm.search("xyzzy_nonexistent_abc");
    expect(results.length).toBe(0);
  });

  it("should build index and search via n-gram index", () => {
    mm.store("JWT authentication setup guide", "semantic", ["auth"]);
    mm.store("Database migration with Alembic", "semantic", ["db"]);
    mm.buildIndex();
    expect(mm.index.built).toBe(true);
    const results = mm.search("authentication");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });

  it("should report correct stats", () => {
    mm.store("Memory 1", "episodic");
    mm.store("Memory 2", "semantic");
    mm.store("Memory 3", "procedural");
    const stats = mm.getStats();
    expect(stats.episodicCount).toBeGreaterThanOrEqual(1);
    expect(stats.semanticCount).toBeGreaterThanOrEqual(1);
    expect(stats.proceduralCount).toBeGreaterThanOrEqual(1);
  });

  it("should handle empty content gracefully", () => {
    expect(mm.store("", "episodic")).toBe(false);
    expect(mm.store("   ", "semantic")).toBe(false);
  });
});
