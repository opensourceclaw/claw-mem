// Semantic Strategy - Current behavior wrapper (v6.31.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Semantic strategy - current behavior wrapper for MEMORY.md storage.
 */
export class SemanticStrategy implements StorageStrategy {
  readonly name = "semantic";
  readonly memoryTypes = ["semantic"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    context.semantic.store({
      content: record.text,
      tags: record.tags,
      metadata: record.metadata,
    });

    return { id: record.id, strategy: this.name };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    const all = context.semantic.getAll();
    return all
      .filter(e => !query || e.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, options?.limit ?? 10)
      .map(e => ({
        id: e.id || "",
        text: e.content,
        memory_type: "semantic",
        created_at: e.timestamp,
        metadata: e.metadata,
        tags: e.tags,
      }));
  }
}
