// Bridge RPC Strategy Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { handleRequest, type JsonRpcRequest } from "../../src/bridge.js";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";

describe("Bridge RPC Strategy", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-rpc-strat-"));
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

  it("store returns strategy used", async () => {
    const m = mm();
    const resp = await handleRequest(req("store", {
      content: "Test content",
      memory_type: "episodic",
    }), m);

    expect(resp.error).toBeUndefined();
    expect((resp.result as any).strategy).toBe("episodic");
  });

  it("list_strategies returns all strategies", async () => {
    const m = mm();
    const resp = await handleRequest(req("list_strategies"), m);

    expect(resp.error).toBeUndefined();
    const result = resp.result as any;
    expect(result.strategies.length).toBeGreaterThan(0);
    expect(result.strategies.find((s: any) => s.name === "fact")).toBeDefined();
  });

  it("get_preference returns preference", async () => {
    const m = mm();
    m.store("dark", "preference", [], { pref_key: "theme" });

    const resp = await handleRequest(req("get_preference", { pref_key: "theme" }), m);
    expect(resp.error).toBeUndefined();
    expect((resp.result as any).preference).not.toBeNull();
  });

  it("get_preference returns null for missing pref_key", async () => {
    const m = mm();
    const resp = await handleRequest(req("get_preference", {}), m);
    expect(resp.error?.code).toBe(-32602);
  });

  it("get_preference_history returns version chain", async () => {
    const m = mm();
    m.store("light", "preference", [], { pref_key: "theme" });
    m.store("dark", "preference", [], { pref_key: "theme" });

    const resp = await handleRequest(req("get_preference_history", { pref_key: "theme" }), m);
    expect(resp.error).toBeUndefined();
    expect((resp.result as any).versions.length).toBe(2);
  });

  it("rollback_preference rolls back to previous version", async () => {
    const m = mm();
    m.store("light", "preference", [], { pref_key: "theme" });
    m.store("dark", "preference", [], { pref_key: "theme" });

    const resp = await handleRequest(req("rollback_preference", {
      pref_key: "theme",
      version: 1,
    }), m);

    expect(resp.error).toBeUndefined();
    expect((resp.result as any).preference.content).toBe("light");
  });
});
