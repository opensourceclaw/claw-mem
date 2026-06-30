// Session Snapshot Strategy - Overwrite for session snapshots (v6.31.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions, StrategyStats } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Session snapshot strategy - overwrite latest snapshot for same session.
 * Only the latest snapshot per session is kept.
 */
export class SessionSnapshotStrategy implements StorageStrategy {
  readonly name = "session-snapshot";
  readonly memoryTypes = ["session_snapshot"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    // Extract session_id from record
    const sessionId = record.metadata?.session_id as string | undefined;

    if (!sessionId) {
      // No session_id, fall back to append-only
      context.episodic.store({
        content: record.text,
        tags: [...(record.tags || []), "session_snapshot"],
        metadata: record.metadata,
        id: record.id,
        timestamp: record.created_at,
      });
      return { id: record.id, strategy: this.name };
    }

    // Look for existing snapshot with same session_id
    const existing = this.findBySessionId(sessionId, context);

    if (existing) {
      // Overwrite: store new with same ID (idempotency)
      context.episodic.store({
        content: record.text,
        tags: [...(record.tags || []), "session_snapshot"],
        metadata: {
          ...record.metadata,
          overwritten_at: new Date().toISOString(),
        },
        id: existing.id, // Keep same ID for idempotency
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

    // New snapshot
    context.episodic.store({
      content: record.text,
      tags: [...(record.tags || []), "session_snapshot"],
      metadata: record.metadata,
      id: record.id,
      timestamp: record.created_at,
      session_id: sessionId,
    });
    return { id: record.id, strategy: this.name, overwritten: false };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    const limit = options?.limit ?? 20;
    const recent = context.episodic.getRecent(limit * 2);

    const results = recent
      .filter(e => e.tags?.includes("session_snapshot"))
      .filter(e => !query || e.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, limit);

    return results.map(e => ({
      id: e.id || e.timestamp,
      text: e.content,
      memory_type: "session_snapshot",
      created_at: e.timestamp,
      metadata: e.metadata,
      tags: e.tags,
    }));
  }

  getStats(context: StrategyContext): StrategyStats {
    const recent = context.episodic.getRecent(1000);
    const snapshotCount = recent.filter(e => e.tags?.includes("session_snapshot")).length;

    return {
      name: this.name,
      memoryCount: snapshotCount,
    };
  }

  private findBySessionId(sessionId: string, context: StrategyContext): { id: string } | null {
    const recent = context.episodic.getRecent(100);
    for (const entry of recent) {
      if ((entry.session_id === sessionId || entry.metadata?.session_id === sessionId) &&
          entry.tags?.includes("session_snapshot")) {
        return { id: entry.id || entry.timestamp };
      }
    }
    return null;
  }
}
