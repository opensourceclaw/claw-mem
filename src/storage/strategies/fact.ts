// Fact Strategy - Append with entity indexing (v6.31.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions, StrategyStats } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Fact strategy - append-only with mandatory entity indexing.
 * Entity index is persisted after each fact store.
 */
export class FactStrategy implements StorageStrategy {
  readonly name = "fact";
  readonly memoryTypes = ["fact"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    // 1. Append to episodic storage
    context.episodic.store({
      content: record.text,
      tags: [...(record.tags || []), "fact"],
      metadata: record.metadata,
      id: record.id,
      timestamp: record.created_at,
      session_id: record.metadata?.session_id as string | undefined,
    });

    // 2. Index entities (if entity index available)
    if (context.entityIndex) {
      context.entityIndex.index(record.text, record.id);
    }

    return { id: record.id, strategy: this.name };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    const limit = options?.limit ?? 10;
    const results: MemoryRecord[] = [];
    const seenIds = new Set<string>();

    // 1. Entity-enhanced search (if available and query provided)
    if (context.entityIndex && query) {
      const entityResult = context.entityIndex.search(query);
      if (entityResult) {
        // Get memories by entity's memoryIds
        for (const memoryId of entityResult.entity.memoryIds.slice(0, limit)) {
          if (!seenIds.has(memoryId)) {
            const memory = this.getMemoryById(memoryId, context);
            if (memory && memory.tags?.includes("fact")) {
              results.push(memory);
              seenIds.add(memoryId);
            }
          }
        }
      }
    }

    // 2. Keyword search as fallback/supplement
    const recent = context.episodic.getRecent(limit * 3);
    for (const entry of recent) {
      if (results.length >= limit) break;
      if (!entry.tags?.includes("fact")) continue;
      const id = entry.id || entry.timestamp;
      if (seenIds.has(id)) continue;
      if (!query || entry.content.toLowerCase().includes(query.toLowerCase())) {
        results.push({
          id,
          text: entry.content,
          memory_type: "fact",
          created_at: entry.timestamp,
          metadata: entry.metadata,
          tags: entry.tags,
        });
        seenIds.add(id);
      }
    }

    return results.slice(0, limit);
  }

  getStats(context: StrategyContext): StrategyStats {
    const recent = context.episodic.getRecent(1000);
    const factCount = recent.filter(e => e.tags?.includes("fact")).length;

    return {
      name: this.name,
      memoryCount: factCount,
    };
  }

  private getMemoryById(id: string, context: StrategyContext): MemoryRecord | null {
    const recent = context.episodic.getRecent(1000);
    for (const entry of recent) {
      if (entry.id === id || entry.timestamp === id) {
        return {
          id: entry.id || entry.timestamp,
          text: entry.content,
          memory_type: "fact",
          created_at: entry.timestamp,
          metadata: entry.metadata,
          tags: entry.tags,
        };
      }
    }
    return null;
  }
}
