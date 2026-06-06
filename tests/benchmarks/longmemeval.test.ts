import { describe, it, expect } from "vitest";
import { getMemoryManager } from "../../src/memory_manager";

describe("LongMemEval Benchmark", () => {
  it("immediate recall after store", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-lme-0" });
    mm.store("Peter's favorite language is TypeScript", "episodic");
    mm.store("The project deadline is June 30th 2026", "episodic");
    mm.store("Claude Code is used for AI development", "episodic");
    mm.store("SQLite is the local-first database choice", "episodic");
    mm.store("RSI scores should be checked weekly", "episodic");
    mm.buildIndex();

    expect(mm.search("TypeScript").length).toBeGreaterThan(0);
    expect(mm.search("deadline").length).toBeGreaterThan(0);
    expect(mm.search("database").length).toBeGreaterThan(0);
  });

  it("retains critical facts alongside other memories", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-lme-1x" });
    mm.store("CRITICAL: Peter prefers TypeScript for all new projects", "episodic");
    mm.store("Project uses CI/CD pipeline for deployment", "episodic");
    mm.store("Weekly reviews happen on Friday mornings", "episodic");
    mm.buildIndex();

    expect(mm.search("CRITICAL").length).toBeGreaterThan(0);
    expect(mm.search("TypeScript").length).toBeGreaterThan(0);
    expect(mm.search("Peter").length).toBeGreaterThan(0);
  });

  it("multiple phases stored and retrieved", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-lme-2x" });
    mm.store("Phase 1: architecture design completed successfully", "episodic");
    mm.store("Phase 2: core implementation done and reviewed", "episodic");
    mm.store("Phase 3: testing and validation passed", "episodic");
    mm.store("Phase 4: deployment to production complete", "episodic");
    mm.buildIndex();

    expect(mm.search("architecture design").length).toBeGreaterThan(0);
    expect(mm.search("implementation").length).toBeGreaterThan(0);
    expect(mm.search("testing").length).toBeGreaterThan(0);
    expect(mm.search("deployment").length).toBeGreaterThan(0);
  });

  it("search latency is acceptable", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-lme-3y" });
    mm.store("Test memory for latency measurement purposes", "episodic");
    mm.buildIndex();
    const t0 = Date.now();
    const r = mm.search("latency measurement");
    expect(Date.now() - t0).toBeLessThan(5000);
    expect(r.length).toBeGreaterThan(0);
  });
});
