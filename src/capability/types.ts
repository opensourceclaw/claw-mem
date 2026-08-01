/** claw-mem v7.0.0 — Capability Layer Types */

export interface MemorySearchOptions {
  memoryType?: string;
  limit?: number;
}

export interface MemoryItem {
  id: string;
  content: string;
  type: string;
  timestamp: number;
  tags?: string[];
  relevance?: number;
}

export interface MemorySearchResult {
  items: MemoryItem[];
  total: number;
}

export interface MemoryContextResult {
  context: string;
}

export interface MemoryStatsResult {
  total: number;
  byType: Record<string, number>;
}

export interface IMemoryCapability {
  readonly name: "memory";
  readonly version: string;

  store(content: string, memoryType?: string, tags?: string[], metadata?: Record<string, unknown>): Promise<{ id: string; stored: boolean }>;
  search(query: string, options?: MemorySearchOptions): Promise<MemorySearchResult>;
  getContext(params?: { limit?: number }): Promise<MemoryContextResult>;
  getStats(): Promise<MemoryStatsResult>;
  dispose(): Promise<void>;
}
