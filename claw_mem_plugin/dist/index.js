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
import { spawn } from 'child_process';
import * as path from 'path';
// ============================================================================
// ClawMemBridge - Python Bridge Client
// ============================================================================
/**
 * Bridge client for communicating with Python Bridge
 */
class ClawMemBridge {
    config;
    process = null;
    requestId = 0;
    pendingRequests = new Map();
    ready = false;
    starting = false;
    logger;
    constructor(config, logger) {
        this.config = config;
        this.logger = logger;
    }
    /**
     * Check if bridge is ready
     */
    isReady() {
        return this.ready;
    }
    /**
     * Wait for bridge to become ready with timeout
     */
    async waitForReady(timeoutMs = 10000) {
        if (this.ready)
            return true;
        const start = Date.now();
        while (!this.ready) {
            if (Date.now() - start > timeoutMs) {
                this.logger.warn('[claw-mem bridge] Timed out waiting for bridge to become ready');
                return false;
            }
            await new Promise(r => setTimeout(r, 200));
        }
        this.logger.info('[claw-mem bridge] Bridge is now ready');
        return true;
    }
    /**
     * Start the bridge
     */
    async start() {
        if (this.process || this.starting) {
            return;
        }
        this.starting = true;
        return new Promise((resolve, reject) => {
            const pythonPath = this.config.pythonPath || 'python3';
            const bridgeModule = 'claw_mem.bridge'; // Module name, not path
            if (this.config.debug) {
                this.logger.info(`[claw-mem bridge] Starting with ${pythonPath} -m ${bridgeModule}`);
            }
            // Set PYTHONPATH only if workspaceDir is explicitly configured
            const workspaceDir = this.config.workspaceDir || process.cwd();
            const env = { ...process.env };
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
            this.process.stdout?.on('data', (data) => {
                const lines = data.toString().split('\n').filter(line => line.trim());
                for (const line of lines) {
                    try {
                        const response = JSON.parse(line);
                        const pending = this.pendingRequests.get(response.id);
                        if (pending) {
                            this.pendingRequests.delete(response.id);
                            if (response.error) {
                                pending.reject(new Error(response.error.message));
                            }
                            else {
                                pending.resolve(response.result);
                            }
                        }
                    }
                    catch (e) {
                        this.logger.error('[claw-mem bridge] Failed to parse response:', e);
                    }
                }
            });
            // Handle stderr (logs)
            this.process.stderr?.on('data', (data) => {
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
                reject: (err) => {
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
    async call(method, params) {
        return new Promise((resolve, reject) => {
            if (!this.ready) {
                reject(new Error('Bridge not ready'));
                return;
            }
            if (!this.process || !this.process.stdin) {
                reject(new Error('Bridge not started'));
                return;
            }
            const id = ++this.requestId;
            const request = {
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
    async stop() {
        if (this.process) {
            try {
                await this.call('shutdown');
            }
            catch (e) {
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
function extractQueryFromEvent(event) {
    // Extract last user message or other context
    if (event?.messages && Array.isArray(event.messages)) {
        const userMessages = event.messages.filter((m) => m.role === 'user');
        if (userMessages.length > 0) {
            const lastMessage = userMessages[userMessages.length - 1];
            const content = lastMessage.content;
            // Content can be string or array (multimodal)
            if (typeof content === 'string') {
                return content;
            }
            if (Array.isArray(content)) {
                // Concatenate text parts from multimodal content
                return content
                    .filter((p) => p.type === 'text')
                    .map((p) => p.text || '')
                    .join(' ')
                    || '';
            }
            return String(content || '');
        }
    }
    return '';
}
/**
 * Format memories for injection
 */
function formatMemories(memories) {
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
function extractFactsFromEvent(event) {
    // Extract facts from conversation - capture all user messages for now
    const facts = [];
    if (event?.messages && Array.isArray(event.messages)) {
        // Get all user messages
        const userMessages = event.messages
            .filter((m) => m.role === 'user')
            .map((m) => typeof m.content === 'string' ? m.content : String(m.content?.text || ''))
            .filter((content) => content.length > 0);
        // Keep the last 5 messages (more lenient than 3)
        facts.push(...userMessages.slice(-5));
    }
    return facts;
}
// ============================================================================
// Plugin Entry
// Uses plain object export. At runtime OpenClaw >= 2026.4.x calls
// registerMemoryCapability on the actual API object.
// ============================================================================
const plugin = {
    id: 'claw-mem',
    name: 'Claw Memory System',
    description: 'Three-tier memory system for OpenClaw (Local-First) - Plugin Slots Enabled',
    version: '2.12.1',
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
    register(api) {
        const config = {
            pythonPath: api.pluginConfig?.pythonPath,
            bridgePath: api.pluginConfig?.bridgePath,
            workspaceDir: api.pluginConfig?.workspaceDir || api.config?.workspaceDir,
            autoRecall: api.pluginConfig?.autoRecall ?? true,
            autoCapture: api.pluginConfig?.autoCapture ?? true,
            topK: api.pluginConfig?.topK ?? 10,
            debug: api.pluginConfig?.debug ?? false,
        };
        const bridge = new ClawMemBridge(config, api.logger);
        let currentSessionId;
        // ========================================================================
        // Register Memory Capability (Plugin Slots - v2.5.0+)
        // Uses (api as any) for registerMemoryCapability which exists at
        // runtime on OpenClaw >= 2026.4.x APIs but not in our local type stubs.
        // ========================================================================
        api.registerMemoryCapability({
            // promptBuilder: Build memory context before each agent turn
            promptBuilder: async (params) => {
                if (!bridge.isReady())
                    return [];
                try {
                    const result = await bridge.call('build_context', {
                        topK: config.topK,
                        query: 'important recent context',
                    });
                    if (result?.context && Array.isArray(result.context)) {
                        api.logger.debug?.(`[claw-mem] promptBuilder: ${result.context.length} section(s) injected`);
                        return result.context;
                    }
                }
                catch (error) {
                    api.logger.warn('[claw-mem] promptBuilder failed, skipping memory injection:', error);
                }
                return [];
            },
            // flushPlanResolver: Compaction strategy for session compression
            flushPlanResolver: (_params) => {
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
                getMemorySearchManager: async (params) => {
                    if (!bridge.isReady()) {
                        return { manager: null, error: 'claw-mem bridge not initialized' };
                    }
                    // Start memory session for this agent
                    try {
                        await bridge.call('start_session', { sessionId: params.agentId });
                        api.logger.debug?.(`[claw-mem] Memory session started: ${params.agentId}`);
                    }
                    catch (error) {
                        api.logger.warn('[claw-mem] Failed to start memory session:', error);
                    }
                    const manager = {
                        search: async (query, opts) => {
                            try {
                                const result = await bridge.call('search', {
                                    query,
                                    limit: opts?.maxResults ?? config.topK,
                                });
                                if (!result?.memories)
                                    return [];
                                return result.memories
                                    .filter((m) => !opts?.minScore || m.score >= opts.minScore)
                                    .map((m) => ({
                                    path: `memory://${m.id}`,
                                    startLine: 0,
                                    endLine: 0,
                                    score: m.score || 0,
                                    snippet: (m.content || '').slice(0, 500),
                                    source: 'memory',
                                }));
                            }
                            catch (error) {
                                api.logger.error('[claw-mem] MemorySearchManager.search error:', error);
                                return [];
                            }
                        },
                        readFile: async (_params) => {
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
                            }
                            catch (error) {
                                api.logger.warn('[claw-mem] Failed to end memory session:', error);
                            }
                        },
                    };
                    return { manager };
                },
                resolveMemoryBackendConfig: (_params) => ({
                    backend: 'builtin',
                }),
                closeAllMemorySearchManagers: async () => {
                    try {
                        await bridge.call('end_session', {});
                    }
                    catch (error) {
                        api.logger.warn('[claw-mem] Failed to close all memory sessions:', error);
                    }
                },
            },
        });
        // ========================================================================
        // Register Tools (factory pattern: (ctx) => ({ name, description, parameters, execute }))
        // ========================================================================
        api.registerTool((_ctx) => ({
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
            execute: async (_toolCallId, params) => {
                if (!bridge.isReady())
                    return { error: 'Bridge not initialized' };
                try {
                    return await bridge.call('search', params);
                }
                catch (error) {
                    api.logger.error('[claw-mem] Search error:', error);
                    return { error: error.message };
                }
            },
        }), { names: ['memory_search'] });
        api.registerTool((_ctx) => ({
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
            execute: async (_toolCallId, params) => {
                if (!bridge.isReady())
                    return { error: 'Bridge not initialized' };
                try {
                    return await bridge.call('store', params);
                }
                catch (error) {
                    api.logger.error('[claw-mem] Store error:', error);
                    return { error: error.message };
                }
            },
        }), { names: ['memory_store'] });
        api.registerTool((_ctx) => ({
            name: 'memory_get',
            description: 'Get a specific memory by ID. Note: This operation is not supported by the current MemoryManager. Use memory_search instead.',
            parameters: {
                type: 'object',
                properties: {
                    id: { type: 'string', description: 'Memory ID' },
                },
                required: ['id'],
            },
            execute: async (_toolCallId, _params) => {
                return { error: 'MemoryManager does not support get() method. Use memory_search instead.' };
            },
        }), { names: ['memory_get'] });
        api.registerTool((_ctx) => ({
            name: 'memory_forget',
            description: 'Delete a memory by ID. Note: This operation is not supported by the current MemoryManager.',
            parameters: {
                type: 'object',
                properties: {
                    id: { type: 'string', description: 'Memory ID to delete' },
                },
                required: ['id'],
            },
            execute: async (_toolCallId, _params) => {
                return { error: 'MemoryManager does not support delete() method.' };
            },
        }), { names: ['memory_forget'] });
        // ========================================================================
        // Register Hooks (DEPRECATED - replaced by registerMemoryCapability)
        // Kept for backward compatibility with OpenClaw < 2026.4.x
        // ========================================================================
        // Debug hook removed: wildcard hooks are not supported in current OpenClaw
        // Use explicit hook names (before_agent_start, agent_end) instead
        // Auto-recall: inject memories before agent starts
        if (config.autoRecall) {
            api.logger.info('[claw-mem] Registering before_agent_start hook, autoRecall:', config.autoRecall);
            api.on('before_agent_start', async (event, ctx) => {
                api.logger.info('[claw-mem] before_agent_start triggered, session:', ctx.sessionKey);
                currentSessionId = ctx.sessionKey;
                // Wait for bridge to be ready (with 15s timeout)
                const bridgeReady = await bridge.waitForReady(15000);
                if (!bridgeReady) {
                    api.logger.warn('[claw-mem] Bridge not ready, skipping auto-recall');
                    return;
                }
                // Extract query from event
                const query = extractQueryFromEvent(event);
                if (!query) {
                    api.logger.debug?.('[claw-mem] No query extracted, skipping auto-recall');
                    return;
                }
                try {
                    // Search memories
                    api.logger.info('[claw-mem] Searching memories for:', query);
                    const result = await bridge.call('search', {
                        query,
                        limit: config.topK,
                    });
                    // Inject memories into context
                    if (result.memories && result.memories.length > 0) {
                        api.logger.info(`[claw-mem] Found ${result.memories.length} memories`);
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
                    else {
                        api.logger.info('[claw-mem] No memories found');
                    }
                }
                catch (error) {
                    api.logger.error('[claw-mem] Auto-recall error:', error?.message || String(error), error?.stack ? '\n' + error.stack : '');
                }
            });
        }
        // Auto-capture: store memories after agent ends
        if (config.autoCapture) {
            api.logger.info('[claw-mem] Registering agent_end hook, autoCapture:', config.autoCapture);
            api.on('agent_end', async (event, ctx) => {
                api.logger.info('[claw-mem] agent_end triggered, session:', ctx.sessionKey);
                // Wait for bridge to be ready (with 15s timeout)
                const bridgeReady = await bridge.waitForReady(15000);
                if (!bridgeReady) {
                    api.logger.warn('[claw-mem] Bridge not ready, skipping auto-capture');
                    return;
                }
                // Extract facts from conversation
                const facts = extractFactsFromEvent(event);
                api.logger.info(`[claw-mem] Extracted ${facts.length} facts from conversation`);
                // Store each fact
                let stored = 0;
                for (const fact of facts) {
                    try {
                        api.logger.debug?.(`[claw-mem] Storing fact: ${fact.substring(0, 80)}...`);
                        await bridge.call('store', {
                            text: fact,
                            memory_type: 'episodic',
                        });
                        stored++;
                    }
                    catch (error) {
                        api.logger.error('[claw-mem] Auto-capture error:', error?.message || String(error), error?.stack ? '\n' + error.stack : '');
                    }
                }
                if (stored > 0) {
                    api.logger.info(`[claw-mem] Auto-capture stored ${stored}/${facts.length} facts`);
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
