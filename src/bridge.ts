// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Plugin Bridge (TypeScript)
 *
 * Direct JSON-RPC handler interface. Routes OpenClaw plugin calls
 * to MemoryManager without subprocess. Replaces Python subprocess bridge.
 */

import { MemoryManager, getMemoryManager } from "./memory_manager";

export interface JsonRpcRequest {
  jsonrpc: "2.0";
  method: string;
  params?: Record<string, unknown>;
  id?: string | number;
}

export interface JsonRpcResponse {
  jsonrpc: "2.0";
  id?: string | number;
  result?: unknown;
  error?: { code: number; message: string };
}

export interface ClawMemPluginApi {
  registerService(svc: { id: string; start(): Promise<void>; stop(): Promise<void> }): void;
  registerTool(factory: unknown, opts: { names: string[] }): void;
  on(event: string, handler: (event: unknown, ctx: unknown) => Promise<void>): void;
  pluginConfig?: Record<string, unknown>;
  logger?: { info(...a: unknown[]): void; error(...a: unknown[]): void; warn(...a: unknown[]): void };
}

/** Handle a single JSON-RPC request. Returns response suitable for serialization. */
export function handleRequest(req: JsonRpcRequest, mm?: MemoryManager): JsonRpcResponse {
  const id = req.id;
  const params = req.params ?? {};
  const manager = mm ?? getMemoryManager();

  try {
    const method = req.method;
    let result: unknown;

    switch (method) {
      case "ping":
        result = { version: "5.0.0", status: "ok" };
        break;
      case "status":
        result = manager.getStats();
        break;
      case "store":
        result = {
          success: manager.store(
            String(params.content ?? ""),
            String(params.memory_type ?? "episodic"),
            (params.tags as string[]) ?? [],
            (params.metadata as Record<string, unknown>) ?? {},
          ),
        };
        break;
      case "search":
        result = {
          results: manager.search(
            String(params.query ?? ""),
            params.memory_type as string,
            Number(params.limit ?? 10),
          ),
        };
        break;
      case "get":
        result = { status: "not_implemented" };
        break;
      case "delete":
        result = { status: "not_implemented" };
        break;
      case "build_context":
        result = { context: "" };
        break;
      case "dreaming_run": {
        result = { staged: 0, scored: 0, passed: 0, promoted: 0, duration_ms: 0 };
        break;
      }
      case "dreaming_status":
        result = { status: "no_run" };
        break;
      case "dreaming_dry_run":
        result = { staged: 0, scored: 0, passed: 0, promoted: 0, duration_ms: 0, dry_run: true };
        break;
      case "system.health":
        result = manager.health();
        break;
      case "system.stats":
        result = manager.getStats();
        break;
      case "system.integrityCheck": {
        const { IntegrityChecker } = require("./integrity_checker");
        result = new IntegrityChecker(manager.workspace, manager.index).quickCheck();
        break;
      }
      case "export":
        result = {
          exported: new (require("./data_portability").DataPortability)(manager.workspace)
            .exportData(String(params.outputDir || "/tmp/claw-mem-export")),
        };
        break;
      case "import":
        result = {
          imported: new (require("./data_portability").DataPortability)(manager.workspace)
            .importData(String(params.inputDir || "/tmp/claw-mem-import")),
        };
        break;
      default:
        return { jsonrpc: "2.0", id, error: { code: -32601, message: `Method '${method}' not found` } };
    }

    return { jsonrpc: "2.0", id, result };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return { jsonrpc: "2.0", id, error: { code: -32000, message: msg } };
  }
}

/** OpenClaw plugin registration entry point. */
export const plugin = {
  id: "claw-mem",
  name: "Claw Memory System (TS v5.0.0)",
  description: "Local-First Three-Tier Memory System",
  version: "5.0.0",
  register(api: ClawMemPluginApi) {
    const config = api.pluginConfig ?? {};
    void new MemoryManager({
      workspace: (config.workspaceDir as string) || undefined,
      enableGating: !!(config.enableGating ?? false),
      enableDecay: !!(config.enableDecay ?? false),
      enableCompression: !!(config.enableCompression ?? true),
    });

    api.logger?.info("[claw-mem TS] v5.0.0 initialized");

    api.registerService({
      id: "claw-mem-ts",
      start: async () => { api.logger?.info("[claw-mem TS] service started"); },
      stop: async () => { api.logger?.info("[claw-mem TS] service stopped"); },
    });
  },
};
