import { describe, it, expect, beforeEach, vi } from "vitest";
import {
  TieredDecayEngine,
  TierLevel,
  type StorageBackend,
  type LLMProvider,
} from "../../src/decay/tiered_decay";

// ── Mock storage ────────────────────────────────────────────────────────

class MockStorage implements StorageBackend {
  filePath = "/tmp/test-memory.md";
  private memories: Record<string, unknown>[] = [];

  constructor(memories?: Record<string, unknown>[]) {
    this.memories = memories ?? [];
  }

  getAll(): Record<string, unknown>[] {
    return [...this.memories];
  }

  _formatMemory(mem: Record<string, unknown>): string {
    return `- [${mem.id}] ${mem.content}\n`;
  }

  addMemory(mem: Record<string, unknown>): void {
    this.memories.push(mem);
  }
}

class MockLLM implements LLMProvider {
  private responses: Map<string, string> = new Map();
  generate(prompt: string): string {
    for (const [key, val] of this.responses) {
      if (prompt.includes(key)) return val;
    }
    return "0.5";
  }
  setResponse(content: string, score: string): void {
    this.responses.set(content, score);
  }
}

function makeMemory(
  id: string,
  content: string,
  createdHoursAgo: number = 0,
  meta?: Record<string, string>,
  tags?: string[],
): Record<string, unknown> {
  const created = new Date(Date.now() - createdHoursAgo * 3600 * 1000).toISOString();
  return { id, content, created_at: created, metadata: meta ?? {}, tags: tags ?? [] };
}

// ── Tests ───────────────────────────────────────────────────────────────

describe("TieredDecayEngine", () => {
  let storage: MockStorage;

  beforeEach(() => {
    storage = new MockStorage();
  });

  // ── Classification ─────────────────────────────────────────────────

  describe("classify()", () => {
    it("classifies recent memory as HOT", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 3600); // 1hr hot
      const mem = makeMemory("m1", "recent content", 0.5); // 30 min ago
      expect(engine.classify(mem)).toBe(TierLevel.HOT);
    });

    it("classifies medium-age memory as WARM", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 1); // 1s hot
      const mem = makeMemory("m1", "older content", 2); // 2 hours ago
      expect(engine.classify(mem)).toBe(TierLevel.WARM);
    });

    it("classifies old memory as COLD", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 1, 1); // tiny TTLs
      const mem = makeMemory("m1", "ancient", 48); // 2 days ago
      expect(engine.classify(mem)).toBe(TierLevel.COLD);
    });

    it("classifies deprecated memory as COLD regardless of age", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 999999);
      const mem = makeMemory("m1", "new but deprecated", 0, { deprecated: "true" });
      expect(engine.classify(mem)).toBe(TierLevel.COLD);
    });

    it("handles deprecated=true variants", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 999999);
      expect(engine.classify(makeMemory("m1", "x", 0, { deprecated: "True" }))).toBe(TierLevel.COLD);
      expect(engine.classify(makeMemory("m2", "x", 0, { deprecated: "1" }))).toBe(TierLevel.COLD);
    });

    it("uses timestamp field if created_at missing", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 3600);
      const ts = new Date(Date.now() - 2 * 3600 * 1000).toISOString();
      const mem = { id: "m1", content: "test", timestamp: ts };
      expect(engine.classify(mem)).toBe(TierLevel.WARM);
    });
  });

  // ── Promotion ───────────────────────────────────────────────────────

  describe("promote()", () => {
    it("returns null for empty id", () => {
      const engine = new TieredDecayEngine(storage);
      expect(engine.promote("")).toBeNull();
    });

    it("returns current tier for HOT memory", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 999999);
      const mem = makeMemory("m1", "content", 0);
      storage.addMemory(mem);
      expect(engine.promote("m1")).toBe(TierLevel.HOT);
    });

    it("returns null for non-existent memory", () => {
      const engine = new TieredDecayEngine(storage);
      expect(engine.promote("nonexistent")).toBeNull();
    });

    it("promotes COLD to WARM after multiple accesses", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 1, 1); // tiny TTLs
      const mem = makeMemory("m1", "old content", 240); // 10 days ago
      storage.addMemory(mem);
      engine.promote("m1");
      expect(engine.promote("m1")).toBe(TierLevel.WARM);
    });
  });

  // ── Importance Scoring ──────────────────────────────────────────────

  describe("getImportance()", () => {
    it("returns cached importance on second call", () => {
      const engine = new TieredDecayEngine(storage);
      const mem = makeMemory("m1", "important memory content");
      const i1 = engine.getImportance(mem);
      const i2 = engine.getImportance(mem);
      expect(i1).toBe(i2); // cached
    });

    it("uses LLM when provider set", () => {
      const llm = new MockLLM();
      llm.setResponse("test content", "0.85");
      const engine = new TieredDecayEngine(storage, undefined, llm);
      const mem = makeMemory("m2", "test content");
      expect(engine.getImportance(mem)).toBe(0.85);
    });

    it("falls back to rule-based with long content bonus", () => {
      const engine = new TieredDecayEngine(storage);
      // Content longer than 200 chars
      const longContent = "A".repeat(250);
      const mem1 = makeMemory("m1", longContent);
      const mem2 = makeMemory("m2", "short");
      expect(engine.getImportance(mem1)).toBeGreaterThan(engine.getImportance(mem2));
    });

    it("adds tag importance bonus", () => {
      const engine = new TieredDecayEngine(storage);
      const withTags = makeMemory("m1", "content", 0, {}, ["critical", "important"]);
      const withoutTags = makeMemory("m2", "content", 0, {}, []);
      expect(engine.getImportance(withTags)).toBeGreaterThan(engine.getImportance(withoutTags));
    });

    it("uses explicit metadata importance", () => {
      const engine = new TieredDecayEngine(storage);
      const mem = makeMemory("m1", "content", 0, { importance: "0.95" });
      expect(engine.getImportance(mem)).toBe(0.95);
    });

    it("LLM provider error falls back to rule-based", () => {
      const badLLM: LLMProvider = {
        generate: () => { throw new Error("LLM failed"); },
      };
      const engine = new TieredDecayEngine(storage, undefined, badLLM);
      const mem = makeMemory("m1", "test");
      const score = engine.getImportance(mem);
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(1);
    });
  });

  // ── Eviction ────────────────────────────────────────────────────────

  describe("evict()", () => {
    it("evicts deprecated memories first", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 999999, 999, 999, 5, 5, 5);
      for (let i = 0; i < 3; i++) {
        storage.addMemory(makeMemory(`active${i}`, "content", 0));
      }
      storage.addMemory(makeMemory("depr", "deprecated", 0, { deprecated: "true" }));
      const count = engine.evict();
      expect(count).toBeGreaterThanOrEqual(1);
    });

    it("evicts overflow from WARM/COLD tiers", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 1, 1, 30, 5, 2, 2);
      // Add many old memories to trigger COLD overflow
      for (let i = 0; i < 10; i++) {
        storage.addMemory(makeMemory(`cold${i}`, "old content", 240 * (i + 1))); // 10+ days ago
      }
      const count = engine.evict();
      expect(count).toBeGreaterThan(0);
    });

    it("returns 0 when no eviction needed", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 999999, 999, 999, 1000, 1000, 1000);
      storage.addMemory(makeMemory("m1", "single", 0));
      expect(engine.evict()).toBe(0);
    });

    it("does not evict from HOT tier", () => {
      const engine = new TieredDecayEngine(storage, undefined, undefined, 999999, 999, 999, 0, 0, 0);
      // maxHot=0 but shouldn't evict HOT
      storage.addMemory(makeMemory("m1", "hot content", 0));
      const count = engine.evict();
      // Should not evict the hot memory even though maxHot is 0
      expect(count).toBe(0);
    });
  });

  // ── Full Cycle ──────────────────────────────────────────────────────

  describe("runCycle()", () => {
    it("returns tier counts and eviction stats", () => {
      const engine = new TieredDecayEngine(storage);
      storage.addMemory(makeMemory("h1", "recent", 0));
      storage.addMemory(makeMemory("w1", "older", 48));
      storage.addMemory(makeMemory("c1", "ancient", 720));
      storage.addMemory(makeMemory("depr", "x", 0, { deprecated: "true" }));
      const result = engine.runCycle();
      expect(result.total).toBe(4);
      expect(result.hot).toBeGreaterThanOrEqual(1);
      expect(result.warm).toBeGreaterThanOrEqual(0);
      expect(result.cold).toBeGreaterThanOrEqual(1);
      expect(typeof result.evicted).toBe("number");
      expect(typeof result.durationMs).toBe("number");
    });

    it("handles empty storage", () => {
      const engine = new TieredDecayEngine(storage);
      const result = engine.runCycle();
      expect(result.total).toBe(0);
      expect(result.evicted).toBe(0);
    });
  });

  // ── toString ────────────────────────────────────────────────────────

  describe("toString()", () => {
    it("returns readable representation", () => {
      const engine = new TieredDecayEngine(storage);
      const str = engine.toString();
      expect(str).toContain("TieredDecayEngine");
      expect(str).toContain("hot");
      expect(str).toContain("warm");
    });
  });
});
