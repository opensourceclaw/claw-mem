/**
 * claw-mem v7.2.0 — OpenClaw Plugin Entry Point
 *
 * Standardized OpenClaw Plugin interface for the Memory System.
 * Wraps existing MemoryManager for storage, search, and retrieval.
 */

import { getMemoryManager, type MemoryManager } from "../src/memory_manager";

// ── Plugin Interface Types ──────────────────────────────────────────────

export interface OpenClawPlugin {
  id: string;
  version: string;
  kind: string;
  initialize(config: PluginConfig): Promise<void>;
  shutdown(): Promise<void>;
}

export interface PluginConfig {
  storagePath?: string;
  maxFileSize?: string;
  compression?: boolean;
}

export interface MemoryEntry {
  id: string;
  key: string;
  value: unknown;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface SearchResult {
  entries: MemoryEntry[];
  total: number;
  query: string;
}

export type ManageAction =
  | { type: "clear" }
  | { type: "export"; format: "json" | "markdown" }
  | { type: "import"; data: unknown };

// ── MemoryPlugin Implementation ─────────────────────────────────────────

export class MemoryPlugin implements OpenClawPlugin {
  readonly id = "claw-mem";
  readonly version = "7.2.0";
  readonly kind = "memory";

  private config: PluginConfig = {};
  private manager!: MemoryManager;
  private initialized = false;

  async initialize(config: PluginConfig): Promise<void> {
    this.config = {
      storagePath: config.storagePath ?? "~/.openclaw/memory",
      maxFileSize: config.maxFileSize ?? "10MB",
      compression: config.compression ?? true,
    };
    this.manager = getMemoryManager({ workspace: this.config.storagePath, autoDetect: false });
    this.initialized = true;
  }

  async shutdown(): Promise<void> {
    this.initialized = false;
  }

  async store(key: string, value: unknown, tags?: string[]): Promise<void> {
    this.ensureInit();
    this.manager.store(JSON.stringify(value), "episodic", tags);
  }

  async retrieve(key: string): Promise<unknown | null> {
    this.ensureInit();
    const results = this.manager.search(key, undefined, 1);
    return results.length > 0 ? results[0].content : null;
  }

  async search(query: string, limit = 10): Promise<SearchResult> {
    this.ensureInit();
    const results = this.manager.search(query, undefined, limit);
    const entries: MemoryEntry[] = results.map((r: Record<string, unknown>, i: number) => ({
      id: (r.id as string) ?? `mem-${i}`,
      key: (r.id as string) ?? `mem-${i}`,
      value: r.content ?? "",
      timestamp: (r.timestamp as number) ?? Date.now(),
      metadata: r.metadata as Record<string, unknown> | undefined,
    }));
    return { entries, total: entries.length, query };
  }

  async manage(action: ManageAction): Promise<void> {
    this.ensureInit();
    switch (action.type) {
      case "clear":
        this.manager.getStats();
        break;
      case "export":
        break;
      case "import":
        break;
    }
  }

  private ensureInit(): void {
    if (!this.initialized) {
      throw new Error("MemoryPlugin not initialized. Call initialize() first.");
    }
  }
}

export default MemoryPlugin;
