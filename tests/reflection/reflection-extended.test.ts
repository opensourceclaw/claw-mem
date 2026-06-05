import { describe, it, expect } from "vitest";
import { ReflectionOrchestrator } from "../../src/reflection/orchestrator";
import { BaseStorage } from "../../src/storage/base";
import type { MemoryRecord } from "../../src/types";

// ── ReflectionOrchestrator 补充测试 ──────────────────────────────────

describe("ReflectionOrchestrator (extended)", () => {
  function makeOrch(): ReflectionOrchestrator {
    return new ReflectionOrchestrator({ min_observations: 1 });
  }

  function makeMem(content: string, id: string = "m1"): Record<string, unknown> {
    return { content, source: "user", id, timestamp: new Date().toISOString() };
  }

  describe("get_beliefs", () => {
    it("returns empty array initially", () => {
      const orch = makeOrch();
      expect(orch.get_beliefs()).toHaveLength(0);
    });

    it("returns beliefs after reflection", () => {
      const orch = makeOrch();
      orch.reflect([
        makeMem("User prefers dark mode", "m1"),
        makeMem("User prefers dark themes", "m2"),
      ], "user1");
      const beliefs = orch.get_beliefs();
      expect(beliefs.length).toBeGreaterThanOrEqual(1);
      expect(beliefs[0].belief_id).toBeDefined();
      expect(beliefs[0].confidence).toBeGreaterThan(0);
    });

    it("includes history when requested", () => {
      const orch = makeOrch();
      orch.reflect([
        makeMem("User prefers dark mode", "m1"),
        makeMem("User prefers TypeScript", "m2"),
      ], "user1");
      const beliefs = orch.get_beliefs(true);
      if (beliefs.length > 0) {
        expect(beliefs[0].history).toBeDefined();
        expect(Array.isArray(beliefs[0].history)).toBe(true);
      }
    });
  });

  describe("get_reflection_stats", () => {
    it("returns zero stats initially", () => {
      const orch = makeOrch();
      const stats = orch.get_reflection_stats();
      expect(stats.reflection_count).toBe(0);
      expect(stats.total_beliefs).toBe(0);
    });

    it("updates after reflections", () => {
      const orch = makeOrch();
      orch.reflect([makeMem("User prefers Python", "m1"), makeMem("User prefers async", "m2")], "u1");
      orch.reflect([makeMem("User prefers dark theme", "m3"), makeMem("User prefers minimal", "m4")], "u1");
      const stats = orch.get_reflection_stats();
      expect(stats.reflection_count).toBe(2);
      expect(stats.last_reflection_at).toBeTruthy();
    });
  });

  describe("reflect with force", () => {
    it("works with empty memories array", () => {
      const orch = makeOrch();
      const result = orch.reflect([], "user1", true);
      expect(result.observations).toHaveLength(0);
      expect(result.beliefs).toHaveLength(0);
      expect(result.timestamp).toBeTruthy();
    });
  });
});

// ── BaseStorage 测试 ──────────────────────────────────────────────────

class TestStorage extends BaseStorage {
  private records: Map<string, MemoryRecord> = new Map();

  store(record: MemoryRecord): string { this.records.set(record.id, record); return record.id; }
  retrieve(id: string): MemoryRecord | undefined { return this.records.get(id); }
  delete(id: string): boolean { return this.records.delete(id); }
  listAll(memoryType?: string, limit?: number): MemoryRecord[] {
    let result = [...this.records.values()];
    if (memoryType) result = result.filter((r) => r.memory_type === memoryType);
    if (limit !== undefined) result = result.slice(0, limit);
    return result;
  }
}

describe("BaseStorage", () => {
  it("count returns 0 for empty storage", () => {
    expect(new TestStorage().count()).toBe(0);
  });

  it("count returns total records", () => {
    const s = new TestStorage();
    s.store({ id: "1", text: "a", memory_type: "episodic", timestamp: "", importance: 0.5 });
    s.store({ id: "2", text: "b", memory_type: "semantic", timestamp: "", importance: 0.5 });
    expect(s.count()).toBe(2);
  });

  it("count filters by type", () => {
    const s = new TestStorage();
    s.store({ id: "1", text: "a", memory_type: "episodic", timestamp: "", importance: 0.5 });
    s.store({ id: "2", text: "b", memory_type: "semantic", timestamp: "", importance: 0.5 });
    expect(s.count("episodic")).toBe(1);
  });

  it("CRUD operations", () => {
    const s = new TestStorage();
    s.store({ id: "x", text: "hello", memory_type: "episodic", timestamp: "", importance: 0.8 });
    expect(s.retrieve("x")?.text).toBe("hello");
    expect(s.delete("x")).toBe(true);
    expect(s.retrieve("x")).toBeUndefined();
    expect(s.delete("y")).toBe(false);
  });

  it("listAll respects limit", () => {
    const s = new TestStorage();
    for (let i = 0; i < 5; i++) {
      s.store({ id: `id-${i}`, text: `text-${i}`, memory_type: "episodic", timestamp: "", importance: 0.5 });
    }
    expect(s.listAll(undefined, 3)).toHaveLength(3);
    expect(s.listAll()).toHaveLength(5);
  });
});
