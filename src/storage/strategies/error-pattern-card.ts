// Error Pattern Card Strategy (v7.6.0, ADR-003)

import type { StorageStrategy, StrategyContext, StoreResult, RetrieveOptions, StrategyStats } from "../strategy-registry.js";
import type { MemoryRecord } from "../../types.js";
import type { ErrorPatternCard, ErrorSignature, CardEffectiveness } from "../../types.js";

/** Fixed tags on every card entry (findByCardId anchor, category filter) */
export const ERROR_PATTERN_TAG = "error_pattern_card";
export const CARD_SCHEMA_VERSION = "1";

// ── structured <-> storage-face metadata (ADR-003 §2) ───────────────────────
// MEMORY.md HTML comments hold flat string values; nested structures are
// JSON-stringified per key (retention precedent). Values containing "; " would
// break the comment splitter — same accepted limitation as retention.
export function encodeCardMetadata(
  card: Pick<ErrorPatternCard, "errorSignature" | "rootCauseCategory" | "verification" | "provenance" | "effectiveness"> &
    { cardId: string },
): Record<string, string> {
  const meta: Record<string, string> = {
    card_id: card.cardId,
    card_schema_version: CARD_SCHEMA_VERSION,
    error_signature: JSON.stringify(card.errorSignature),
    root_cause_category: card.rootCauseCategory,
    provenance: JSON.stringify(card.provenance),
    effectiveness: JSON.stringify(card.effectiveness),
  };
  if (card.verification) meta.verification = card.verification;
  return meta;
}

function decodeMeta<T>(raw: unknown): T | undefined {
  if (typeof raw !== "string") return undefined;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return undefined;
  }
}

/** Decode a stored entry into a structured card; null when schema is invalid. */
export function decodeErrorPatternCard(
  entry: { id?: string; timestamp: string; content: string; tags: string[]; metadata: Record<string, string> },
): ErrorPatternCard | null {
  const meta = entry.metadata;
  const cardId = meta["card_id"];
  const category = meta["root_cause_category"];
  const signature = decodeMeta<ErrorSignature>(meta["error_signature"]);
  const provenance = decodeMeta<{ source: string; author?: string }>(meta["provenance"]);
  if (!cardId || !category || !signature || !provenance) return null;
  const effectiveness = decodeMeta<CardEffectiveness>(meta["effectiveness"]) ?? {
    hitCount: 0,
    avoidedCount: 0,
    inactive: false,
  };
  return {
    cardId,
    errorSignature: signature,
    rootCauseCategory: category,
    resolution: entry.content,
    verification: meta["verification"],
    effectiveness,
    provenance,
    createdAt: entry.timestamp,
    updatedAt: meta["updated_at"],
  };
}

/**
 * Error pattern card strategy — overwrite-with-version-chain on the semantic
 * surface, mirroring the preference pattern but with its own chain directory
 * (`memory/error-pattern-cards/{cardId}.json`) so card history never shares a
 * chain with preferences. Same cardId rewrite = edit (archive old, store new).
 */
export class ErrorPatternCardStrategy implements StorageStrategy {
  readonly name = "error-pattern-card";
  readonly memoryTypes = ["error_pattern_card"];

  store(record: MemoryRecord, context: StrategyContext): StoreResult {
    const cardId = record.metadata?.card_id as string | undefined;
    if (!cardId) {
      throw new Error("[ErrorPatternCardStrategy] missing metadata.card_id — route through storeErrorPatternCard");
    }
    const chain = context.errorPatternVersionChain;
    if (!chain) {
      throw new Error("[ErrorPatternCardStrategy] missing errorPatternVersionChain in strategy context");
    }

    const existing = this.findByCardId(cardId, context);
    const storageMeta = record.metadata as Record<string, string>;

    if (existing) {
      // Edit: archive current version, then full-record update (content/tags/metadata)
      chain.archive(cardId, existing);
      const updated = context.semantic.updateRecord(existing.id!, {
        content: record.text,
        tags: record.tags,
        metadata: storageMeta,
      });
      if (!updated) {
        throw new Error(`[ErrorPatternCardStrategy] semantic update failed for card ${cardId}`);
      }
      return {
        id: existing.id!,
        strategy: this.name,
        version: chain.getLatestVersion(cardId),
        previousId: existing.id!,
      };
    }

    // New card
    context.semantic.store({
      content: record.text,
      tags: record.tags,
      metadata: storageMeta,
    });
    const version = chain.archive(cardId, record);
    return { id: record.id, strategy: this.name, version };
  }

  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[] {
    if (!context) return [];
    const all = context.semantic.getAll();
    return all
      .filter((e) => e.tags?.includes(ERROR_PATTERN_TAG))
      .filter((e) => !query || e.content.toLowerCase().includes(query.toLowerCase()))
      .slice(0, options?.limit ?? 10)
      .map((e) => ({
        id: e.id || "",
        text: e.content,
        memory_type: "error_pattern_card",
        created_at: e.timestamp,
        metadata: e.metadata,
        tags: e.tags,
      }));
  }

  getStats(context: StrategyContext): StrategyStats {
    const all = context.semantic.getAll();
    return {
      name: this.name,
      memoryCount: all.filter((e) => e.tags?.includes(ERROR_PATTERN_TAG)).length,
    };
  }

  private findByCardId(cardId: string, context: StrategyContext): MemoryRecord | null {
    const results = context.semantic.searchByTag(`card:${cardId}`);
    if (results.length === 0) return null;
    const r = results[0];
    return {
      id: r.id || "",
      text: r.content,
      memory_type: "error_pattern_card",
      created_at: r.timestamp,
      metadata: r.metadata,
      tags: r.tags,
    };
  }
}
