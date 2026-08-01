/** claw-mem v7.0.0 — MemoryCapability Implementation */

import { getMemoryManager, resetMemoryManager, formatMemoryContext } from "../index.js";
import type {
  IMemoryCapability, MemorySearchOptions, MemorySearchResult,
  MemoryContextResult, MemoryStatsResult, MemoryItem,
} from "./types.js";

export class MemoryCapability implements IMemoryCapability {
  readonly name = "memory" as const;
  readonly version = "7.0.0";

  private manager = getMemoryManager();
  private disposed = false;

  async store(
    content: string,
    memoryType?: string,
    tags?: string[],
    metadata?: Record<string, unknown>,
  ): Promise<{ id: string; stored: boolean }> {
    this.checkDisposed();
    const stored = this.manager.store(content, memoryType, tags, metadata);
    return { id: `mem-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`, stored };
  }

  async search(query: string, options?: MemorySearchOptions): Promise<MemorySearchResult> {
    this.checkDisposed();
    const results = this.manager.hybridSearch(query, options as any) as any;
    const items: MemoryItem[] = (results?.items ?? []).map((r: any, i: number) => ({
      id: r.id ?? `r-${i}`,
      content: r.content ?? "",
      type: r.memoryType ?? r.type ?? "episodic",
      timestamp: r.timestamp ?? Date.now(),
      tags: r.tags ?? [],
      relevance: r.score ?? r.relevance,
    }));
    return { items, total: results?.total ?? items.length };
  }

  async getContext(params?: { limit?: number }): Promise<MemoryContextResult> {
    this.checkDisposed();
    const memories = this.manager.hybridSearch("*", { limit: params?.limit ?? 10 } as any) as any;
    const memArray: Array<Record<string, unknown>> = (memories?.items ?? []).map((r: any) => ({
      content: r.content ?? "",
      type: r.memoryType ?? "episodic",
    }));
    const context = formatMemoryContext(memArray);
    return { context };
  }

  async getStats(): Promise<MemoryStatsResult> {
    this.checkDisposed();
    const stats = this.manager.getStats() as any;
    return {
      total: stats?.totalMemories ?? stats?.total ?? 0,
      byType: stats?.byType ?? {},
    };
  }

  async dispose(): Promise<void> {
    if (this.disposed) return;
    resetMemoryManager();
    this.disposed = true;
  }

  private checkDisposed(): void { if (this.disposed) throw new Error("MemoryCapability disposed"); }
}
