// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * TieredDecayEngine (F2 - v4.7.0)
 *
 * Three-tier storage decay: HOT (current session), WARM (recently accessed),
 * COLD (long-term). Evicts based on composite score of recency, frequency,
 * and importance.
 */

import type { DecayConfig } from "./functions";

// ── External type stubs ────────────────────────────────────────────────

/**
 * Minimal interface for a storage backend that TieredDecayEngine interacts with.
 * In the full system this is SemanticStorage.
 */
export interface StorageBackend {
  filePath: string;
  getAll(): Record<string, unknown>[];
  _formatMemory(mem: Record<string, unknown>): string;
}

/**
 * Minimal interface for an LLM provider capable of text generation.
 */
export interface LLMProvider {
  generate(prompt: string, options?: { maxTokens?: number; system?: string }): string;
}

// ── Prompt ─────────────────────────────────────────────────────────────

const IMPORTANCE_PROMPT =
  "Rate the importance of this memory on a scale of 0.0 to 1.0 " +
  "(0=trivial, 0.5=useful, 0.8=very important, 1.0=critical). " +
  "Return only the number.\n\nMemory: {content}";

// ── Enum ───────────────────────────────────────────────────────────────

export enum TierLevel {
  HOT = "hot",
  WARM = "warm",
  COLD = "cold",
}

// ── Helpers ────────────────────────────────────────────────────────────

function nowIso(): string {
  return new Date().toISOString();
}

// ── Engine ─────────────────────────────────────────────────────────────

export class TieredDecayEngine {
  /** Track access timestamps for recency scoring */
  private _accessLog: Record<string, number[]> = {};
  private _importanceCache: Record<string, number> = {};
  private _lastCycle: number = 0;

  hotTtl: number;
  warmTtl: number;
  coldTtl: number;
  maxHot: number;
  maxWarm: number;
  maxCold: number;

  constructor(
    private _storage: StorageBackend,
    private _config?: DecayConfig,
    private _llmProvider?: LLMProvider,
    hotTtl: number = 3600,
    warmTtlDays: number = 7,
    coldTtlDays: number = 30,
    maxHot: number = 100,
    maxWarm: number = 500,
    maxCold: number = 2000,
  ) {
    this.hotTtl = hotTtl; // seconds
    this.warmTtl = warmTtlDays * 86400;
    this.coldTtl = coldTtlDays * 86400;
    this.maxHot = maxHot;
    this.maxWarm = maxWarm;
    this.maxCold = maxCold;
  }

  // ── classification ───────────────────────────────────────────────────

  /** Classify a single memory into a tier based on its age and metadata. */
  classify(memory: Record<string, unknown>): TierLevel {
    const meta = (memory.metadata as Record<string, string>) || {};

    // Deprecated memories go directly to COLD for immediate eviction
    if (meta.deprecated === "true" || meta.deprecated === "True" || meta.deprecated === "1") {
      return TierLevel.COLD;
    }

    // Use creation timestamp for age calculation
    const createdRaw =
      (memory.created_at as string) || (memory.timestamp as string) || nowIso();
    const createdDt = new Date(createdRaw.replace("Z", "+00:00"));
    const ageSeconds = (Date.now() - createdDt.getTime()) / 1000;

    if (ageSeconds <= this.hotTtl) return TierLevel.HOT;
    if (ageSeconds <= this.warmTtl) return TierLevel.WARM;
    return TierLevel.COLD;
  }

  /**
   * Record an access, potentially promoting the memory tier.
   *
   * Promotion rules:
   *   COLD -> WARM if recently accessed (resets TTL)
   *   WARM -> HOT if accessed within hot TTL
   *   HOT stays HOT
   */
  promote(memoryId: string): TierLevel | null {
    if (!memoryId) return null;

    const now = Date.now() / 1000;
    if (!this._accessLog[memoryId]) {
      this._accessLog[memoryId] = [];
    }
    this._accessLog[memoryId].push(now);

    // Look up current memory
    const allM = this._storage.getAll();
    const mem = allM.find((m) => (m.id as string) === memoryId);
    if (!mem) return null;

    const current = this.classify(mem);
    if (current === TierLevel.HOT || current === TierLevel.WARM) return current;

    // COLD -> WARM promotion: record access and return
    const freq = this._accessFrequency(memoryId);
    return freq >= 2 ? TierLevel.WARM : TierLevel.COLD;
  }

  // ── importance scoring ───────────────────────────────────────────────

  /** Score memory importance (0.0 - 1.0). Uses cached LLM score or rule-based fallback. */
  getImportance(memory: Record<string, unknown>): number {
    const mid = (memory.id as string) || "";
    if (mid && mid in this._importanceCache) return this._importanceCache[mid];

    // Try LLM scoring
    if (this._llmProvider) {
      try {
        const content = (memory.content as string) || "";
        const scoreText = this._llmProvider.generate(
          IMPORTANCE_PROMPT.replace("{content}", content),
          { maxTokens: 16 },
        );
        const score = this._parseScore(scoreText);
        if (score !== null) {
          if (mid) this._importanceCache[mid] = score;
          return score;
        }
      } catch {
        // fall through to rule-based
      }
    }

    // Rule-based fallback
    const score = this._ruleImportance(memory);
    if (mid) this._importanceCache[mid] = score;
    return score;
  }

  private _parseScore(text: string): number | null {
    if (!text) return null;
    const score = parseFloat(text.trim());
    if (isNaN(score)) return null;
    return Math.max(0.0, Math.min(1.0, score));
  }

  /** Rule-based importance fallback when LLM is unavailable. */
  private _ruleImportance(memory: Record<string, unknown>): number {
    const content = (memory.content as string) || "";
    const tags = (memory.tags as string[]) || [];
    const meta = (memory.metadata as Record<string, string>) || {};
    let score = 0.3; // baseline

    // Longer content may be more important
    if (content.length > 200) score += 0.15;
    else if (content.length > 50) score += 0.05;

    // Presence of tags
    if (tags.length > 0) score += 0.05;

    // Critical tags
    const criticalKeywords = ["critical", "important", "essential", "preference", "rule"];
    if (tags.some((t) => criticalKeywords.some((kw) => t.toLowerCase().includes(kw)))) {
      score += 0.2;
    }

    // Explicit importance in metadata
    if (meta.importance !== undefined) {
      const parsed = parseFloat(meta.importance);
      if (!isNaN(parsed)) score = parsed;
    }

    return Math.max(0.0, Math.min(1.0, score));
  }

  // ── access metrics ───────────────────────────────────────────────────

  private _accessFrequency(memoryId: string): number {
    const timestamps = this._accessLog[memoryId] || [];
    const now = Date.now() / 1000;
    const cutoff = now - 14 * 86400;
    return timestamps.filter((ts) => ts >= cutoff).length;
  }

  /** Seconds since last access (lower = more recent). */
  private _accessRecency(memoryId: string): number {
    const timestamps = this._accessLog[memoryId] || [];
    if (timestamps.length === 0) return Infinity;
    return Date.now() / 1000 - Math.max(...timestamps);
  }

  // ── eviction ─────────────────────────────────────────────────────────

  /**
   * Composite eviction score. Lower score = evict first.
   *
   * Formula: norm_recency * 0.4 + norm_freq * 0.3 + importance * 0.3
   */
  private _compositeScore(memory: Record<string, unknown>): number {
    const mid = (memory.id as string) || "";
    const importance = this.getImportance(memory);

    const recency = this._accessRecency(mid);
    let normRec: number;
    if (!isFinite(recency) || recency <= 0) {
      normRec = 0.0;
    } else {
      const ttlX2 = this.coldTtl * 2;
      normRec = Math.max(0.0, 1.0 - recency / ttlX2);
    }

    const freq = this._accessFrequency(mid);
    const normFreq = Math.min(1.0, freq / 5.0); // cap at 5 accesses

    return normRec * 0.4 + normFreq * 0.3 + importance * 0.3;
  }

  /**
   * Evict low-score memories, preferentially from COLD tier.
   * Always evicts deprecated memories first, then applies composite scoring.
   * Returns count of evicted memories.
   */
  evict(): number {
    const allMemories = this._storage.getAll();

    const evictedIds: string[] = [];
    const nonEvicted: Record<string, unknown>[] = [];

    // Phase 1: always evict deprecated
    for (const m of allMemories) {
      const meta = (m.metadata as Record<string, string>) || {};
      if (meta.deprecated === "true" || meta.deprecated === "True" || meta.deprecated === "1") {
        evictedIds.push((m.id as string) || "");
      } else {
        nonEvicted.push(m);
      }
    }

    // Respect max tier capacities
    const tiers: Record<TierLevel, Record<string, unknown>[]> = {
      [TierLevel.HOT]: [],
      [TierLevel.WARM]: [],
      [TierLevel.COLD]: [],
    };
    for (const m of nonEvicted) {
      const tier = this.classify(m);
      tiers[tier].push(m);
    }

    // Evict from WARM and COLD tiers if over capacity
    const maxMap: Record<TierLevel, number> = {
      [TierLevel.HOT]: this.maxHot,
      [TierLevel.WARM]: this.maxWarm,
      [TierLevel.COLD]: this.maxCold,
    };

    for (const [tier, maxCap] of Object.entries(maxMap)) {
      if (tier === TierLevel.HOT) continue; // Don't evict from HOT tier
      const tierMems = tiers[tier as TierLevel];
      const overflow = tierMems.length - maxCap;
      if (overflow <= 0) continue;

      // Score and sort: lowest score first
      const scored = tierMems.map((m) => ({ score: this._compositeScore(m), mem: m }));
      scored.sort((a, b) => a.score - b.score);
      for (const { mem } of scored.slice(0, overflow)) {
        evictedIds.push((mem.id as string) || "");
      }
    }

    if (evictedIds.length === 0) return 0;

    // Mark evicted memories as deprecated
    const validIds = new Set(evictedIds.filter(Boolean));
    for (const m of allMemories) {
      const id = m.id as string;
      if (validIds.has(id)) {
        const meta = (m.metadata as Record<string, string>) || {};
        meta.deprecated = "true";
        m.metadata = meta;
      }
    }

    this._rewriteFile(this._storage, allMemories);
    return validIds.size;
  }

  // ── full cycle ───────────────────────────────────────────────────────

  /** Run a complete decay cycle: classify, score, evict. Returns stats dict. */
  runCycle(): Record<string, unknown> {
    const t0 = Date.now();
    const allM = this._storage.getAll();

    // Classify all
    const tierCounts: Record<TierLevel, number> = {
      [TierLevel.HOT]: 0,
      [TierLevel.WARM]: 0,
      [TierLevel.COLD]: 0,
    };
    for (const m of allM) {
      const tier = this.classify(m);
      tierCounts[tier]++;
    }

    // Evict
    const evicted = this.evict();

    const duration = Math.round(Date.now() - t0);
    this._lastCycle = Date.now() / 1000;

    return {
      total: allM.length,
      hot: tierCounts[TierLevel.HOT],
      warm: tierCounts[TierLevel.WARM],
      cold: tierCounts[TierLevel.COLD],
      evicted,
      durationMs: duration,
    };
  }

  /** Rewrite the MEMORY.md file with updated memories. */
  private _rewriteFile(storage: StorageBackend, memories: Record<string, unknown>[]): void {
    const fs = require("fs") as typeof import("fs");
    const lines: string[] = [];
    lines.push("# MEMORY.md\n");
    lines.push("<!-- Core Memory - Permanent Storage -->\n");
    for (const mem of memories) {
      lines.push(storage._formatMemory(mem));
    }
    fs.writeFileSync(storage.filePath, lines.join("\n"), "utf-8");
  }

  toString(): string {
    return `TieredDecayEngine(hot=${this.hotTtl}s, warm=${this.warmTtl / 86400}d, cold=${this.coldTtl / 86400}d)`;
  }
}
