import { describe, it, expect, beforeEach } from "vitest";
import { MemoryEntityManager } from "../../src/memory/entity-manager.js";

describe("MemoryEntityManager", () => {
  let manager: MemoryEntityManager;

  beforeEach(() => {
    manager = new MemoryEntityManager();
  });

  describe("linkEntity()", () => {
    it("should link entity to memory", () => {
      manager.linkEntity("mem-1", "entity-A");
      expect(manager.getEntityMemories("entity-A")).toContain("mem-1");
    });

    it("should link multiple memories to same entity", () => {
      manager.linkEntity("mem-1", "entity-A");
      manager.linkEntity("mem-2", "entity-A");
      manager.linkEntity("mem-3", "entity-A");

      const memories = manager.getEntityMemories("entity-A");
      expect(memories).toHaveLength(3);
      expect(memories).toContain("mem-1");
      expect(memories).toContain("mem-2");
      expect(memories).toContain("mem-3");
    });
  });

  describe("unlinkEntity()", () => {
    it("should unlink memory from entity", () => {
      manager.linkEntity("mem-1", "entity-A");
      manager.unlinkEntity("mem-1", "entity-A");
      expect(manager.getEntityMemories("entity-A")).toHaveLength(0);
    });

    it("should remove entity when last memory unlinked", () => {
      manager.linkEntity("mem-1", "entity-A");
      manager.unlinkEntity("mem-1", "entity-A");
      expect(manager.getEntityCount()).toBe(0);
    });
  });

  describe("deleteEntity()", () => {
    it("should delete entity and return affected memories", () => {
      manager.linkEntity("mem-1", "entity-A");
      manager.linkEntity("mem-2", "entity-A");

      const affected = manager.deleteEntity("entity-A");
      expect(affected).toHaveLength(2);
      expect(affected).toContain("mem-1");
      expect(affected).toContain("mem-2");
      expect(manager.getEntityCount()).toBe(0);
    });

    it("should record deletion to audit log", () => {
      manager.linkEntity("mem-1", "entity-A");
      manager.deleteEntity("entity-A");

      const auditLog = manager.getEntityAuditLog();
      expect(auditLog.length).toBeGreaterThan(0);
      expect(auditLog[0].action).toBe("delete_entity");
    });
  });

  describe("audit log", () => {
    it("should return audit stats", () => {
      manager.linkEntity("mem-1", "entity-A");
      manager.deleteEntity("entity-A");

      const stats = manager.getAuditStats();
      expect(stats.total).toBeGreaterThan(0);
      expect(stats.topActions.some(a => a.action === "delete_entity")).toBe(true);
    });
  });
});
