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
            // Set PYTHONPATH to include src directory
            const workspaceDir = this.config.workspaceDir || process.cwd();
            const srcDir = path.join(workspaceDir, 'src');
            // Spawn Python Bridge process with separate arguments
            this.process = spawn(pythonPath, ['-m', bridgeModule], {
                stdio: ['pipe', 'pipe', 'pipe'],
                cwd: workspaceDir,
                env: {
                    ...process.env,
                    PYTHONPATH: srcDir,
                },
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
            // Initialize bridge
            this.call('initialize', { config: this.config })
                .then(() => {
                this.ready = true;
                this.starting = false;
                this.logger.info('[claw-mem bridge] Started successfully');
                resolve();
            })
                .catch((err) => {
                this.logger.error('[claw-mem bridge] Failed to initialize:', err);
                this.starting = false;
                reject(err);
            });
        });
    }
    /**
     * Call a method on the bridge
     */
    async call(method, params) {
        return new Promise((resolve, reject) => {
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
                this.logger.debug(`[claw-mem bridge] → ${requestStr.trim()}`);
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
            return lastMessage.content || '';
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
    // Extract important facts from conversation
    // This is a simple implementation - can be enhanced with LLM
    const facts = [];
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
// Plugin Definition
// ============================================================================
const plugin = {
    id: 'claw-mem',
    name: 'Claw Memory System',
    description: 'Three-tier memory system for OpenClaw (Local-First)',
    version: '2.0.0',
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
        // Register Tools
        // ========================================================================
        api.registerTool({
            name: 'memory_search',
            label: 'Memory Search',
            description: 'Search through memories stored in claw-mem. Use when you need context about past conversations, decisions, or learned information.',
            parameters: {
                type: 'object',
                properties: {
                    query: { type: 'string', description: 'Search query' },
                    limit: { type: 'number', description: 'Max results', default: config.topK },
                },
                required: ['query'],
            },
        }, async (params) => {
            if (!bridge.isReady()) {
                return { error: 'Bridge not initialized' };
            }
            try {
                const result = await bridge.call('search', params);
                return result;
            }
            catch (error) {
                api.logger.error('[claw-mem] Search error:', error);
                return { error: error.message };
            }
        });
        api.registerTool({
            name: 'memory_store',
            label: 'Memory Store',
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
        }, async (params) => {
            if (!bridge.isReady()) {
                return { error: 'Bridge not initialized' };
            }
            try {
                const result = await bridge.call('store', params);
                return result;
            }
            catch (error) {
                api.logger.error('[claw-mem] Store error:', error);
                return { error: error.message };
            }
        });
        api.registerTool({
            name: 'memory_get',
            label: 'Memory Get',
            description: 'Get a specific memory by ID. Note: This operation is not supported by the current MemoryManager. Use memory_search instead.',
            parameters: {
                type: 'object',
                properties: {
                    id: { type: 'string', description: 'Memory ID' },
                },
                required: ['id'],
            },
        }, async (params) => {
            return { error: 'MemoryManager does not support get() method. Use memory_search instead.' };
        });
        api.registerTool({
            name: 'memory_forget',
            label: 'Memory Forget',
            description: 'Delete a memory by ID. Note: This operation is not supported by the current MemoryManager.',
            parameters: {
                type: 'object',
                properties: {
                    id: { type: 'string', description: 'Memory ID to delete' },
                },
                required: ['id'],
            },
        }, async (params) => {
            return { error: 'MemoryManager does not support delete() method.' };
        });
        // ========================================================================
        // Register Hooks
        // ========================================================================
        // Auto-recall: inject memories before agent starts
        if (config.autoRecall) {
            api.on('before_agent_start', async (event, ctx) => {
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
                }
                catch (error) {
                    api.logger.error('[claw-mem] Auto-recall error:', error);
                }
            });
        }
        // Auto-capture: store memories after agent ends
        if (config.autoCapture) {
            api.on('agent_end', async (event, ctx) => {
                // Extract facts from conversation
                const facts = extractFactsFromEvent(event);
                // Store each fact
                for (const fact of facts) {
                    try {
                        await bridge.call('store', {
                            text: fact,
                            memory_type: 'episodic',
                        });
                    }
                    catch (error) {
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
