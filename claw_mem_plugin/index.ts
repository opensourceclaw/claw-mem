/**
 * claw-mem Plugin for OpenClaw
 * 
 * Architecture: Local-First
 * - TypeScript Plugin spawns Python Bridge process
 * - Communication via stdio JSON-RPC
 * - Zero network overhead
 * - Minimal latency (<10ms)
 * 
 * @packageDocumentation
 */

import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Plugin configuration
 */
interface ClawMemConfig {
  pythonPath?: string;
  bridgePath?: string;
  workspaceDir?: string;
  autoRecall?: boolean;
  autoCapture?: boolean;
  topK?: number;
  debug?: boolean;
}

/**
 * JSON-RPC Request
 */
interface JSONRPCRequest {
  jsonrpc: '2.0';
  method: string;
  params?: any;
  id?: number | string;
}

/**
 * JSON-RPC Response
 */
interface JSONRPCResponse {
  jsonrpc: '2.0';
  result?: any;
  error?: { code: number; message: string; data?: any };
  id?: number | string;
}

/**
 * OpenClaw Plugin API (minimal interface)
 */
interface OpenClawPluginApi {
  id: string;
  name: string;
  version?: string;
  description?: string;
  source: string;
  rootDir?: string;
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
  registerService(service: { id: string; start: () => Promise<void>; stop: () => Promise<void> }): void;

  // Plugin Slots API (v2.5.0+)
  registerMemoryCapability(capability: MemoryPluginCapability): void;
}

/**
 * Memory Plugin Capability (matching OpenClaw SDK)
 */
interface MemoryPluginCapability {
  promptBuilder?: MemoryPromptSectionBuilder;
  flushPlanResolver?: MemoryFlushPlanResolver;
  runtime?: MemoryPluginRuntime;
}

type MemoryPromptSectionBuilder = (params: {
  availableTools: Set<string>;
  citationsMode?: string;
}) => Promise<string[]>;

interface MemoryFlushPlan {
  softThresholdTokens: number;
  forceFlushTranscriptBytes: number;
  reserveTokensFloor: number;
  prompt: string;
  systemPrompt: string;
  relativePath: string;
}

type MemoryFlushPlanResolver = (params: {
  cfg?: any;
  nowMs?: number;
}) => MemoryFlushPlan | null;

interface MemoryPluginRuntime {
  getMemorySearchManager(params: {
    cfg: any;
    agentId: string;
    purpose?: string;
  }): Promise<{ manager: any | null; error?: string }>;
  resolveMemoryBackendConfig(params: {
    cfg: any;
    agentId: string;
  }): { backend: string };
  closeAllMemorySearchManagers?(): Promise<void>;
}

interface MemorySearchResult {
  path: string;
  startLine: number;
  endLine: number;
  score: number;
  snippet: string;
  source: string;
}

/**
 * Plugin Definition
 */
interface PluginDefinition {
  id?: string;
  name?: string;
  description?: string;
  version?: string;
  kind?: 'memory' | 'context-engine';
  configSchema?: any;
  register?: (api: OpenClawPluginApi) => void | Promise<void>;
}

// ============================================================================
// ClawMemBridge - Python Bridge Client
// ============================================================================

/**
 * Bridge client for communicating with Python Bridge
 */
class ClawMemBridge {
  private process: ChildProcess | null = null;
  private requestId = 0;
  private pendingRequests = new Map<number | string, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }>();
  private ready = false;
  private starting = false;
  private logger: OpenClawPluginApi['logger'];
  
  constructor(
    private config: ClawMemConfig,
    logger: OpenClawPluginApi['logger']
  ) {
    this.logger = logger;
  }
  
  /**
   * Check if bridge is ready
   */
  isReady(): boolean {
    return this.ready;
  }
  
  /**
   * Start the bridge
   */
  async start(): Promise<void> {
    if (this.process || this.starting) {
      return;
    }
    
    this.starting = true;
    
    return new Promise((resolve, reject) => {
      const pythonPath = this.config.pythonPath || 'python3';
      const bridgeModule = 'claw_mem.bridge';  // Module name, not path
      
      if (this.config.debug) {
        this.logger.info(`[claw-mem bridge] Starting with ${pythonPath} -m ${bridgeModule}`);
      }
      
      // Set PYTHONPATH only if workspaceDir is explicitly configured
      const workspaceDir = this.config.workspaceDir || process.cwd();
      const env: Record<string, string> = { ...process.env as Record<string, string> };
      if (this.config.workspaceDir) {
        const srcDir = path.join(workspaceDir, 'src');
        env.PYTHONPATH = srcDir;
      }

      // Spawn Python Bridge process with separate arguments
      this.process = spawn(pythonPath, ['-m', bridgeModule], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: workspaceDir,
        env,
      });
      
      // Handle stdout (responses)
      this.process.stdout?.on('data', (data: Buffer) => {
        const lines = data.toString().split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          try {
            const response: JSONRPCResponse = JSON.parse(line);
            const pending = this.pendingRequests.get(response.id!);
            
            if (pending) {
              this.pendingRequests.delete(response.id!);
              
              if (response.error) {
                pending.reject(new Error(response.error.message));
              } else {
                pending.resolve(response.result);
              }
            }
          } catch (e) {
            this.logger.error('[claw-mem bridge] Failed to parse response:', e);
          }
        }
      });
      
      // Handle stderr (logs)
      this.process.stderr?.on('data', (data: Buffer) => {
        const msg = data.toString().trim();
        if (msg) {
          this.logger.info(`[claw-mem bridge] ${msg}`);
        }
      });
      
      // Handle process exit
      this.process.on('exit', (code) => {
        this.logger.info(`[claw-mem bridge] exited with code ${code}`);
        this.process = null;
        this.ready = false;
        this.starting = false;
      });
      
      // Handle process error
      this.process.on('error', (err) => {
        this.logger.error('[claw-mem bridge] Process error:', err);
        this.process = null;
        this.ready = false;
        this.starting = false;
        reject(err);
      });
      
      // Bridge auto-initializes in __init__ and sends id=0 response.
      // Wait for that response instead of sending a separate initialize call.
      this.pendingRequests.set(0, {
        resolve: () => {
          this.ready = true;
          this.starting = false;
          this.logger.info('[claw-mem bridge] Started successfully');
          resolve();
        },
        reject: (err: Error) => {
          this.starting = false;
          this.logger.error('[claw-mem bridge] Failed to initialize:', err);
          reject(err);
        },
      });
    });
  }
  
  /**
   * Call a method on the bridge
   */
  async call(method: string, params?: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.process || !this.process.stdin) {
        reject(new Error('Bridge not started'));
        return;
      }
      
      const id = ++this.requestId;
      const request: JSONRPCRequest = {
        jsonrpc: '2.0',
        method,
        params,
        id,
      };
      
      this.pendingRequests.set(id, { resolve, reject });
      
      // Send request
      const requestStr = JSON.stringify(request) + '\n';
      this.process.stdin.write(requestStr);
      
      if (this.config.debug) {
        this.logger.debug?.(`[claw-mem bridge] → ${requestStr.trim()}`);
      }
      
      // Timeout after 30 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`Timeout waiting for response to ${method}`));
        }
      }, 30000);
    });
  }
  
  /**
   * Stop the bridge
   */
  async stop(): Promise<void> {
    if (this.process) {
      try {
        await this.call('shutdown');
      } catch (e) {
        // Ignore shutdown errors
      }
      
      this.process.kill();
      this.process = null;
      this.ready = false;
    }
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Extract query from event
 */
function extractQueryFromEvent(event: any): string {
  // Extract last user message or other context
  if (event?.messages && Array.isArray(event.messages)) {
    const userMessages = event.messages.filter((m: any) => m.role === 'user');
    if (userMessages.length > 0) {
      const lastMessage = userMessages[userMessages.length - 1];
      return lastMessage.content || '';
    }
  }
  return '';
}

/**
 * Format memories for injection
 */
function formatMemories(memories: any[]): string {
  if (!memories || memories.length === 0) {
    return '';
  }
  
  const lines = ['Relevant memories from previous conversations:'];
  for (const memory of memories) {
    if (memory.content) {
      lines.push(`- ${memory.content}`);
    }
  }
  return lines.join('\n');
}

/**
 * Extract facts from conversation
 */
function extractFactsFromEvent(event: any): string[] {
  // Extract important facts from conversation
  // This is a simple implementation - can be enhanced with LLM
  const facts: string[] = [];
  
  if (event?.messages && Array.isArray(event.messages)) {
    for (const message of event.messages) {
      // Simple heuristic: extract user messages
      if (message.role === 'user' && message.content) {
        const content = message.content.toLowerCase();
        
        // Check for preference patterns
        if (content.includes('prefer') || content.includes('like') || content.includes('want')) {
          facts.push(message.content);
        }
        
        // Check for important facts
        if (content.includes('important') || content.includes('remember') || content.includes('note')) {
          facts.push(message.content);
        }
        
        // Check for decisions
        if (content.includes('decided') || content.includes('chose') || content.includes('selected')) {
          facts.push(message.content);
        }
      }
    }
  }
  
  // Limit to top 3 facts to avoid overwhelming
  return facts.slice(0, 3);
}

// ============================================================================
// Plugin Entry
// Uses plain object export. At runtime OpenClaw >= 2026.4.x calls
// registerMemoryCapability on the actual API object.
// ============================================================================

const plugin: PluginDefinition = {
  id: 'claw-mem',
  name: 'Claw Memory System',
  description: 'Three-tier memory system for OpenClaw (Local-First) - Plugin Slots Enabled',
  version: '2.5.0',
  kind: 'memory',

  configSchema: {
    type: 'object',
    properties: {
      pythonPath: { type: 'string' },
      bridgePath: { type: 'string' },
      workspaceDir: { type: 'string' },
      autoRecall: { type: 'boolean', default: true },
      autoCapture: { type: 'boolean', default: true },
      topK: { type: 'number', default: 10 },
      debug: { type: 'boolean', default: false },
    },
  },

  register(api: OpenClawPluginApi) {
    const config: ClawMemConfig = {
      pythonPath: api.pluginConfig?.pythonPath as string | undefined,
      bridgePath: api.pluginConfig?.bridgePath as string | undefined,
      workspaceDir: (api.pluginConfig?.workspaceDir as string | undefined) || api.config?.workspaceDir,
      autoRecall: (api.pluginConfig?.autoRecall as boolean | undefined) ?? true,
      autoCapture: (api.pluginConfig?.autoCapture as boolean | undefined) ?? true,
      topK: (api.pluginConfig?.topK as number | undefined) ?? 10,
      debug: (api.pluginConfig?.debug as boolean | undefined) ?? false,
    };
    
    const bridge = new ClawMemBridge(config, api.logger);
    let currentSessionId: string | undefined;

    // ========================================================================
    // Register Memory Capability (Plugin Slots - v2.5.0+)
    // Uses (api as any) for registerMemoryCapability which exists at
    // runtime on OpenClaw >= 2026.4.x APIs but not in our local type stubs.
    // ========================================================================

    (api as any).registerMemoryCapability({
      // promptBuilder: Build memory context before each agent turn
      promptBuilder: async (params: { availableTools: Set<string>; citationsMode?: string }) => {
        if (!bridge.isReady()) return [];

        try {
          const result = await bridge.call('build_context', {
            topK: config.topK,
            query: 'important recent context',
          });

          if (result?.context && Array.isArray(result.context)) {
            api.logger.debug?.(`[claw-mem] promptBuilder: ${result.context.length} section(s) injected`);
            return result.context as string[];
          }
        } catch (error) {
          api.logger.warn('[claw-mem] promptBuilder failed, skipping memory injection:', error);
        }

        return [];
      },

      // flushPlanResolver: Compaction strategy for session compression
      flushPlanResolver: (_params: { cfg?: any; nowMs?: number }) => {
        const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        return {
          softThresholdTokens: 100000,
          forceFlushTranscriptBytes: 500000,
          reserveTokensFloor: 20000,
          prompt: 'Below is a conversation transcript. Summarize it concisely, preserving key context, decisions, user preferences, and action items. Remove redundancy while retaining all essential information.',
          systemPrompt: 'You are a conversation summarizer for an AI memory system. Extract and preserve essential information. Be concise.',
          relativePath: `compaction/flush-${ts}.md`,
        };
      },

      // runtime: Memory search manager and backend configuration
      runtime: {
        getMemorySearchManager: async (params: { cfg: any; agentId: string; purpose?: string }) => {
          if (!bridge.isReady()) {
            return { manager: null, error: 'claw-mem bridge not initialized' };
          }

          // Start memory session for this agent
          try {
            await bridge.call('start_session', { sessionId: params.agentId });
            api.logger.debug?.(`[claw-mem] Memory session started: ${params.agentId}`);
          } catch (error) {
            api.logger.warn('[claw-mem] Failed to start memory session:', error);
          }

          const manager = {
            search: async (
              query: string,
              opts?: { maxResults?: number; minScore?: number; sessionKey?: string }
            ): Promise<MemorySearchResult[]> => {
              try {
                const result = await bridge.call('search', {
                  query,
                  limit: opts?.maxResults ?? config.topK,
                });

                if (!result?.memories) return [];

                return result.memories
                  .filter((m: any) => !opts?.minScore || m.score >= opts.minScore)
                  .map((m: any): MemorySearchResult => ({
                    path: `memory://${m.id}`,
                    startLine: 0,
                    endLine: 0,
                    score: m.score || 0,
                    snippet: (m.content || '').slice(0, 500),
                    source: 'memory',
                  }));
              } catch (error) {
                api.logger.error('[claw-mem] MemorySearchManager.search error:', error);
                return [];
              }
            },

            readFile: async (_params: { relPath: string; from?: number; lines?: number }) => {
              return { text: '', path: _params.relPath };
            },

            status: () => ({
              backend: 'builtin',
              workspace: config.workspaceDir || '',
            }),

            probeEmbeddingAvailability: async () => null,
            probeVectorAvailability: async () => false,

            close: async () => {
              try {
                await bridge.call('end_session', { sessionId: params.agentId });
                api.logger.debug?.(`[claw-mem] Memory session ended: ${params.agentId}`);
              } catch (error) {
                api.logger.warn('[claw-mem] Failed to end memory session:', error);
              }
            },
          };

          return { manager };
        },

        resolveMemoryBackendConfig: (_params: { cfg: any; agentId: string }) => ({
          backend: 'builtin' as const,
        }),

        closeAllMemorySearchManagers: async () => {
          try {
            await bridge.call('end_session', {});
          } catch (error) {
            api.logger.warn('[claw-mem] Failed to close all memory sessions:', error);
          }
        },
      },
    });

    // ========================================================================
    // Register Tools (factory pattern: (ctx) => ({ name, description, parameters, execute }))
    // ========================================================================

    api.registerTool((_ctx: any) => ({
      name: 'memory_search',
      description: 'Search through memories stored in claw-mem. Use when you need context about past conversations, decisions, or learned information.',
      parameters: {
        type: 'object',
        properties: {
          query: { type: 'string', description: 'Search query' },
          limit: { type: 'number', description: 'Max results', default: config.topK },
        },
        required: ['query'],
      },
      execute: async (_toolCallId: string, params: any) => {
        if (!bridge.isReady()) return { error: 'Bridge not initialized' };
        try {
          return await bridge.call('search', params);
        } catch (error) {
          api.logger.error('[claw-mem] Search error:', error);
          return { error: (error as Error).message };
        }
      },
    }), { names: ['memory_search'] });

    api.registerTool((_ctx: any) => ({
      name: 'memory_store',
      description: 'Store important information in claw-mem. Use for important facts, decisions, user preferences, or anything worth remembering.',
      parameters: {
        type: 'object',
        properties: {
          text: { type: 'string', description: 'Information to remember' },
          metadata: { type: 'object' },
          memory_type: { type: 'string', description: 'Memory type: episodic, semantic, or procedural', default: 'episodic' },
        },
        required: ['text'],
      },
      execute: async (_toolCallId: string, params: any) => {
        if (!bridge.isReady()) return { error: 'Bridge not initialized' };
        try {
          return await bridge.call('store', params);
        } catch (error) {
          api.logger.error('[claw-mem] Store error:', error);
          return { error: (error as Error).message };
        }
      },
    }), { names: ['memory_store'] });

    api.registerTool((_ctx: any) => ({
      name: 'memory_get',
      description: 'Get a specific memory by ID. Note: This operation is not supported by the current MemoryManager. Use memory_search instead.',
      parameters: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'Memory ID' },
        },
        required: ['id'],
      },
      execute: async (_toolCallId: string, _params: any) => {
        return { error: 'MemoryManager does not support get() method. Use memory_search instead.' };
      },
    }), { names: ['memory_get'] });

    api.registerTool((_ctx: any) => ({
      name: 'memory_forget',
      description: 'Delete a memory by ID. Note: This operation is not supported by the current MemoryManager.',
      parameters: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'Memory ID to delete' },
        },
        required: ['id'],
      },
      execute: async (_toolCallId: string, _params: any) => {
        return { error: 'MemoryManager does not support delete() method.' };
      },
    }), { names: ['memory_forget'] });
    
    // ========================================================================
    // Register Hooks (DEPRECATED - replaced by registerMemoryCapability)
    // Kept for backward compatibility with OpenClaw < 2026.4.x
    // ========================================================================

    // Auto-recall: inject memories before agent starts
    if (config.autoRecall) {
      api.on('before_agent_start', async (event: any, ctx: any) => {
        currentSessionId = ctx.sessionKey;
        
        // Extract query from event
        const query = extractQueryFromEvent(event);
        
        if (!query) {
          return;
        }
        
        try {
          // Search memories
          const result = await bridge.call('search', {
            query,
            limit: config.topK,
          });
          
          // Inject memories into context
          if (result.memories && result.memories.length > 0) {
            const formatted = formatMemories(result.memories);
            if (formatted) {
              return {
                inject: [
                  {
                    role: 'system',
                    content: formatted,
                  },
                ],
              };
            }
          }
        } catch (error) {
          api.logger.error('[claw-mem] Auto-recall error:', error);
        }
      });
    }
    
    // Auto-capture: store memories after agent ends
    if (config.autoCapture) {
      api.on('agent_end', async (event: any, ctx: any) => {
        // Extract facts from conversation
        const facts = extractFactsFromEvent(event);
        
        // Store each fact
        for (const fact of facts) {
          try {
            await bridge.call('store', {
              text: fact,
              memory_type: 'episodic',
            });
          } catch (error) {
            api.logger.error('[claw-mem] Auto-capture error:', error);
          }
        }
      });
    }
    
    // ========================================================================
    // Lifecycle
    // ========================================================================
    
    // Start bridge
    bridge.start().catch((err) => {
      api.logger.error('[claw-mem] Failed to start bridge:', err);
    });
    
    // Register service for lifecycle
    api.registerService({
      id: 'claw-mem',
      start: async () => {
        api.logger.info('[claw-mem] Service started (local-first mode)');
      },
      stop: async () => {
        await bridge.stop();
        api.logger.info('[claw-mem] Service stopped');
      },
    });
  },
};

export default plugin;
