// Preference Strategy - Overwrite with version chain (v6.31.0)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions, StrategyStats } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";

/**
 * Preference strategy - overwrite with version chain.
 * Preferences are stored in SemanticStorage with version history.
 */
export class PreferenceStrategy implements StorageStrategy {
  readonly name = "preference";
  readonly memoryTypes = ["preference"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    // Extract pref_key from metadata
    const prefKey = record.metadata?.pref_key as string | undefined;

    if (!prefKey) {
      // No pref_key, fall back to append with warning
      console.warn("[PreferenceStrategy] No pref_key provided, falling back to append");
      context.semantic.store({
        content: record.text,
        tags: [...(record.tags || []), "preference"],
        metadata: record.metadata,
      });
      return { id: record.id, strategy: this.name };
    }

    // Look for existing preference with same pref_key
    const existing = this.findByPrefKey(prefKey, context);

    if (existing) {
      // Archive old version to version chain
      context.versionChain.archive(prefKey, {
        id: existing.id,
        text: existing.text,
        memory_type: "preference",
        created_at: existing.created_at,
        metadata: existing.metadata,
        tags: existing.tags,
      });

      // Update in semantic storage
      context.semantic.update(existing.id, record.text);

      const newVersion = context.versionChain.getLatestVersion(prefKey);

      return {
        id: existing.id,
        strategy: this.name,
        version: newVersion,
        previousId: existing.id,
      };
    }

    // New preference
    context.semantic.store({
      content: record.text,
      tags: [...(record.tags || []), "preference", `pref:${prefKey}`],
      metadata: { ...record.metadata, pref_key: prefKey },
    });

    // Archive as version 1
    const version = context.versionChain.archive(prefKey, record);

    return {
      id: record.id,
      strategy: this.name,
      version,
    };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];

    // If query is a pref_key, return specific preference
    if (query.startsWith("pref_key:")) {
      const prefKey = query.replace("pref_key:", "");
      const pref = this.findByPrefKey(prefKey, context);
      return pref ? [pref] : [];
    }

    // General search
    const all = context.semantic.getAll();
    return all
      .filter(e => e.tags?.includes("preference"))
      .filter(e => !query || e.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, options?.limit ?? 10)
      .map(e => ({
        id: e.id || "",
        text: e.content,
        memory_type: "preference",
        created_at: e.timestamp,
        metadata: e.metadata,
        tags: e.tags,
      }));
  }

  getStats(context: StrategyContext): StrategyStats {
    const all = context.semantic.getAll();
    const prefCount = all.filter(e => e.tags?.includes("preference")).length;

    return {
      name: this.name,
      memoryCount: prefCount,
    };
  }

  private findByPrefKey(prefKey: string, context: StrategyContext): MemoryRecord | null {
    const results = context.semantic.searchByTag(`pref:${prefKey}`);
    if (results.length === 0) return null;

    const r = results[0];
    return {
      id: r.id || "",
      text: r.content,
      memory_type: "preference",
      created_at: r.timestamp,
      metadata: r.metadata,
      tags: r.tags,
    };
  }
}
