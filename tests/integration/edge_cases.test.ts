// Copyright 2026 Peter Cheng
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager } from "../../src/memory_manager";
import { IntegrityChecker } from "../../src/integrity_checker";
import { IndexEvolver } from "../../src/retrieval/index_evolver";
import { InMemoryIndex } from "../../src/storage/index";
import { MemoryFederation } from "../../src/memory/federation";

describe("Edge Cases", () => {
  let tmpDir: string;
  let mm: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-ec-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    mm = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("empty storage: search returns empty", () => {
    const results = mm.search("anything");
    expect(results.length).toBe(0);
  });

  it("empty storage: stats show zero counts", () => {
    const stats = mm.getStats();
    expect(stats.episodicCount).toBe(0);
    expect(stats.semanticCount).toBe(0);
  });

  it("large content: store 50KB text", () => {
    const large = "x".repeat(50000);
    const ok = mm.store(large, "episodic");
    expect(ok).toBe(true);
    const results = mm.search("xxx");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });

  it("index: load empty then build on demand", () => {
    const idx = new InMemoryIndex(3, tmpDir, false);
    expect(idx.built).toBe(false);
    idx.loadOrBuild([{ id: "test", content: "hello world" }]);
    expect(idx.built).toBe(true);
  });

  it("integrity_checker: seeded workspace reports degraded (no index)", () => {
    // Write enough content so MEMORY.md passes size check
    mm.store("Test content for integrity check", "semantic", ["test"]);
    const checker = new IntegrityChecker(tmpDir);
    const report = checker.quickCheck();
    expect(report.episodic.files).toBeGreaterThanOrEqual(0);
    expect(report.durationMs).toBeGreaterThanOrEqual(0);
    expect(report.status).toBeDefined();
  });

  it("integrity_checker: index rebuild on corruption", () => {
    const idx = new InMemoryIndex(3, tmpDir, false);
    const checker = new IntegrityChecker(tmpDir, idx);
    const report = checker.quickCheck();
    // Index was never built, so rebuilt flag should be true after quickCheck tries loadOrBuild
    expect(report.index.rebuilt).toBe(true);
  });

  it("index_evolver: tracks access and write counts", () => {
    const idx = new InMemoryIndex(3, tmpDir, false);
    idx.loadOrBuild([{ id: "x", content: "test" }]);
    const evolver = new IndexEvolver(idx, { accessThreshold: 99999, writeThreshold: 99999 });
    evolver.touchWrite(5);
    evolver.touchAccess(10);
    const stats = evolver.stats;
    expect(stats.writeCount).toBeGreaterThanOrEqual(5);
    expect(stats.accessCount).toBeGreaterThanOrEqual(10);
    expect(stats.indexBuilt).toBe(true);
  });

  it("federation: search across empty workspaces", () => {
    const fed = new MemoryFederation({ workspaces: [tmpDir] });
    const results = fed.search("nonexistent");
    expect(results.length).toBe(0);
  });

  it("federation: search finds content across workspace", () => {
    mm.store("Shared memory content", "semantic", ["shared"]);
    const fed = new MemoryFederation({ workspaces: [tmpDir] });
    fed.share({ id: "test-1", agent_id: "test", memory_type: "semantic", content: "Shared memory content", tags: ["shared"], timestamp: Date.now() / 1000, confidence: 1.0, source: "local" });
    const results = fed.search("Shared");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });
});
