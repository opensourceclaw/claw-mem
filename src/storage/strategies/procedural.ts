// Procedural Strategy - Current behavior wrapper (v6.31.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Procedural strategy - current behavior wrapper for procedural storage.
 */
export class ProceduralStrategy implements StorageStrategy {
  readonly name = "procedural";
  readonly memoryTypes = ["procedural"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    context.procedural.store({
      content: record.text,
      tags: record.tags,
      metadata: record.metadata,
    });

    return { id: record.id, strategy: this.name };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    const all = context.procedural.getAll();
    return all
      .filter(e => !query || e.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, options?.limit ?? 10)
      .map(e => ({
        id: e.timestamp,
        text: e.content,
        memory_type: "procedural",
        created_at: e.timestamp,
        metadata: e.metadata,
        tags: e.tags,
      }));
  }
}
