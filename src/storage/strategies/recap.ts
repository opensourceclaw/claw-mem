// Recap Strategy - Store session recap summaries (v6.33.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Recap strategy - stores session recap summaries.
 * Keeps the latest recap per session for quick recovery.
 */
export class RecapStrategy implements StorageStrategy {
  readonly name = "recap";
  readonly memoryTypes = ["session_recap"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    // Extract session_id from record
    const sessionId = record.metadata?.session_id as string | undefined;

    if (!sessionId) {
      // No session_id, fall back to episodic storage
      context.episodic.store({
        content: record.text,
        tags: [...(record.tags || []), "session_recap"],
        metadata: record.metadata,
        id: record.id,
        timestamp: record.created_at,
      });
      return { id: record.id, strategy: this.name };
    }

    // Look for existing recap with same session_id
    const existing = this.findBySessionId(sessionId, context);

    if (existing) {
      // Overwrite: store new with same ID (idempotency)
      context.episodic.store({
        content: record.text,
        tags: [...(record.tags || []), "session_recap"],
        metadata: {
          ...record.metadata,
          overwritten_at: new Date().toISOString(),
        },
        id: existing.id,
        timestamp: record.created_at,
        session_id: sessionId,
      });
      return {
        id: existing.id,
        strategy: this.name,
        previousId: existing.id,
        overwritten: true,
      };
    }

    // New recap: store normally
    context.episodic.store({
      content: record.text,
      tags: [...(record.tags || []), "session_recap"],
      metadata: record.metadata,
      id: record.id,
      timestamp: record.created_at,
      session_id: sessionId,
    });

    return { id: record.id, strategy: this.name };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    // Retrieve by session_id if in query
    if (query.includes("session_id:")) {
      const sessionIdMatch = query.match(/session_id:([^\s]+)/);
      if (sessionIdMatch) {
        const sessionId = sessionIdMatch[1];
        const record = this.findBySessionId(sessionId, context);
        return record ? [record] : [];
      }
    }

    // Retrieve latest recaps
    const allEntries = context.episodic.getAll();
    const recaps = allEntries
      .filter((e: any) => e.tags?.includes("session_recap"))
      .sort((a: any, b: any) => (b.timestamp || 0) - (a.timestamp || 0))
      .slice(0, options?.limit || 1);

    // Convert EpisodicEntry to MemoryRecord
    return recaps.map((e: any) => ({
      id: e.id || "",
      text: e.content || "",
      memory_type: "session_recap" as const,
      created_at: e.timestamp || new Date().toISOString(),
      metadata: e.metadata || {},
      tags: e.tags || [],
    }));
  }

  getStats(context: StrategyContext): { name: string; memoryCount: number; lastUpdated?: string } {
    const allEntries = context.episodic.getAll();
    const recaps = allEntries.filter((e: any) => e.tags?.includes("session_recap"));
    return {
      name: this.name,
      memoryCount: recaps.length,
      lastUpdated: recaps.length > 0 ? recaps[0].timestamp?.toString() : undefined,
    };
  }

  /**
   * Find recap by session ID
   */
  private findBySessionId(sessionId: string, context: StrategyContext): MemoryRecord | null {
    const allEntries = context.episodic.getAll();
    const recap = allEntries.find((e: any) => e.tags?.includes("session_recap") && e.session_id === sessionId);
    if (!recap) return null;

    return {
      id: recap.id || "",
      text: recap.content || "",
      memory_type: "session_recap" as const,
      created_at: recap.timestamp || new Date().toISOString(),
      metadata: recap.metadata || {},
      tags: recap.tags || [],
    };
  }
}