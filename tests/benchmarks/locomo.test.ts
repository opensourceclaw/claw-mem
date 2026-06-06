import { describe, it, expect } from "vitest";
import { getMemoryManager } from "../../src/memory_manager";

describe("LoCoMo Benchmark", () => {
  it("stores long conversation and builds index", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-locomo" });
    const msgs = [
      "The three-tier memory design includes episodic, semantic, and procedural",
      "Episodic memory stores conversation history and events",
      "Semantic memory extracts facts and concepts",
      "Procedural memory captures skills and workflows",
      "CJK text support for Chinese and Japanese is required",
      "Performance target is under 10ms for search operations",
      "SQLite is used as the persistent storage backend",
    ];
    for (const m of msgs) mm.store(m, "episodic");
    mm.buildIndex();
    expect(mm.getStats().stores).toBeGreaterThanOrEqual(7);
  });

  it("retrieves information after store", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-locomo2" });
    mm.store("SQLite is the persistent database backend", "episodic");
    mm.buildIndex();
    expect(mm.search("SQLite").length).toBeGreaterThan(0);
  });

  it("handles medium context", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-locomo3" });
    for (let i = 0; i < 20; i++) mm.store(`Context message ${i}`, "episodic");
    mm.buildIndex();
    expect(mm.search("Context message").length).toBeGreaterThan(0);
  });

  it("memory tier search works", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-locomo4" });
    mm.store("Our system uses episodic memory for events", "episodic");
    mm.store("We also have semantic memory for facts", "semantic");
    mm.buildIndex();
    expect(mm.search("episodic memory").length).toBeGreaterThan(0);
  });

  it("context utilization after more stores", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-locomo5" });
    mm.store("SQLite database is the primary storage", "episodic");
    mm.buildIndex();
    const before = mm.search("SQLite").length;
    for (let i = 0; i < 10; i++) mm.store(`Noise ${i}`, "episodic");
    mm.buildIndex();
    expect(mm.search("SQLite").length).toBeGreaterThanOrEqual(before);
  });

  it("search latency is acceptable", () => {
    const mm = getMemoryManager({ workspace: "/tmp/claw-mem-locomo6" });
    mm.store("CRITICAL: deployment uses blue-green strategy", "episodic");
    mm.buildIndex();
    const t0 = Date.now();
    const r = mm.search("deployment");
    expect(Date.now() - t0).toBeLessThan(5000);
    expect(r.length).toBeGreaterThan(0);
  });
});
