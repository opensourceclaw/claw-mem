// Entity RPC Tests (v6.30.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { handleRequest, type JsonRpcRequest } from "../../src/bridge";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager";

describe("Entity RPC", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-entity-rpc-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  function mm(): MemoryManager {
    return new MemoryManager({ workspace: tmpDir, autoDetect: false });
  }

  function req(method: string, params?: Record<string, unknown>): JsonRpcRequest {
    return { jsonrpc: "2.0", method, params, id: 1 };
  }

  describe("entity_search", () => {
    it("returns entity", () => {
      const m = mm();
      m.store("Working on claw-mem with TypeScript", "episodic");

      const resp = handleRequest(req("entity_search", { name: "clawmem" }), m);
      expect(resp.error).toBeUndefined();
      expect(resp.result).not.toBeNull();

      const result = resp.result as any;
      expect(result.entity.name).toBe("clawmem");
    });

    it("returns related entities", () => {
      const m = mm();
      m.store("claw-mem uses TypeScript and Docker", "episodic");

      const resp = handleRequest(req("entity_search", { name: "clawmem" }), m);
      const result = resp.result as any;

      expect(result.related_entities).toContain("typescript");
      expect(result.related_entities).toContain("docker");
    });

    it("returns null for missing entity", () => {
      const m = mm();

      const resp = handleRequest(req("entity_search", { name: "nonexistent" }), m);
      expect(resp.result).toBeNull();
    });

    it("returns -32602 for missing name", () => {
      const m = mm();

      const resp = handleRequest(req("entity_search", {}), m);
      expect(resp.error?.code).toBe(-32602);
      expect(resp.error?.message).toBe("Missing name");
    });
  });

  describe("entity_resolve", () => {
    it("returns canonical", () => {
      const m = mm();

      const resp = handleRequest(req("entity_resolve", { name: "claw-mem" }), m);
      expect(resp.error).toBeUndefined();

      const result = resp.result as any;
      expect(result.canonical).toBe("clawmem");
    });

    it("returns alternatives", () => {
      const m = mm();
      m.store("Using claw-mem", "episodic");

      const resp = handleRequest(req("entity_resolve", { name: "clawmem" }), m);
      const result = resp.result as any;

      expect(result.alternatives).toContain("claw-mem");
    });

    it("returns -32602 for missing name", () => {
      const m = mm();

      const resp = handleRequest(req("entity_resolve", {}), m);
      expect(resp.error?.code).toBe(-32602);
    });
  });

  describe("entity_list", () => {
    it("returns all entities", () => {
      const m = mm();
      m.store("claw-mem and TypeScript", "episodic");
      m.store("Docker setup", "episodic");

      const resp = handleRequest(req("entity_list"), m);
      expect(resp.error).toBeUndefined();

      const result = resp.result as any;
      expect(result.entities.length).toBeGreaterThan(0);
      expect(result.total).toBeGreaterThan(0);
    });

    it("returns entity summary", () => {
      const m = mm();
      m.store("claw-mem work", "episodic");

      const resp = handleRequest(req("entity_list"), m);
      const result = resp.result as any;

      const entity = result.entities.find((e: any) => e.name === "clawmem");
      expect(entity).toBeDefined();
      expect(entity.type).toBeDefined();
      expect(entity.memory_count).toBeDefined();
    });

    it("supports pagination with limit and offset", () => {
      const m = mm();
      // Store multiple entities
      m.store("claw-mem and TypeScript", "episodic");
      m.store("Docker and Git", "episodic");
      m.store("npm and vitest", "episodic");

      // Get total count first
      const totalResp = handleRequest(req("entity_list", { limit: 100 }), m);
      const totalResult = totalResp.result as any;
      const totalCount = totalResult.total;

      // Get first page
      const page1 = handleRequest(req("entity_list", { limit: 2, offset: 0 }), m);
      const result1 = page1.result as any;
      expect(result1.entities.length).toBeLessThanOrEqual(2);
      expect(result1.limit).toBe(2);
      expect(result1.offset).toBe(0);
      expect(result1.total).toBe(totalCount);

      // Get second page
      const page2 = handleRequest(req("entity_list", { limit: 2, offset: 2 }), m);
      const result2 = page2.result as any;
      expect(result2.offset).toBe(2);
      expect(result2.total).toBe(totalCount);
    });
  });

  describe("entity_stats", () => {
    it("returns stats", () => {
      const m = mm();
      m.store("claw-mem and TypeScript", "episodic");

      const resp = handleRequest(req("entity_stats"), m);
      expect(resp.error).toBeUndefined();

      const result = resp.result as any;
      expect(result.entityCount).toBeGreaterThan(0);
      expect(result.coocCount).toBeDefined();
    });

    it("returns empty stats when no entities", () => {
      const m = mm();

      const resp = handleRequest(req("entity_stats"), m);
      const result = resp.result as any;

      expect(result.entityCount).toBe(0);
    });
  });
});
