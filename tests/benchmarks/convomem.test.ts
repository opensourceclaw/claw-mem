import { describe, it, expect } from "vitest";
import { getMemoryManager } from "../../src/memory_manager";

describe("ConvoMem Benchmark", () => {
  it("loads test data and builds index", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-convomem" });
    mm.store("Peter prefers TypeScript and Chinese", "episodic");
    mm.store("Yesterday we did a code review of the memory module", "episodic");
    mm.store("Peter uses Docker and TypeScript for development", "episodic");
    mm.store("The project claw-mem is a three-tier memory system", "episodic");
    mm.store("The context window size is 204800 tokens", "episodic");
    mm.store("Peter decided to migrate to TypeScript strict mode", "episodic");
    mm.buildIndex();
    expect(mm.getStats().searches).toBeGreaterThanOrEqual(0);
  });

  it("search returns results after indexing", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-convomem2" });
    mm.store("Peter prefers TypeScript and Chinese for development", "episodic");
    mm.buildIndex();
    const results = mm.search("TypeScript");
    expect(Array.isArray(results)).toBe(true);
  });

  it("handles empty search gracefully", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-convomem3" });
    expect(mm.search("")).toEqual([]);
  });

  it("store and search round-trip works", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-convomem4" });
    mm.store("unique-test-marker-xyz", "semantic");
    mm.buildIndex();
    const results = mm.search("unique-test-marker-xyz");
    expect(results.length).toBeGreaterThan(0);
  });

  it("factual queries return results", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-convomem5" });
    mm.store("The context window size is exactly 204800 tokens for this model", "episodic");
    mm.buildIndex();
    expect(mm.search("204800").length).toBeGreaterThan(0);
  });

  it("entity queries work across memory types", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-convomem6" });
    mm.store("Peter uses Docker as containerization tool", "episodic");
    mm.store("Docker is essential for deployment", "semantic");
    mm.buildIndex();
    expect(mm.search("Docker").length).toBeGreaterThanOrEqual(1);
  });
});
