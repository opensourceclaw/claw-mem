/**
 * claw-mem v5.2.0 Plugin for OpenClaw
 *
 * Architecture: Direct TypeScript (no Python subprocess)
 * - Plugin imports TS MemoryManager directly
 * - Zero network overhead, zero subprocess overhead
 * - ConstitutionStore, Stage 0 injection, all v5.1 features
 */

import * as path from "path";
import { handleRequest, type JsonRpcRequest } from "../src/bridge";
import { getMemoryManager, type MemoryManager } from "../src/memory_manager";
import { ConstitutionStore } from "../src/constitution";

// ============================================================================
// Type Definitions
// ============================================================================

interface ClawMemConfig {
  workspaceDir?: string;
  autoRecall?: boolean;
  autoCapture?: boolean;
  topK?: number;
  debug?: boolean;
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

  constructor(config: ClawMemConfig, logger: OpenClawPluginApi["logger"]) {
    this._logger = logger;
    const ws = config.workspaceDir || process.cwd();
    this._manager = getMemoryManager({ workspace: ws, autoDetect: false });
    this._constitution = this._manager.constitutionStore;
    this._ready = true;
    logger.info("[claw-mem TS] v5.1.0 initialized (no Python subprocess)");
  }

  isReady(): boolean { return this._ready; }

  async call(method: string, params?: any): Promise<any> {
    const req: JsonRpcRequest = {
      jsonrpc: "2.0",
      method,
      params: params ?? {},
      id: 1,
    };
    const resp = handleRequest(req, this._manager);
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
  configSchema?: any;
  register?: (api: OpenClawPluginApi) => void | Promise<void>;
}

const plugin: PluginDefinition = {
  id: "claw-mem",
  name: "Claw Memory System (TS v5.1.0)",
  description: "Three-tier memory system for OpenClaw — direct TypeScript, no Python subprocess",
  version: "5.1.0",
  kind: "memory",

  configSchema: {
    type: "object",
    properties: {
      workspaceDir: { type: "string", description: "Workspace directory" },
      autoRecall: { type: "boolean", default: true },
      autoCapture: { type: "boolean", default: true },
      topK: { type: "number", default: 10 },
      debug: { type: "boolean", default: false },
    },
  },

  register(api: OpenClawPluginApi) {
    const config: ClawMemConfig = {
      workspaceDir: (api.pluginConfig?.workspaceDir as string | undefined) || api.config?.workspaceDir,
      autoRecall: (api.pluginConfig?.autoRecall as boolean | undefined) ?? true,
      autoCapture: (api.pluginConfig?.autoCapture as boolean | undefined) ?? true,
      topK: (api.pluginConfig?.topK as number | undefined) ?? 10,
      debug: (api.pluginConfig?.debug as boolean | undefined) ?? false,
    };

    const bridge = new TsBridge(config, api.logger);
    let currentSessionId: string | undefined;

    // ========================================================================
    // Register Memory Capability (Plugin Slots)
    // ========================================================================

    (api as any).registerMemoryCapability({
      promptBuilder: async (_params: { availableTools: Set<string>; citationsMode?: string }) => {
        if (!bridge.isReady()) return [];
        try {
          const criticalResult = await bridge.call("get_critical_rules", {});
          const result = await bridge.call("build_context", {
            topK: config.topK,
            query: "important recent context",
          });
          const sections: string[] = [];
          if (result?.context && Array.isArray(result.context)) {
            sections.push(...(result.context as string[]));
          }
          if (criticalResult?.rules && Array.isArray(criticalResult.rules) && criticalResult.rules.length > 0) {
            const rulesLines = criticalResult.rules.map((r: any) => `- **${r.id}**: ${r.text}`);
            sections.unshift("Critical Rules:\n" + rulesLines.join("\n"));
          }
          return sections;
        } catch (error) {
          api.logger.warn("[claw-mem TS] promptBuilder failed:", error);
          return [];
        }
      },

      flushPlanResolver: (_params: { cfg?: any; nowMs?: number }) => {
        const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
        return {
          softThresholdTokens: 100000,
          forceFlushTranscriptBytes: 500000,
          reserveTokensFloor: 20000,
          prompt: "Summarize the conversation, preserving key context, decisions, preferences, and action items.",
          systemPrompt: "You are a conversation summarizer for an AI memory system.",
          relativePath: `compaction/flush-${ts}.md`,
        };
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
          try { await bridge.call("end_session", {}); }
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

    // ========================================================================
    // Hooks
    // ========================================================================

    const bridgeReady: Promise<void> = bridge.start();

    if (config.autoRecall) {
      api.on("before_agent_start", async (event: any, ctx: any) => {
        currentSessionId = ctx.sessionKey;
        try { await bridgeReady; } catch { return; }
        if (!bridge.isReady()) return;

        try {
          await bridge.call("start_session", { sessionId: ctx.sessionKey });
        } catch (error) {
          api.logger.warn("[claw-mem TS] Failed to start session:", error);
        }

        const query = extractQueryFromEvent(event);
        let searchResults: any[] = [];
        if (query && typeof query === "string" && query.trim()) {
          try {
            const result = await bridge.call("search", { query, limit: config.topK });
            searchResults = result.memories || [];
          } catch (error) {
            api.logger.error("[claw-mem TS] Auto-recall error:", error);
          }
        }
        if (searchResults.length > 0) {
          const formatted = formatMemories(searchResults);
          if (formatted) {
            return { inject: [{ role: "system", content: formatted }] };
          }
        }
      });
    }

    if (config.autoCapture) {
      api.on("after_agent_turn", async (event: any, ctx: any) => {
        try { await bridgeReady; } catch { return; }
        if (!bridge.isReady()) return;
        const messages: any[] = [];
        if (event?.userMessage) messages.push(event.userMessage);
        if (event?.assistantMessage) messages.push(event.assistantMessage);
        if (messages.length === 0) return;
        try {
          const important = await bridge.call("extract_important_content", { messages });
          if (important?.important && Array.isArray(important.important)) {
            for (const item of important.important) {
              if (item.importance && item.importance >= 0.5) {
                await bridge.call("store", {
                  text: item.content, memory_type: "episodic",
                  metadata: { importance: item.importance, source: item.source,
                    content_type: item.type, session_id: ctx.sessionKey },
                });
              }
            }
          }
        } catch (error) {
          api.logger.debug?.("[claw-mem TS] after_agent_turn capture skipped:", error);
        }
      });

      api.on("agent_end", async (event: any, ctx: any) => {
        try { await bridgeReady; } catch { return; }
        if (!bridge.isReady()) return;

        if (event?.messages && event.messages.length > 0) {
          const recentMsgs = event.messages.slice(-50);
          try {
            const important = await bridge.call("extract_important_content", { messages: recentMsgs });
            if (important?.important && Array.isArray(important.important)) {
              for (const item of important.important) {
                if (item.importance && item.importance >= 0.5) {
                  await bridge.call("store", {
                    text: item.content, memory_type: "episodic",
                    metadata: { importance: item.importance, source: item.source,
                      content_type: item.type, session_id: ctx.sessionKey },
                  });
                }
              }
            }
          } catch (error) {
            api.logger.warn("[claw-mem TS] extract_important_content failed:", error);
          }
        }
      });
    }

    bridgeReady.catch((err) => {
      api.logger.error("[claw-mem TS] Failed to start:", err);
    });

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
