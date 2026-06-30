// Entity Integration Tests (v6.30.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager";

describe("MemoryManager Entity Integration", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-entity-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  describe("auto-indexing", () => {
    it("auto-indexes entities on store", () => {
      manager.store("Working on claw-mem with TypeScript", "episodic");

      const result = manager.entitySearch("clawmem");
      expect(result).not.toBeNull();
      expect(result?.entity.name).toBe("clawmem");
    });

    it("does not index when disabled", () => {
      resetMemoryManager();
      const disabledManager = new MemoryManager({
        workspace: tmpDir,
        autoDetect: false,
        config: { entityIndex: { enabled: false } } as any,
      });

      disabledManager.store("Working on claw-mem", "episodic");

      const result = disabledManager.entitySearch("clawmem");
      expect(result).toBeNull();
    });

    it("handles indexing errors gracefully", () => {
      // Store should succeed even if indexing fails
      const success = manager.store("Valid content", "episodic");
      expect(success).toBe(true);
    });
  });

  describe("entity search", () => {
    it("entitySearch returns results", () => {
      manager.store("Fixed bug in claw-mem using TypeScript", "episodic");
      manager.store("claw-mem performance improvements", "episodic");

      const result = manager.entitySearch("clawmem");
      expect(result).not.toBeNull();
      expect(result?.entity.memoryIds.length).toBeGreaterThanOrEqual(2);
    });

    it("entitySearch returns null when disabled", () => {
      resetMemoryManager();
      const disabledManager = new MemoryManager({
        workspace: tmpDir,
        autoDetect: false,
        config: { entityIndex: { enabled: false } } as any,
      });

      const result = disabledManager.entitySearch("anything");
      expect(result).toBeNull();
    });

    it("entitySearch returns related entities", () => {
      manager.store("claw-mem uses TypeScript and Docker", "episodic");

      const result = manager.entitySearch("clawmem");
      expect(result?.related).toContain("typescript");
      expect(result?.related).toContain("docker");
    });
  });

  describe("entity resolve", () => {
    it("entityResolve returns results", () => {
      manager.store("Working on claw-mem", "episodic");

      const result = manager.entityResolve("claw-mem");
      expect(result).not.toBeNull();
      expect(result?.canonical).toBe("clawmem");
    });

    it("entityResolve returns alternatives", () => {
      manager.store("Using claw-mem", "episodic");

      const result = manager.entityResolve("clawmem");
      expect(result?.alternatives).toContain("claw-mem");
    });
  });

  describe("list entities", () => {
    it("listEntities returns all entities", () => {
      manager.store("claw-mem and TypeScript", "episodic");
      manager.store("Docker container setup", "episodic");

      const entities = manager.listEntities();
      expect(entities.length).toBeGreaterThan(0);
    });

    it("listEntities returns empty array when disabled", () => {
      resetMemoryManager();
      const disabledManager = new MemoryManager({
        workspace: tmpDir,
        autoDetect: false,
        config: { entityIndex: { enabled: false } } as any,
      });

      const entities = disabledManager.listEntities();
      expect(entities).toEqual([]);
    });
  });

  describe("entity stats", () => {
    it("getEntityStats returns stats", () => {
      manager.store("claw-mem and TypeScript", "episodic");

      const stats = manager.getEntityStats();
      expect(stats.entityCount).toBeGreaterThan(0);
    });

    it("getEntityStats returns empty stats when disabled", () => {
      resetMemoryManager();
      const disabledManager = new MemoryManager({
        workspace: tmpDir,
        autoDetect: false,
        config: { entityIndex: { enabled: false } } as any,
      });

      const stats = disabledManager.getEntityStats();
      expect(stats).toEqual({ entityCount: 0, coocCount: 0, totalMemoryLinks: 0, avgCoocPerEntity: 0 });
    });
  });

  describe("backward compatibility", () => {
    it("existing store API works", () => {
      const success = manager.store("Test content", "episodic", ["test"]);
      expect(success).toBe(true);
    });

    it("existing search API works", () => {
      manager.store("Test content for search", "episodic");

      const results = manager.search("Test content");
      expect(results.length).toBeGreaterThan(0);
    });

    it("search results unchanged", () => {
      manager.store("claw-mem is a memory system", "episodic");

      const results = manager.search("memory system");
      expect(results.length).toBeGreaterThan(0);
    });
  });
});
