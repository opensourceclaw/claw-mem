/**
 * claw-mem v6.26.0 Plugin for OpenClaw
 *
 * Architecture: Direct TypeScript (no Python subprocess)
 * - Plugin imports TS MemoryManager directly
 * - Zero network overhead, zero subprocess overhead
 * - ConstitutionStore, Stage 0 injection, all v6.6.0 features
 */

import * as path from "path";
import { handleRequest, type JsonRpcRequest } from "./bridge";
import { getMemoryManager, type MemoryManager } from "./memory_manager";
import { ConstitutionStore } from "./constitution";

// ============================================================================
// Type Definitions
// ============================================================================

interface ClawMemConfig {
  workspaceDir?: string;
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
    logger.info("[claw-mem TS] v6.6.0 initialized (no Python subprocess)");
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
  name: "Claw Memory System (TS v6.26.0)",
  description: "Three-tier memory system for OpenClaw — direct TypeScript, no Python subprocess",
  version: "6.26.0",
  kind: "memory",

  configSchema: {
    type: "object",
    properties: {
      workspaceDir: { type: "string", description: "Workspace directory" },
      topK: { type: "number", default: 10 },
      debug: { type: "boolean", default: false },
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
    // Register Memory Capability (Plugin Slots)
    // ========================================================================

    (api as any).registerMemoryCapability({
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
          api.logger.warn("[claw-mem TS] promptBuilder failed:", error);
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

    bridgeReady.catch((err) => {
      api.logger.error("[claw-mem TS] Failed to start:", err);
    });

    // v5.3.0: Dispatch History tools for neoclaw perception loop
    api.registerTool((_ctx: any) => ({
      name: "memory_dispatch_store",
      description: "Store agent dispatch history record (for neoclaw perception loop)",
      parameters: {
        type: "object",
        properties: {
          agent: { type: "string", description: "Target agent (stark/pepper/happy)" },
          intent_type: { type: "string", description: "Intent type (tech/business/economic/body/mind/relationship/asset/investment/risk)" },
          task: { type: "string", description: "Task description" },
          result: { type: "string", description: "Result (success/failure/timeout/rejected)" },
          latency_ms: { type: "number", description: "Latency in milliseconds" },
          confidence: { type: "number", description: "Confidence 0-1" },
          metadata: { type: "object", description: "Additional metadata" },
        },
        required: ["agent", "intent_type", "task", "result"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("store_dispatch_history", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_dispatch_store"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_dispatch_query",
      description: "Query dispatch history with filters and statistics",
      parameters: {
        type: "object",
        properties: {
          agent: { type: "string", description: "Filter by agent" },
          intent_type: { type: "string", description: "Filter by intent type" },
          result: { type: "string", description: "Filter by result" },
          stats: { type: "boolean", description: "Return aggregated statistics instead of raw records" },
          limit: { type: "number", description: "Max records", default: 100 },
        },
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try {
          if (params.stats) return await bridge.call("get_dispatch_stats", params);
          return await bridge.call("get_dispatch_history", params);
        } catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_dispatch_query"] });

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

    // v5.4.0: Cross-Domain Signal tools for neoclaw v5.1.0
    api.registerTool((_ctx: any) => ({
      name: "memory_cross_domain_store",
      description: "Store cross-domain signal for inter-pillar correlation detection",
      parameters: {
        type: "object",
        properties: {
          pillar: { type: "string", description: "Pillar (stark/pepper/happy)" },
          agent: { type: "string", description: "Agent name" },
          signal_type: { type: "string", description: "Signal type (task_start/task_complete/alert/insight)" },
          summary: { type: "string", description: "Human-readable summary" },
          impact_score: { type: "number", description: "Impact score 0-1" },
          related_domains: { type: "array", items: { type: "string" } },
          metadata: { type: "object" },
          ttl: { type: "number", description: "TTL in seconds (optional)" },
        },
        required: ["pillar", "agent", "signal_type", "summary"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("store_cross_domain_signal", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_cross_domain_store"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_cross_domain_query",
      description: "Query cross-domain signals with pillar/time/impact filters",
      parameters: {
        type: "object",
        properties: {
          pillars: { type: "array", items: { type: "string" } },
          min_impact: { type: "number", description: "Minimum impact score" },
          limit: { type: "number", default: 100 },
        },
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("get_cross_domain_signals", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_cross_domain_query"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_cross_domain_correlate",
      description: "Detect cross-domain correlations between current intent and other pillar signals",
      parameters: {
        type: "object",
        properties: {
          current_pillar: { type: "string" },
          current_intent: { type: "string" },
          time_range: { type: "string", default: "6h" },
          threshold: { type: "number", default: 0.5 },
        },
        required: ["current_pillar", "current_intent"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("detect_cross_domain_correlation", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_cross_domain_correlate"] });

    // v5.5.0: Tech Debt Tracking tools for devclaw v4.0.0
    api.registerTool((_ctx: any) => ({
      name: "memory_debt_store",
      description: "Store technical debt record for project tracking",
      parameters: {
        type: "object",
        properties: {
          project: { type: "string", description: "Project name" },
          debt_type: { type: "string", description: "Debt type (code_smell/architecture/dependency/documentation/test_coverage/security/performance/compatibility)" },
          location: { type: "string", description: "Location (file:line or module)" },
          description: { type: "string", description: "Description" },
          severity: { type: "string", description: "Severity (critical/high/medium/low)" },
          impact_score: { type: "number", description: "Impact score 0-1" },
          priority: { type: "string", description: "Priority (auto-inferred if omitted)" },
          assigned_to: { type: "string" },
          metadata: { type: "object" },
        },
        required: ["project", "debt_type", "location", "description", "severity"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try { return await bridge.call("store_tech_debt", params); }
        catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_debt_store"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_debt_query",
      description: "Query technical debts with filters and get statistics",
      parameters: {
        type: "object",
        properties: {
          project: { type: "string" },
          severities: { type: "array", items: { type: "string" } },
          status: { type: "string" },
          stats: { type: "boolean", description: "Return aggregated statistics" },
          limit: { type: "number", default: 100 },
        },
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try {
          if (params.stats) return await bridge.call("get_debt_stats", params);
          return await bridge.call("get_tech_debts", params);
        } catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_debt_query"] });

    api.registerTool((_ctx: any) => ({
      name: "memory_debt_update",
      description: "Update tech debt status or priority",
      parameters: {
        type: "object",
        properties: {
          debt_id: { type: "string" },
          status: { type: "string", description: "New status (open/in_progress/resolved/wont_fix)" },
          priority: { type: "string", description: "New priority (urgent/high/normal/low)" },
          resolution: { type: "string", description: "Resolution description (required for resolved)" },
          reason: { type: "string", description: "Update reason" },
        },
        required: ["debt_id"],
      },
      execute: async (_id: string, params: any) => {
        if (!bridge.isReady()) return { error: "Bridge not initialized" };
        try {
          if (params.status) return await bridge.call("update_debt_status", params);
          if (params.priority) return await bridge.call("update_debt_priority", params);
          return { error: "Must provide status or priority" };
        } catch (error) { return { error: (error as Error).message }; }
      },
    }), { names: ["memory_debt_update"] });

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
