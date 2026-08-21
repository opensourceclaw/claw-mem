/**
 * claw-mem v7.4.0 — pi agent Runtime Plugin Entry
 *
 * Wraps the 16 memory tools as pi agent AgentTool definitions.
 * Executes via the shared JSON-RPC handleRequest bridge (src/bridge.ts),
 * the same business path the OpenClaw plugin uses.
 */

import type { AgentTool, AgentToolResult } from "@earendil-works/pi-agent-core";
import { Type, type Static } from "@sinclair/typebox";
import { handleRequest, type JsonRpcRequest } from "../src/bridge";

async function run(method: string, params: unknown, toolCallId: string): Promise<AgentToolResult<any>> {
  const req: JsonRpcRequest = { jsonrpc: "2.0", id: toolCallId, method, params: params as Record<string, unknown> };
  const res = await handleRequest(req);
  const text = res.error ? JSON.stringify(res.error) : JSON.stringify(res.result ?? {});
  return { content: [{ type: "text", text }], details: {} };
}

// ── Schema helpers ───────────────────────────────────────────────────────
const Query = Type.String({ description: "Search query" });
const Limit = Type.Optional(Type.Number({ description: "Max results" }));
const SessionId = Type.String({ description: "Session ID" });
const PrefKey = Type.String({ description: "Preference key" });

// ── Tool definitions (parameters mirror openclaw_plugin JSON Schema) ─────

export const memTools: AgentTool[] = [
  {
    name: "memory_search",
    label: "Memory Search",
    description: "Search through memories stored in claw-mem.",
    parameters: Type.Object({
      query: Query,
      limit: Limit,
    }),
    execute: async (id, params) => run("search", params, id),
  },
  {
    name: "memory_store",
    label: "Memory Store",
    description: "Store important information in claw-mem.",
    parameters: Type.Object({
      text: Type.String({ description: "Information to remember" }),
      metadata: Type.Optional(Type.Object({})),
      memory_type: Type.Optional(Type.String({ description: "Memory type" })),
    }),
    execute: async (id, params) => run("store", params, id),
  },
  {
    name: "memory_get",
    label: "Memory Get",
    description: "Get a specific memory by ID (limited support).",
    parameters: Type.Object({
      id: Type.String({ description: "Memory ID" }),
    }),
    execute: async (id, params) => run("get", params, id),
  },
  {
    name: "memory_forget",
    label: "Memory Forget",
    description: "Delete a memory by ID (limited support).",
    parameters: Type.Object({
      id: Type.String({ description: "Memory ID to delete" }),
    }),
    execute: async (id, params) => run("delete", params, id),
  },
  {
    name: "memory_failure_classify",
    label: "Failure Classify",
    description: "Classify a failure signal for typed feedback collection.",
    parameters: Type.Object({
      error_message: Type.String({ description: "Error message to classify" }),
      context: Type.Optional(Type.Object({})),
    }),
    execute: async (id, params) => run("classify_failure_signal", params, id),
  },
  {
    name: "memory_get_constitution",
    label: "Get Constitution",
    description: "Get all constitution rules.",
    parameters: Type.Object({}),
    execute: async (id, params) => run("get_constitution", params, id),
  },
  {
    name: "memory_promote_constitution_rule",
    label: "Promote Constitution Rule",
    description: "Promote a rule to constitution.",
    parameters: Type.Object({
      content: Type.String({ description: "Rule content" }),
      tags: Type.Optional(Type.Array(Type.String())),
    }),
    execute: async (id, params) => run("promote_constitution_rule", params, id),
  },
  {
    name: "memory_delete_constitution_rule",
    label: "Delete Constitution Rule",
    description: "Delete a constitution rule.",
    parameters: Type.Object({
      entryId: Type.String({ description: "Rule ID to delete" }),
    }),
    execute: async (id, params) => run("delete_constitution_rule", params, id),
  },
  {
    name: "memory_transcript_get",
    label: "Transcript Get",
    description: "Get transcript for a session.",
    parameters: Type.Object({
      sessionId: SessionId,
    }),
    execute: async (id, params) => run("transcript_get", params, id),
  },
  {
    name: "memory_transcript_search",
    label: "Transcript Search",
    description: "Search across transcripts.",
    parameters: Type.Object({
      query: Query,
      limit: Limit,
    }),
    execute: async (id, params) => run("transcript_search", params, id),
  },
  {
    name: "memory_session_snapshot",
    label: "Session Snapshot",
    description: "Create a session snapshot.",
    parameters: Type.Object({
      snapshot: Type.Object({}),
    }),
    execute: async (id, params) => run("session_snapshot", params, id),
  },
  {
    name: "memory_session_get_latest",
    label: "Session Get Latest",
    description: "Get latest session snapshot.",
    parameters: Type.Object({
      sessionId: Type.Optional(SessionId),
    }),
    execute: async (id, params) => run("session_get_latest", params, id),
  },
  {
    name: "memory_entity_search",
    label: "Entity Search",
    description: "Search entities.",
    parameters: Type.Object({
      name: Type.String({ description: "Entity name to search" }),
    }),
    execute: async (id, params) => run("entity_search", params, id),
  },
  {
    name: "memory_entity_list",
    label: "Entity List",
    description: "List all entities.",
    parameters: Type.Object({
      limit: Type.Optional(Type.Number({ description: "Max results" })),
      offset: Type.Optional(Type.Number({ description: "Offset" })),
    }),
    execute: async (id, params) => run("entity_list", params, id),
  },
  {
    name: "memory_get_preference",
    label: "Get Preference",
    description: "Get user preference.",
    parameters: Type.Object({
      pref_key: PrefKey,
    }),
    execute: async (id, params) => run("get_preference", params, id),
  },
  {
    name: "memory_rollback_preference",
    label: "Rollback Preference",
    description: "Rollback preference to previous version.",
    parameters: Type.Object({
      pref_key: PrefKey,
      version: Type.Number({ description: "Target version number" }),
    }),
    execute: async (id, params) => run("rollback_preference", params, id),
  },
];

export default memTools;

// memoryTools 别名 — 文档/CHANGELOG 约定名（兼容 memTools 已有使用者）
export const memoryTools = memTools;
