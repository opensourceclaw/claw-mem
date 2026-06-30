// Episodic Strategy - Default append-only storage (v6.31.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Default episodic strategy - append-only behavior.
 * This is the fallback for all unknown memory types.
 */
export class EpisodicStrategy implements StorageStrategy {
  readonly name = "episodic";
  readonly memoryTypes = ["episodic", "*"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    // Simple append-only behavior (existing behavior)
    context.episodic.store({
      content: record.text,
      tags: record.tags,
      metadata: record.metadata,
      id: record.id,
      timestamp: record.created_at,
      session_id: record.metadata?.session_id as string | undefined,
    });

    return { id: record.id, strategy: this.name };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    const limit = options?.limit ?? 10;
    const recent = context.episodic.getRecent(limit * 3);

    const results = recent
      .filter(e => !query || e.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, limit);

    // Convert to MemoryRecord format
    return results.map(e => ({
      id: e.id || e.timestamp,
      text: e.content,
      memory_type: "episodic",
      created_at: e.timestamp,
      metadata: e.metadata,
      tags: e.tags,
    }));
  }
}
