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
        debug: (...args: any[]) => void;
    };
    registerTool(tool: any, handler: (params: any) => Promise<any>): void;
    on(eventName: string, handler: (event: any, ctx: any) => Promise<any | void>): void;
    registerService(service: {
        id: string;
        start: () => Promise<void>;
        stop: () => Promise<void>;
    }): void;
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
declare const plugin: PluginDefinition;
export default plugin;
//# sourceMappingURL=index.d.ts.map