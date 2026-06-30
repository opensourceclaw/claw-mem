// Entity Index Tests (v6.30.0)

import { describe, it, expect, beforeEach } from "vitest";
import { EntityIndex } from "../../src/entity/entity-index";
import { EntityExtractor } from "../../src/entity/entity-extractor";
import { EntityResolver } from "../../src/entity/entity-resolver";

describe("EntityIndex", () => {
  let index: EntityIndex;

  beforeEach(() => {
    index = new EntityIndex();
  });

  describe("indexing", () => {
    it("indexes entities from text", () => {
      index.index("Working on claw-mem with @peter", "memory_1");

      const result = index.search("clawmem");
      expect(result).not.toBeNull();
      expect(result?.entity.memoryIds).toContain("memory_1");
    });

    it("creates entity records", () => {
      index.index("Using TypeScript for claw-mem", "memory_1");

      const entities = index.listAll();
      expect(entities.find(e => e.name === "typescript")).toBeDefined();
      expect(entities.find(e => e.name === "clawmem")).toBeDefined();
    });

    it("updates existing entity records", () => {
      index.index("Using claw-mem", "memory_1");
      index.index("Fixed bug in claw-mem", "memory_2");

      const result = index.search("clawmem");
      expect(result?.entity.memoryIds).toHaveLength(2);
      expect(result?.entity.memoryIds).toContain("memory_1");
      expect(result?.entity.memoryIds).toContain("memory_2");
    });

    it("creates co-occurrence entries", () => {
      index.index("Using claw-mem and TypeScript together", "memory_1");

      const related = index.getCooccurrences("clawmem");
      expect(related).toContain("typescript");
    });

    it("increments co-occurrence count", () => {
      index.index("claw-mem with TypeScript", "memory_1");
      index.index("claw-mem and TypeScript again", "memory_2");

      const stats = index.getStats();
      expect(stats.coocCount).toBe(1); // Same pair
    });

    it("handles duplicate memoryId", () => {
      index.index("claw-mem project", "memory_1");
      index.index("claw-mem again", "memory_1");

      const result = index.search("clawmem");
      expect(result?.entity.memoryIds).toHaveLength(1);
    });

    it("enforces maxEntitiesPerMemory limit", () => {
      const limitedIndex = new EntityIndex({ maxEntitiesPerMemory: 3 });

      // Create text with many entities
      const text = "Using claw-mem with TypeScript, Docker, GitHub, Git, npm, vitest, and eslint";
      limitedIndex.index(text, "memory_1");

      const entities = limitedIndex.listAll();
      expect(entities.length).toBeLessThanOrEqual(3);
    });

    it("keeps highest confidence entities when limiting", () => {
      const limitedIndex = new EntityIndex({ maxEntitiesPerMemory: 2 });

      // claw-mem (0.95 project), @peter (0.95 person), TypeScript (0.9 tool)
      const text = "Working on claw-mem with @peter using TypeScript";
      limitedIndex.index(text, "memory_1");

      const entities = limitedIndex.listAll();
      const names = entities.map(e => e.name);

      // Should have kept claw-mem and peter (both 0.95 confidence)
      expect(names).toContain("clawmem");
      expect(names).toContain("peter");
      expect(names).not.toContain("typescript");
    });
  });

  describe("search", () => {
    it("searches by entity name", () => {
      index.index("Working on claw-mem", "memory_1");

      const result = index.search("clawmem");
      expect(result).not.toBeNull();
      expect(result?.entity.name).toBe("clawmem");
    });

    it("returns co-occurring entities", () => {
      index.index("claw-mem uses TypeScript and Docker", "memory_1");

      const result = index.search("clawmem");
      expect(result?.related).toContain("typescript");
      expect(result?.related).toContain("docker");
    });

    it("handles entity not found", () => {
      const result = index.search("nonexistent");
      expect(result).toBeNull();
    });

    it("resolves name before search", () => {
      index.index("Using claw-mem", "memory_1");

      // Search with different casing
      const result = index.search("ClawMem");
      expect(result).not.toBeNull();
      expect(result?.entity.name).toBe("clawmem");
    });
  });

  describe("resolve", () => {
    it("resolves name to canonical", () => {
      const result = index.resolve("claw-mem");

      expect(result.canonical).toBe("clawmem");
    });

    it("returns candidates", () => {
      index.index("Using claw-mem", "memory_1");

      const result = index.resolve("clawmem");
      expect(result.alternatives).toContain("claw-mem");
    });
  });

  describe("edge cases", () => {
    it("handles empty text", () => {
      index.index("", "memory_1");
      expect(index.listAll()).toHaveLength(0);
    });

    it("handles text without entities", () => {
      index.index("just some random words", "memory_1");
      expect(index.listAll()).toHaveLength(0);
    });

    it("handles memory removal", () => {
      index.index("claw-mem and TypeScript", "memory_1");
      index.index("claw-mem again", "memory_2");

      index.removeMemory("memory_1");

      const result = index.search("clawmem");
      expect(result?.entity.memoryIds).not.toContain("memory_1");
      expect(result?.entity.memoryIds).toContain("memory_2");
    });

    it("removes entity when no memories left", () => {
      index.index("claw-mem only", "memory_1");

      index.removeMemory("memory_1");

      expect(index.search("clawmem")).toBeNull();
    });

    it("updates coocGraph on memory removal", () => {
      index.index("claw-mem and TypeScript", "memory_1");
      index.index("claw-mem and TypeScript", "memory_2");

      // Check coocGraph has entry
      let related = index.getCooccurrences("clawmem");
      expect(related).toContain("typescript");

      // Remove one memory
      index.removeMemory("memory_1");

      // coocGraph should still have entry (count decremented)
      related = index.getCooccurrences("clawmem");
      expect(related).toContain("typescript");

      // Remove second memory
      index.removeMemory("memory_2");

      // Now both entities are gone, coocGraph should be empty
      const stats = index.getStats();
      expect(stats.coocCount).toBe(0);
    });

    it("removes coocGraph entry when count reaches zero", () => {
      index.index("claw-mem and TypeScript", "memory_1");

      let stats = index.getStats();
      expect(stats.coocCount).toBe(1);

      index.removeMemory("memory_1");

      stats = index.getStats();
      expect(stats.coocCount).toBe(0);
    });
  });

  describe("stats", () => {
    it("returns correct stats", () => {
      index.index("claw-mem and TypeScript", "memory_1");
      index.index("Docker and claw-mem", "memory_2");

      const stats = index.getStats();

      expect(stats.entityCount).toBe(3); // clawmem, typescript, docker
      expect(stats.coocCount).toBeGreaterThan(0);
      expect(stats.totalMemoryLinks).toBe(4); // 2 memories * 2 entities each, minus overlap
    });

    it("returns empty stats for empty index", () => {
      const stats = index.getStats();

      expect(stats.entityCount).toBe(0);
      expect(stats.coocCount).toBe(0);
      expect(stats.totalMemoryLinks).toBe(0);
    });
  });

  describe("clear", () => {
    it("clears all data", () => {
      index.index("claw-mem and TypeScript", "memory_1");

      index.clear();

      expect(index.listAll()).toHaveLength(0);
      expect(index.getStats().coocCount).toBe(0);
    });
  });

  describe("custom extractor/resolver", () => {
    it("uses custom extractor", () => {
      const customExtractor = new EntityExtractor({
        customRules: [
          { pattern: /#\w+/g, type: "concept", confidence: 0.9, nameTransform: (m) => m.slice(1) },
        ],
      });

      const customIndex = new EntityIndex({ extractor: customExtractor });
      customIndex.index("Working on #feature", "memory_1");

      const entities = customIndex.listAll();
      expect(entities.find(e => e.name === "feature")).toBeDefined();
    });

    it("uses custom resolver", () => {
      const customResolver = new EntityResolver({
        customAliases: {
          "mytool": ["TS"],  // Map "TS" (alias for TypeScript) to "mytool"
        },
      });

      const customIndex = new EntityIndex({ resolver: customResolver });
      customIndex.index("Using TS for development", "memory_1");

      // TS is extracted as acronym, then resolved to "mytool"
      const result = customIndex.search("TS");
      expect(result?.entity.name).toBe("mytool");
    });
  });
});
