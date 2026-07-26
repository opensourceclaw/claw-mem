/**
 * claw-mem Plugin for OpenClaw
 *
 * Architecture: Direct TypeScript (no Python subprocess)
 * - Plugin imports TS MemoryManager directly
 * - Zero network overhead, zero subprocess overhead
 * - ConstitutionStore, Stage 0 injection
 */

import * as path from "path";
import { VERSION } from "./version";
import { handleRequest, type JsonRpcRequest } from "./bridge";
import { getMemoryManager, type MemoryManager } from "./memory_manager";
import { ConstitutionStore } from "./constitution";
import { TranscriptStorage, type TranscriptConfig } from "./transcript/index.js";
import { RecapGenerator, type Recap } from "./transcript/recap-generator.js";
import { clearGlobalQueryCache } from "./retrieval/query_cache.js";

// ============================================================================
// Type Definitions
// ============================================================================

interface ClawMemConfig {
  workspaceDir?: string;
  topK?: number;
  debug?: boolean;
  transcript?: Partial<TranscriptConfig>;
}

interface OpenClawPluginApi {
  id: string;
  config: any;
  pluginConfig?: Record<string, unknown>;
  logger: {
    info: (...args: any[]) => void;
    error: (...args: any[]) => void;
    warn: (...args: any[]) => void;
    debug?: (...args: any[]) => void;
  };
  registerTool(factory: (ctx: any) => any, opts?: { names: string[] }): void;
  on(eventName: string, handler: (event: any, ctx: any) => Promise<any | void>): void;
  registerService(service: {
    id: string;
    start: () => Promise<void>;
    stop: () => Promise<void>;
  }): void;
}

interface MemorySearchResult {
  path: string;
  startLine: number;
  endLine: number;
  score: number;
  snippet: string;
  source: string;
}

// ============================================================================
// TS Bridge — direct MemoryManager wrapper (replaces Python subprocess)
// ============================================================================

class TsBridge {
  private _manager: MemoryManager;
  private _constitution: ConstitutionStore;
  private _ready: boolean;
  private _logger: OpenClawPluginApi["logger"];
  // v6.36.0: Removed duplicate TranscriptStorage - use _manager.transcript instead
  private _currentSessionId: string | null = null;

  constructor(config: ClawMemConfig, logger: OpenClawPluginApi["logger"]) {
    this._logger = logger;
    const ws = config.workspaceDir || process.cwd();
    this._manager = getMemoryManager({ workspace: ws, autoDetect: false });
    this._constitution = this._manager.constitutionStore;
    this._ready = true;

    // v6.36.0: TranscriptStorage is now managed by MemoryManager
    // Removed duplicate instantiation to prevent memory leak
    if (this._manager.transcript) {
      logger.info(`[claw-mem TS] ✅ TranscriptStorage available via MemoryManager, workspace: ${ws}`);
    } else {
      logger.warn("[claw-mem TS] ⚠️ TranscriptStorage not initialized");
    }

    logger.info(`[claw-mem TS] v${VERSION} initialized (no duplicate TranscriptStorage)`);
  }

  isReady(): boolean { return this._ready; }

  /** v6.36.0: Expose manager for direct access */
  get manager(): MemoryManager { return this._manager; }

  /** v6.36.0: Delegate to MemoryManager.transcript to avoid duplicate instance */
  get transcriptStorage(): TranscriptStorage | null {
    return this._manager.transcript;
  }

  async call(method: string, params?: any): Promise<any> {
    // v6.36.0: Handle end_session with recap generation (using MemoryManager.transcript)
    if (method === "end_session") {
      const ts = this._manager.transcript;
      // Get current session ID before ending
      const currentSessionId = ts?.getCurrentSessionId();

      // Generate recap before ending session
      if (ts && currentSessionId) {
        const recapGenerator = new RecapGenerator();
        const recap = ts.endSession(recapGenerator);
        if (recap) {
          // Ensure session_id is set correctly
          recap.sessionId = currentSessionId;

          this._logger?.info?.(`[claw-mem TS] Generated recap for session ${currentSessionId}: ${recap.whatWereWeDoing.substring(0, 50)}...`);

          // Store recap as session_recap memory
          this._manager.store(
            `Session Recap: ${recap.whatWereWeDoing}\n\nNext: ${recap.whatIsNext}`,
            "session_recap",
            ["session_recap"],
            { session_id: currentSessionId, timestamp: recap.timestamp }
          );
        }
      } else if (ts) {
        // No session to recap, just end
        ts.endSession();
      }

      // v6.36.0: Clear global query cache on session end to prevent memory leak
      clearGlobalQueryCache();
      this._logger?.debug?.("[claw-mem TS] Cleared global query cache on session end");
    }

    const req: JsonRpcRequest = {
      jsonrpc: "2.0",
      method,
      params: params ?? {},
      id: 1,
    };
    const resp = await handleRequest(req, this._manager);
    if (resp.error) throw new Error(resp.error.message);
    return resp.result;
  }

  async start(): Promise<void> {
    this._ready = true;
  }

  async stop(): Promise<void> {
    this._ready = false;
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Sanitize sessionKey to prevent path traversal and limit length.
 * Removes path separators and truncates to 64 characters.
 */
function sanitizeSessionKey(key: string): string {
  return key.replace(/[/\\]/g, '_').slice(0, 64);
}

function extractQueryFromEvent(event: any): string {
  if (event?.messages && Array.isArray(event.messages)) {
    const userMessages = event.messages.filter((m: any) => m.role === "user");
    if (userMessages.length > 0) {
      const lastMessage = userMessages[userMessages.length - 1];
      const content = lastMessage.content;
      if (typeof content === "string") return content;
      if (Array.isArray(content)) {
        return content.map((c: any) => typeof c === "string" ? c : c?.text || "").join(" ");
      }
      return String(content || "");
    }
  }
  return "";
}

function formatMemories(memories: any[]): string {
  if (!memories || memories.length === 0) return "";
  const lines = ["Relevant memories from previous conversations:"];
  for (const memory of memories) {
    if (memory.content) lines.push(`- ${memory.content}`);
  }
  return lines.join("\n");
}

function extractFactsFromEvent(event: any): { text: string; type: string }[] {
  const results: { text: string; type: string }[] = [];
  if (event?.messages && Array.isArray(event.messages)) {
    for (const m of event.messages) {
      if (!m.role || (m.role !== "user" && m.role !== "assistant")) continue;
      let content = "";
      if (typeof m.content === "string") content = m.content;
      else if (m.content?.text) content = String(m.content.text);
      else if (Array.isArray(m.content)) content = m.content.map((c: any) => String(c.text || "")).join(" ");
      if (!content.trim() || content.length < 10) continue;
      const lower = content.toLowerCase();
      if (lower.startsWith("```") || lower.startsWith("error:")) continue;
      results.push({
        text: content.slice(0, 1000),
        type: m.role === "user" ? "user_input" : "assistant_response",
      });
    }
  }
  return results;
}

// ============================================================================
// Plugin Entry
// ============================================================================

interface PluginDefinition {
  id?: string;
  name?: string;
  description?: string;
  version?: string;
  kind?: "memory" | "context-engine";
  contracts?: { tools?: string[] };
  configSchema?: any;
  register?: (api: OpenClawPluginApi) => void | Promise<void>;
}

const ALL_TOOL_NAMES = [
  "memory_search", "memory_store", "memory_get", "memory_forget",
  "memory_failure_classify",
  "memory_get_constitution", "memory_promote_constitution_rule", "memory_delete_constitution_rule",
  "memory_transcript_get", "memory_transcript_search",
  "memory_session_snapshot", "memory_session_get_latest",
  "memory_entity_search", "memory_entity_list",
  "memory_get_preference", "memory_rollback_preference",
];

  const plugin: PluginDefinition = {
  id: "claw-mem",
  name: `Claw Memory System (TS v${VERSION})`,
  description: "Three-tier memory system for OpenClaw — direct TypeScript, no Python subprocess",
  version: VERSION,
  kind: "memory",

  contracts: {
    tools: ALL_TOOL_NAMES,
  },

  configSchema: {
    type: "object",
    properties: {
      workspaceDir: { type: "string", description: "Workspace directory" },
      topK: { type: "number", default: 10 },
      debug: { type: "boolean", default: false },
      transcript: {
        type: "object",
        properties: {
          enabled: { type: "boolean", default: true },
          ttlDays: { type: "number", default: 30 },
          format: { type: "string", enum: ["markdown", "json"], default: "markdown" },
        },
      },
    },
  },

  register(api: OpenClawPluginApi) {
    const config: ClawMemConfig = {
      workspaceDir: (api.pluginConfig?.workspaceDir as string | undefined) || api.config?.workspaceDir,
      topK: (api.pluginConfig?.topK as number | undefined) ?? 10,
      debug: (api.pluginConfig?.debug as boolean | undefined) ?? false,
    };

    const bridge = new TsBridge(config, api.logger);
    let currentSessionId: string | undefined;

    // ========================================================================
    // Transcript Event Hooks (v6.32.5 - Correct plugin hook names)
    // ========================================================================

    // Track runId to correlate user/assistant messages in the same turn
    let currentRunId: string | undefined;

    // Hook 1: message_received - Capture user messages
    api.on("message_received", async (event: { content?: string; sessionKey?: string; runId?: string; from?: string }, ctx: any) => {
      try {
        const ts = bridge.transcriptStorage;
        if (!ts) {
          api.logger.warn?.("[claw-mem TS] ⚠️ message_received: TranscriptStorage not initialized");
          return;
        }

        const content = event.content;
        if (!content) {
          api.logger.debug?.("[claw-mem TS] message_received: No content in event");
          return;
        }

        // Track runId for correlation with llm_output
        if (event.runId) {
          currentRunId = event.runId;
        }

        // Session identification
        const channel = ctx?.channel || "api";
        const sessionId = event.sessionKey || ctx?.sessionId || `session-${new Date().toISOString().slice(0, 10)}`;

        // Start session if not already active
        if (sessionId !== currentSessionId) {
          const sanitizedId = sanitizeSessionKey(sessionId);
          ts.startSession(sanitizedId, channel);
          currentSessionId = sanitizedId;
          api.logger.info?.(`[claw-mem TS] ✅ Started transcript session: ${sanitizedId}`);
        }

        // Append user message to transcript
        ts.appendMessage({
          role: "user",
          content,
          timestamp: new Date().toISOString(),
        });
        api.logger.info?.(`[claw-mem TS] ✅ Wrote user message to session ${currentSessionId} (${content.length} chars)`);
      } catch (err) {
        api.logger.error?.(`[claw-mem TS] ❌ message_received handler error: ${err}`);
      }
    });

    // Hook 2: llm_output - Capture assistant responses
    api.on("llm_output", async (event: { assistantTexts?: string[]; runId?: string; sessionId?: string; prompt?: string }, ctx: any) => {
      try {
        const ts = bridge.transcriptStorage;
        if (!ts) {
          api.logger.warn?.("[claw-mem TS] ⚠️ llm_output: TranscriptStorage not initialized");
          return;
        }

        const assistantTexts = event.assistantTexts;
        if (!assistantTexts || assistantTexts.length === 0) {
          api.logger.debug?.("[claw-mem TS] llm_output: No assistantTexts in event");
          return;
        }

        // Join all text blocks (filter empty strings)
        const content = assistantTexts.filter(t => t && t.trim()).join("\n");
        if (!content) {
          api.logger.debug?.("[claw-mem TS] llm_output: No content after filtering empty strings");
          return;
        }

        // Session identification - prefer sessionId from llm_output
        const channel = ctx?.channel || "api";
        const sessionId = event.sessionId || currentSessionId || `session-${new Date().toISOString().slice(0, 10)}`;

        // Start session if not already active
        if (sessionId !== currentSessionId) {
          const sanitizedId = sanitizeSessionKey(sessionId);
          ts.startSession(sanitizedId, channel);
          currentSessionId = sanitizedId;
          api.logger.info?.(`[claw-mem TS] ✅ Started transcript session: ${sanitizedId}`);
        }

        // Append assistant message to transcript
        ts.appendMessage({
          role: "assistant",
          content,
          timestamp: new Date().toISOString(),
        });
        api.logger.info?.(`[claw-mem TS] ✅ Wrote assistant message to session ${currentSessionId} (${content.length} chars)`);
      } catch (err) {
        api.logger.error?.(`[claw-mem TS] ❌ llm_output handler error: ${err}`);
      }
    });

    // ========================================================================
    // Register Memory Capability (Plugin Slots)
    // ========================================================================

    (api as any).registerMemoryCapability({
      // v6.40.2: flushPlanResolver for token compression
      // Thresholds adjusted for balanced memory management:
      // - softThresholdTokens: 100k (trigger at 50% of 200k context)
      // - forceFlushTranscriptBytes: 300KB (earlier compaction)
      flushPlanResolver: (_params: { cfg?: any; nowMs?: number }) => {
        const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        return {
          softThresholdTokens: 100000,
          forceFlushTranscriptBytes: 300000,
          reserveTokensFloor: 20000,
          prompt: 'Below is a conversation transcript. Summarize it concisely, preserving key context, decisions, user preferences, and action items. Remove redundancy while retaining all essential information.',
          systemPrompt: 'You are a conversation summarizer for an AI memory system. Extract and preserve essential information. Be concise.',
          relativePath: `compaction/flush-${ts}.md`,
        };
      },

      promptBuilder: async (_params: { availableTools: Set<string>; citationsMode?: string }) => {
        if (!bridge.isReady()) return [];
        try {
          const criticalResult = await bridge.call("get_critical_rules", {});
          const searchResult = await bridge.call("search", {
            query: "important recent context",
            limit: config.topK,
          });
          const sections: string[] = [];
          if (searchResult?.results && Array.isArray(searchResult.results)) {
            for (const r of searchResult.results) {
              sections.push(`- ${r.content} (score: ${r.score?.toFixed(2) || "N/A"})`);
            }
          }
          if (criticalResult?.rules && Array.isArray(criticalResult.rules) && criticalResult.rules.length > 0) {
            const rulesLines = criticalResult.rules.map((r: any) => `- **${r.id}**: ${r.text}`);
            sections.unshift("Critical Rules:\n" + rulesLines.join("\n"));
          }
          return sections;
        } catch (error) {
          const msg = error instanceof Error ? error.message : String(error);
          api.logger.warn(`[claw-mem TS] promptBuilder failed: ${msg}`);
          return [];
        }
      },

      runtime: {
        getMemorySearchManager: async (params: { cfg: any; agentId: string; purpose?: string }) => {
          if (!bridge.isReady()) {
            return { manager: null, error: "claw-mem TS bridge not initialized" };
          }
          try {
            await bridge.call("start_session", { sessionId: params.agentId });
          } catch (error) {
            api.logger.warn("[claw-mem TS] Failed to start memory session:", error);
          }

          const manager = {
            search: async (
              query: string,
              opts?: { maxResults?: number; minScore?: number; sessionKey?: string }
            ): Promise<MemorySearchResult[]> => {
              try {
                const result = await bridge.call("search", {
                  query,
                  limit: opts?.maxResults ?? config.topK,
                });
                if (!result?.memories) return [];
                return result.memories
                  .filter((m: any) => !opts?.minScore || m.score >= opts.minScore)
                  .map((m: any): MemorySearchResult => ({
                    path: `memory://${m.id}`,
                    startLine: 0, endLine: 0,
                    score: m.score || 0,
                    snippet: (m.content || "").slice(0, 500),
                    source: "memory",
                  }));
              } catch (error) {
                api.logger.error("[claw-mem TS] search error:", error);
                return [];
              }
            },
            readFile: async (_p: { relPath: string; from?: number; lines?: number }) =>
              ({ text: "", path: _p.relPath }),
            status: () => ({ backend: "builtin", workspace: config.workspaceDir || "" }),
            probeEmbeddingAvailability: async () => null,
            probeVectorAvailability: async () => false,
            close: async () => {
              try {
                await bridge.call("end_session", { sessionId: params.agentId });
              } catch (error) {
                api.logger.warn("[claw-mem TS] Failed to end memory session:", error);
              }
            },
          };
          return { manager };
        },

        resolveMemoryBackendConfig: (_params: { cfg: any; agentId: string }) =>
          ({ backend: "builtin" as const }),

        closeAllMemorySearchManagers: async () => {
          try {
            await bridge.call("end_session", {});
          }
          catch (error) { api.logger.warn("[claw-mem TS] Failed to close all memory sessions:", error); }
        },
      },
    });
    // ========================================================================
    // Register Tools
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: "memory_search",
      description: "Search through memories stored in claw-mem.",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" },
          limit: { type: "number", description: "Max results", default: config.topK },
        },
        required: ["query"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("search", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_search"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_store",
      description: "Store important information in claw-mem.",
      parameters: {
        type: "object",
        properties: {
          text: { type: "string", description: "Information to remember" },
          metadata: { type: "object" },
          memory_type: { type: "string", default: "episodic" },
        },
        required: ["text"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("store", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_store"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_get",
      description: "Get a specific memory by ID (limited support).",
      parameters: {
        type: "object",
        properties: { id: { type: "string", description: "Memory ID" } },
        required: ["id"],
      },
      execute: async (_id: string, _params: any) =>
        ({ error: "Use memory_search instead." }),
    }), { names: ["memory_get"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_forget",
      description: "Delete a memory by ID (limited support).",
      parameters: {
        type: "object",
        properties: { id: { type: "string", description: "Memory ID to delete" } },
        required: ["id"],
      },
      execute: async (_id: string, _params: any) =>
        ({ error: "Delete not supported." }),
    }), { names: ["memory_forget"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_failure_classify",
      description: "Classify a failure signal for typed feedback collection",
      parameters: {
        type: "object",
        properties: {
          error_message: { type: "string", description: "Error message to classify" },
          context: { type: "object", description: "Error context (agent, task, etc.)" },
        },
        required: ["error_message"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("classify_failure_signal", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_failure_classify"] });

    // ========================================================================
    // Hooks
    // ========================================================================

    const bridgeReady: Promise<void> = bridge.start();

    bridgeReady.catch((err) => {
      api.logger.error("[claw-mem TS] Failed to start:", err);
    });

    // ========================================================================
    // Constitution Tools (v6.38.0)
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: "memory_get_constitution",
      description: "Get all constitution rules",
      parameters: { type: "object", properties: {} },
      execute: async (_id: string, _params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("get_constitution", {}); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_get_constitution"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_promote_constitution_rule",
      description: "Promote a rule to constitution",
      parameters: {
        type: "object",
        properties: {
          content: { type: "string", description: "Rule content" },
          tags: { type: "array", items: { type: "string" } },
        },
        required: ["content"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("promote_constitution_rule", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_promote_constitution_rule"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_delete_constitution_rule",
      description: "Delete a constitution rule",
      parameters: {
        type: "object",
        properties: { entryId: { type: "string", description: "Rule ID to delete" } },
        required: ["entryId"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("delete_constitution_rule", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_delete_constitution_rule"] });

    // ========================================================================
    // Transcript Tools (v6.38.0)
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: "memory_transcript_get",
      description: "Get transcript for a session",
      parameters: {
        type: "object",
        properties: { sessionId: { type: "string", description: "Session ID" } },
        required: ["sessionId"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("transcript_get", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_transcript_get"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_transcript_search",
      description: "Search across transcripts",
      parameters: {
        type: "object",
        properties: {
          query: { type: "string", description: "Search query" },
          limit: { type: "number", description: "Max results", default: 10 },
        },
        required: ["query"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("transcript_search", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_transcript_search"] });

    // ========================================================================
    // Session Snapshot Tools (v6.38.0)
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: "memory_session_snapshot",
      description: "Create a session snapshot",
      parameters: {
        type: "object",
        properties: { snapshot: { type: "object", description: "Session snapshot data" } },
        required: ["snapshot"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("session_snapshot", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_session_snapshot"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_session_get_latest",
      description: "Get latest session snapshot",
      parameters: {
        type: "object",
        properties: { sessionId: { type: "string", description: "Optional session ID" } },
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("session_get_latest", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_session_get_latest"] });

    // ========================================================================
    // Entity Tools (v6.38.0)
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: "memory_entity_search",
      description: "Search entities",
      parameters: {
        type: "object",
        properties: { name: { type: "string", description: "Entity name to search" } },
        required: ["name"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("entity_search", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_entity_search"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_entity_list",
      description: "List all entities",
      parameters: {
        type: "object",
        properties: {
          limit: { type: "number", default: 100 },
          offset: { type: "number", default: 0 },
        },
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("entity_list", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_entity_list"] });

    // ========================================================================
    // Preference Tools (v6.38.0)
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: "memory_get_preference",
      description: "Get user preference",
      parameters: {
        type: "object",
        properties: { pref_key: { type: "string", description: "Preference key" } },
        required: ["pref_key"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("get_preference", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_get_preference"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_rollback_preference",
      description: "Rollback preference to previous version",
      parameters: {
        type: "object",
        properties: {
          pref_key: { type: "string", description: "Preference key" },
          version: { type: "number", description: "Target version number" },
        },
        required: ["pref_key", "version"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("rollback_preference", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_rollback_preference"] });

    api.registerService({
      id: "claw-mem",
      start: async () => { api.logger.info("[claw-mem TS] Service started"); },
      stop: async () => {
        await bridge.stop();
        api.logger.info("[claw-mem TS] Service stopped");
      },
    });
  },
};

export default plugin;
