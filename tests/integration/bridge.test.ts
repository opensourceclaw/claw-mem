// Copyright 2026 Peter Cheng
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { handleRequest, type JsonRpcRequest } from "../../src/bridge";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager";

describe("Bridge JSON-RPC", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-br-"));
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

  it("ping returns version", () => {
    const resp = handleRequest(req("ping"), mm());
    expect(resp.result).toEqual({ version: "6.31.0", status: "ok" });
  });

  it("status returns stats", () => {
    const resp = handleRequest(req("status"), mm());
    const r = resp.result as Record<string, unknown>;
    expect(r.workspace).toBeTruthy();
  });

  it("store and search round-trip", () => {
    const m = mm();
    handleRequest(req("store", {
      content: "Hello World", memory_type: "episodic",
      tags: ["test"], metadata: {},
    }), m);

    const resp = handleRequest(req("search", {
      query: "Hello", limit: 10,
    }), m);
    const results = (resp.result as Record<string, unknown>).results as unknown[];
    expect(results.length).toBe(1);
  });

  it("unknown method returns error", () => {
    const resp = handleRequest({ jsonrpc: "2.0", method: "no_such_method", id: 42 });
    expect(resp.error).toBeDefined();
    expect(resp.error!.code).toBe(-32601);
  });

  it("dreaming methods return error (removed)", () => {
    const resp = handleRequest(req("dreaming_run"), mm());
    expect(resp.error).toBeDefined();
    expect(resp.error!.code).toBe(-32601);
  });

  it("empty search returns empty results", () => {
    const resp = handleRequest(req("search", { query: "", limit: 10 }), mm());
    const results = (resp.result as Record<string, unknown>).results as unknown[];
    expect(results).toEqual([]);
  });

  it("deprecated methods return deprecated status", () => {
    for (const method of ["get", "delete", "build_context"]) {
      const resp = handleRequest(req(method), mm());
      expect(resp.result).toBeDefined();
      expect((resp.result as Record<string, unknown>).status).toBe("deprecated");
    }
  });
});
