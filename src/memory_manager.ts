// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem 6.33.0 — MemoryManager (TypeScript)
 *
 * Core orchestrator: storage, retrieval, gating, decay, graph, compression.
 * Lazy-loads subsystems on first access to keep startup fast.
 */

import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { EpisodicStorage } from "./storage/episodic.js";
import { SemanticStorage } from "./storage/semantic.js";
import { ProceduralStorage } from "./storage/procedural.js";
import { GroundTruthStore } from "./storage/ground_truth.js";
import { InMemoryIndex } from "./storage/index.js";
// MemoryEntry type for indexing
interface MemoryEntry { id: string; content: string; }
import { MemoryConfig } from "./config.js";

/** v6.36.0: Maximum working memory size to prevent unbounded growth */
const WORKING_MAX_SIZE = 500;
import { ComponentFactory, getDefaultFactory } from "./factories.js";
import { ConstitutionStore } from "./constitution.js";
import { TranscriptStorage, type TranscriptEntry, type TranscriptMatch, type TranscriptConfig } from "./transcript/index.js";
import { HybridRetriever, type HybridSearchOptions, type HybridSearchResult } from "./retrieval/hybrid-retriever.js";
import { EntityIndex } from "./entity/entity-index.js";
import { EntityExtractor } from "./entity/entity-extractor.js";
import { EntityResolver } from "./entity/entity-resolver.js";
import type { EntityRecord, EntitySearchResult, ResolutionResult, EntityConfig, DEFAULT_ENTITY_CONFIG } from "./types.js";
import { StrategyRegistry } from "./storage/strategy-registry.js";
import { VersionChain } from "./storage/version-chain.js";
import type { VersionEntry } from "./storage/version-chain.js";
import { EpisodicStrategy, SessionSnapshotStrategy, FactStrategy, PreferenceStrategy, SemanticStrategy, ProceduralStrategy } from "./storage/strategies/index.js";
// Import types only to avoid circular deps
import type { WriteTimeGating } from "./gating/write_time_gating.js";
import type { ThreeTierRetriever } from "./retrieval/three_tier.js";
import type { HybridRouter } from "./retrieval/hybrid_router.js";
import type { TieredDecayEngine } from "./deprecated/decay/tiered_decay.js";
import type { ConceptMediatedGraph } from "./graph/concept_graph.js";
import type { MemoryCompressorV2 } from "./compression/memory_compression_v2.js";
import type { CompressionSpectrum } from "./compression/spectrum.js";
import type { SessionSnapshot } from "./session/snapshot-types.js";

let _silent = false;
export function setSilent(v: boolean): void { _silent = v; }
function log(msg: string): void { if (!_silent) console.log(msg); }

export class MemoryManager {
  config: MemoryConfig;
  workspace: string;
  sessionId: string | null = null;

  // ── eager storage ──
  private _episodic!: EpisodicStorage;
  private _semantic!: SemanticStorage;
  private _procedural!: ProceduralStorage;
  private _gt: GroundTruthStore | null = null;
  private _index!: InMemoryIndex;
  private _working: unknown[] = [];
  private _factory: ComponentFactory;

  // ── lazy subsystems ──
  private _writeGating: WriteTimeGating | null = null;
  private _decayEngine: TieredDecayEngine | null = null;
  private _retriever: ThreeTierRetriever | null = null;
  private _hybridRouter: HybridRouter | null = null;
  private _graph: ConceptMediatedGraph | null = null;
  private _compressor: MemoryCompressorV2 | null = null;
  private _compressionSpectrum: CompressionSpectrum | null = null;
  private _transcript: TranscriptStorage | null = null;
  private _hybridRetriever: HybridRetriever | null = null;
  private _entityIndex: EntityIndex | null = null;
  private _strategyRegistry: StrategyRegistry | null = null;
  private _versionChain: VersionChain | null = null;
  // Future: private _injector: ContextInjector | null = null;
  // Future: private _confidenceGate: ConfidenceGate | null = null;

  constructor(opts?: Partial<{
    workspace?: string; config?: MemoryConfig; autoDetect?: boolean;
    enableGating?: boolean; enableDecay?: boolean; enableGraph?: boolean;
    enableCompression?: boolean; factory?: ComponentFactory;
  }>) {
    this._factory = opts?.factory ?? getDefaultFactory();
    this.config = opts?.config ?? new MemoryConfig(opts);

    if (this.config.autoDetect) {
      this.workspace = this.config.workspace || this._detectWorkspace();
    } else {
      this.workspace = this.config.workspace || path.join(os.homedir(), ".openclaw", "workspace");
    }
    // Ensure workspace exists
    fs.mkdirSync(this.workspace, { recursive: true });

    // Eager-init core storage + index
    this._episodic = new EpisodicStorage(this.workspace);
    this._semantic = new SemanticStorage(this.workspace);
    this._procedural = new ProceduralStorage(this.workspace);
    this._index = new InMemoryIndex(this.workspace);

    // Stats tracking
    this._searchCount = 0;
    this._storeCount = 0;
    this._cacheHits = 0;

    // Async BM25 warmup (non-blocking)
    this._bm25Ready = false;
    this._startAsyncBuild();

    // v6.0.2: Constitution Store
    this.constitutionStore = new ConstitutionStore(this.workspace);
    this._migrateCriticalRulesToConstitution();

    // v6.28.0: Transcript Storage
    const transcriptConfig = (this.config as any).transcript as Partial<TranscriptConfig> | undefined;
    if (transcriptConfig?.enabled !== false) {
      this._transcript = new TranscriptStorage(this.workspace, transcriptConfig);
      // Clean up expired transcripts on startup
      const deleted = this._transcript.cleanupExpired();
      if (deleted > 0) {
        log(`Cleaned up ${deleted} expired transcript directories`);
      }
    }

    // v6.29.0: Hybrid Retriever (lazy initialization)
    this._hybridRetriever = null;

    // v6.30.0: Entity Index (lazy initialization)
    const entityConfig = (this.config as any).entityIndex as Partial<EntityConfig> | undefined;
    if (entityConfig?.enabled !== false) {
      this._entityIndex = new EntityIndex({
        extractor: new EntityExtractor({
          customRules: entityConfig?.customRules,
          customStopwords: entityConfig?.customStopwords,
        }),
        resolver: new EntityResolver({
          customAliases: entityConfig?.customAliases,
        }),
      });

      // 6.33.0: Enable entity index persistence
      const indexDir = path.join(this.workspace, ".claw-mem-index");
      this._entityIndex.enablePersistence(indexDir);
      this._entityIndex.load();
    }

    // 6.33.0: Version Chain for preferences
    this._versionChain = new VersionChain(this.workspace);

    // 6.33.0: Strategy Registry
    this._strategyRegistry = new StrategyRegistry(new EpisodicStrategy());
    this._registerStrategies();

    log(`claw-mem TS 6.33.0 initialized, workspace: ${this.workspace}`);
  }

  // v5.1.0: Constitution Store — 3-layer persistent identity
  constitutionStore!: ConstitutionStore;
  private _constitutionInjected = false;

  injectConstitution(): void {
    if (this._constitutionInjected) return;
    const entries = this.constitutionStore.assemble();
    for (const e of entries) {
      this._working.push({
        id: e.id, content: e.content,
        type: "constitution",
        tags: [...e.tags, "constitution", `L${e.layer}`],
        layer: e.layer,
        timestamp: e.createdAt,
        source: e.source,
      });
    }
    this._constitutionInjected = true;
  }

  private _migrateCriticalRulesToConstitution(): void {
    const rulesPath = path.join(this.workspace, "critical_rules.json");
    const flagPath = rulesPath + ".migrated_to_constitution";
    if (fs.existsSync(flagPath)) return;
    if (!fs.existsSync(rulesPath)) return;
    try {
      const data = JSON.parse(fs.readFileSync(rulesPath, "utf-8")) as Record<string, { content?: string; text?: string }>;
      let count = 0;
      for (const [id, entry] of Object.entries(data)) {
        const content = entry.content || entry.text || "";
        if (!content) continue;
        this.constitutionStore.promoteToL2(content, ["legacy_critical", "migrated_v5.1"], { _migrated_from: "critical_rules", _migrated_rule_id: id });
        count++;
      }
      fs.writeFileSync(flagPath, JSON.stringify({ migrated_at: new Date().toISOString(), count }), "utf-8");
      if (count > 0) log(`Migrated ${count} critical_rules to ConstitutionStore L2`);
    } catch { /* best-effort */ }
  }

  private _searchCount = 0;
  private _storeCount = 0;
  private _cacheHits = 0;
  private _bm25Ready = false;
  private _tokenCount = 0;

  private _estimateTokens(text: string): number {
    const cjkChars = (text.match(/[\u4e00-\u9fff\u3400-\u4dbf]/g) || []).length;
    const latinChars = text.length - cjkChars;
    return Math.ceil(cjkChars / 1.5 + latinChars / 4);
  }

  private _startAsyncBuild(): void {
    // Defer index build to next tick so constructor returns fast
    // Fallback substring search works before index is built
    setTimeout(() => {
      try { this.buildIndex(); this._bm25Ready = true; }
      catch { /* best effort */ }
    }, 10);
  }

  // ── storage accessors ──────────────────────────────────────────

  get episodic(): EpisodicStorage { return this._episodic; }
  get semantic(): SemanticStorage { return this._semantic; }
  get procedural(): ProceduralStorage { return this._procedural; }
  get groundTruth(): GroundTruthStore {
    if (!this._gt) this._gt = new GroundTruthStore();
    return this._gt;
  }
  get index(): InMemoryIndex { return this._index; }
  get workingMemory(): unknown[] { return this._working; }

  // ── feature accessors (lazy via require() for fast startup) ────
  // Using sync require() pattern because tsc compiles to CommonJS
  // modules. Async dynamic import() would require getters to become
  // async, breaking the sync API expected by callers.

  get writeGating(): WriteTimeGating | null {
    if (!this.config.enableGating) return null;
    if (!this._writeGating) {
      const { WriteTimeGating } = require("./gating/write_time_gating");
      this._writeGating = new WriteTimeGating();
    }
    return this._writeGating;
  }

  get decayEngine(): TieredDecayEngine | null {
    if (!this.config.enableDecay) return null;
    if (!this._decayEngine) {
      const { TieredDecayEngine } = require("./deprecated/decay/tiered_decay");
      this._decayEngine = new TieredDecayEngine(this.config);
    }
    return this._decayEngine;
  }

  get retriever(): ThreeTierRetriever {
    if (!this._retriever) {
      const r = require("./retrieval/three_tier");
      this._retriever = new r.ThreeTierRetriever();
    }
    return this._retriever!;
  }

  get hybridRouter(): HybridRouter {
    if (!this._hybridRouter) {
      const r = require("./retrieval/hybrid_router");
      this._hybridRouter = new r.HybridRouter();
    }
    return this._hybridRouter!;
  }

  get graph(): ConceptMediatedGraph | null {
    if (!this.config.enableGraph) return null;
    if (!this._graph) {
      const { ConceptMediatedGraph } = require("./graph/concept_graph");
      this._graph = new ConceptMediatedGraph();
    }
    return this._graph;
  }

  get compressor(): MemoryCompressorV2 | null {
    if (!this.config.enableCompression) return null;
    if (!this._compressor) {
      const { MemoryCompressorV2 } = require("./compression/memory_compression_v2");
      this._compressor = new MemoryCompressorV2();
    }
    return this._compressor;
  }

  get compressionSpectrum(): CompressionSpectrum | null {
    if (!this.config.enableCompression) return null;
    if (!this._compressionSpectrum) {
      const { CompressionSpectrum } = require("./compression/spectrum");
      this._compressionSpectrum = new CompressionSpectrum();
    }
    return this._compressionSpectrum;
  }

  // ── core operations ─────────────────────────────────────────────

  store(content: string, memoryType: string = "episodic",
        tags: string[] = [], metadata: Record<string, unknown> = {}): boolean {
    if (!content?.trim()) return false;

    const id = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    const timestamp = new Date().toISOString();

    // 6.33.0: Strategy-based dispatch
    if (this._strategyRegistry) {
      const record: import("./types.js").MemoryRecord = {
        id,
        text: content,
        memory_type: memoryType as any,
        created_at: timestamp,
        metadata: { ...metadata, session_id: this.sessionId || undefined },
        tags,
      };

      try {
        const strategy = this._strategyRegistry.resolve(memoryType);
        const context = this._buildStrategyContext();
        const result = strategy.store(record, context);

        // Incremental BM25 index update
        if (this._index.built) {
          this._index.addMemory(content, result.id, true);
        }

        // v6.30.0: Auto-index entities (for non-fact types; fact strategy handles this internally)
        if (this._entityIndex && memoryType !== "fact") {
          try {
            this._entityIndex.index(content, result.id);
          } catch {
            // Non-blocking: entity indexing failure should not affect storage
          }
        }

        this._storeCount++;
        this._tokenCount += this._estimateTokens(content);

        return true;
      } catch (err) {
        console.error(`[claw-mem] Strategy store failed:`, err);
        return false;
      }
    }

    // Fallback: Legacy store (should not reach here in normal operation)
    const record = {
      content, tags, metadata,
      id,
      timestamp,
      session_id: this.sessionId || undefined,
    };

    try {
      switch (memoryType) {
        case "episodic": this._episodic.store(record); break;
        case "semantic": this._semantic.store(record); break;
        case "procedural": this._procedural.store(record); break;
        default: return false;
      }
      this._working.push(record);
      // v6.36.0: LRU eviction for working memory
      if (this._working.length > WORKING_MAX_SIZE) {
        this._working = this._working.slice(-WORKING_MAX_SIZE);
      }
      this._storeCount++;
      this._tokenCount += this._estimateTokens(content);

      // Incremental index update
      try {
        if (this._index.built) {
          this._index.addMemory(content, record.id, true);
        }
      } catch { /* index update is best-effort */ }

      // v6.30.0: Auto-index entities
      if (this._entityIndex) {
        try {
          this._entityIndex.index(content, record.id);
        } catch {
          // Non-blocking: entity indexing failure should not affect storage
        }
      }

      return true;
    } catch {
      return false;
    }
  }

  /** Batch store episodic memories with a single file write. */
  storeBatch(contents: Array<{ content: string; tags?: string[]; metadata?: Record<string, unknown> }>): number {
    if (contents.length === 0) return 0;

    const records = contents.map((c) => ({
      content: c.content,
      tags: c.tags ?? [],
      metadata: c.metadata ?? {},
      id: `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      timestamp: new Date().toISOString(),
      session_id: this.sessionId || undefined,
    }));

    try {
      this._episodic.storeBatch(records);
      for (const r of records) {
        this._working.push(r);
        this._storeCount++;
        this._tokenCount += this._estimateTokens(r.content);
        try {
          if (this._index.built) {
            this._index.addMemory(r.content, r.id, true);
          }
        } catch { /* best-effort */ }
      }
      // v6.36.0: LRU eviction for working memory
      if (this._working.length > WORKING_MAX_SIZE) {
        this._working = this._working.slice(-WORKING_MAX_SIZE);
      }
      return records.length;
    } catch {
      return 0;
    }
  }

  // v6.15.0: Upgraded search cache with LRU eviction and configurable limits
  private _searchCache = new Map<string, { results: Array<Record<string, unknown>>; ts: number; lastAccess: number }>();
  private _cacheTTL = 5000;
  private _cacheMaxSize = 500;

  search(query: string, memoryType?: string, limit = 10): Array<Record<string, unknown>> {
    if (!query?.trim()) return [];
    this._searchCount++;

    // Check cache with access-time update for LRU tracking
    const cacheKey = `${query}::${memoryType || "all"}::${limit}`;
    const cached = this._searchCache.get(cacheKey);
    if (cached && Date.now() - cached.ts < this._cacheTTL) {
      this._cacheHits++;
      cached.lastAccess = Date.now();
      return cached.results.slice(0, limit);
    }

    // v6.36.0: Index-first strategy - use index when available, avoid full scan
    if (this._index.built) {
      const ids = this._index.search(query, limit * 3);
      const idSet = new Set(ids);

      // Load by IDs from episodic (most recent first)
      const recent = this._episodic.getRecent(ids.length * 2);
      const indexedResults: Array<Record<string, unknown>> = [];
      for (const m of recent) {
        const recordId = (m as any).id || (m as any).metadata?.id;
        if (recordId && idSet.has(recordId)) {
          indexedResults.push(m as unknown as Record<string, unknown>);
        }
      }

      // If we found results via index, cache and return
      if (indexedResults.length > 0) {
        const t = Date.now();
        this._searchCache.set(cacheKey, { results: indexedResults, ts: t, lastAccess: t });
        return indexedResults.slice(0, limit);
      }
    }

    // Cache eviction (lazy cleanup)
    if (this._searchCache.size >= this._cacheMaxSize) {
      const now = Date.now();
      let oldestKey: string | null = null;
      let oldestAccess = Infinity;
      for (const [k, v] of this._searchCache) {
        if (now - v.ts >= this._cacheTTL) {
          this._searchCache.delete(k);
        } else if (v.lastAccess < oldestAccess) {
          oldestAccess = v.lastAccess;
          oldestKey = k;
        }
      }
      if (this._searchCache.size >= this._cacheMaxSize && oldestKey) {
        this._searchCache.delete(oldestKey);
      }
    }

    // Fallback: Full scan (only when index not available or returned empty)
    const all: Array<Record<string, unknown>> = [];
    // v6.36.0: Limit scan to prevent memory pressure
    const scanLimit = 500;
    if (!memoryType || memoryType === "episodic") {
      all.push(...this._episodic.getRecent(scanLimit) as unknown as Array<Record<string, unknown>>);
    }
    if (!memoryType || memoryType === "semantic") {
      all.push(...this._semantic.getAll() as unknown as Array<Record<string, unknown>>);
    }
    if (!memoryType || memoryType === "procedural") {
      all.push(...this._procedural.getAll() as unknown as Array<Record<string, unknown>>);
    }

    // Substring match fallback
    const q = query.toLowerCase();
    const result = all
      .filter((m) => {
        const c = String(m.content ?? "").toLowerCase();
        return c.includes(q);
      })
      .slice(0, limit);
    const now = Date.now();
    this._searchCache.set(cacheKey, { results: result, ts: now, lastAccess: now });
    return result;
  }

  // ── session snapshot ─────────────────────────────────────────────

  snapshotSession(snapshot: SessionSnapshot): import("./session/snapshot-types.js").SnapshotStoreResult {
    const { SnapshotStore } = require("./session/snapshot-store.js");
    return new SnapshotStore(this, {}).store(snapshot);
  }

  // v6.27.0: Session snapshot API for CheckpointManager integration
  sessionSnapshot(params: { snapshot: SessionSnapshot }): { stored: boolean; id: string } {
    const result = this.snapshotSession(params.snapshot);
    return result;
  }

  sessionGetLatest(params?: { sessionId?: string }): SessionSnapshot | null {
    const { SnapshotStore } = require("./session/snapshot-store.js");
    const store = new SnapshotStore(this, {});
    return store.getLatest(params?.sessionId);
  }

  sessionClose(params: { sessionId: string }): { closed: boolean } {
    const { SnapshotStore } = require("./session/snapshot-store.js");
    const store = new SnapshotStore(this, {});
    return store.close(params.sessionId);
  }

  sessionGetUnclosed(params?: Record<string, never>): { sessions: SessionSnapshot[] } {
    const { SnapshotStore } = require("./session/snapshot-store.js");
    const store = new SnapshotStore(this, {});
    return { sessions: store.getUnclosed() };
  }

  getStats(): Record<string, unknown> {
    const memMb = Math.round(process.memoryUsage().heapUsed / 1024 / 1024 * 100) / 100;
    return {
      workspace: this.workspace,
      sessionId: this.sessionId,
      workingMemoryCount: this._working.length,
      indexBuilt: this._index.built,
      bm25Ready: this._bm25Ready,
      episodicCount: this._episodic.count(),
      semanticCount: this._semantic.count(),
      proceduralCount: this._procedural.count(),
      searches: this._searchCount,
      stores: this._storeCount,
      cacheHits: this._cacheHits,
      cacheSize: this._searchCache.size,
      memoryMb: memMb,
      tokenUsage: { total: this._tokenCount },
      bm25DocCount: this._index.built ? this._index.bm25.doc_count : 0,
      indexDir: path.join(os.homedir(), ".claw-mem", "index"),
    };
  }

  /** v6.9.0: Enhanced health check with score and detailed metrics. */
  health(): Record<string, unknown> {
    const rawStats = this.getStats();
    const stats = { searches: rawStats.searches as number ?? 0, stores: rawStats.stores as number ?? 0, memoryMb: rawStats.memoryMb as number ?? 0, cacheHits: rawStats.cacheHits as number ?? 0 };
    const issues: string[] = [];
    const checks: Record<string, boolean> = {};
    let score = 1.0;

    // Storage integrity
    try {
      const epCount = this._episodic.count();
      const semCount = this._semantic.count();
      const procCount = this._procedural.count();
      checks.episodicStorage = true;
      checks.semanticStorage = true;
      checks.proceduralStorage = true;
      checks.storageAccessible = epCount >= 0 && semCount >= 0 && procCount >= 0;
    } catch {
      checks.storageAccessible = false;
      issues.push("storage inaccessible");
      score -= 0.3;
    }

    // Index health
    checks.indexBuilt = this._index.built;
    if (!this._index.built) {
      issues.push("index not built");
      score -= 0.15;
    }
    checks.bm25Ready = this._bm25Ready;
    if (!this._bm25Ready) {
      issues.push("bm25 warmup pending");
      score -= 0.1;
    }

    // Performance metrics
    if ((stats.searches as number) > 100) {
      issues.push("high search count without index rebuild");
      score -= 0.05;
    }

    // Memory usage
    const memMb = process.memoryUsage().heapUsed / (1024 * 1024);
    checks.memoryOk = memMb < 500;
    if (memMb >= 500) {
      issues.push(`high memory usage: ${memMb.toFixed(0)}MB`);
      score -= 0.1;
    }

    const overallScore = Math.max(0, score);
    const status = overallScore >= 0.8 ? "healthy" : overallScore >= 0.5 ? "degraded" : "unhealthy";

    return {
      status,
      score: overallScore,
      issues,
      checks,
      storage: {
        episodic: this._episodic.count(),
        semantic: this._semantic.count(),
        procedural: this._procedural.count(),
      },
      index: { built: this._index.built, bm25Ready: this._bm25Ready },
      performance: {
        searches: stats.searches,
        stores: stats.stores,
        memoryMb: Math.round(memMb * 100) / 100,
        cacheHits: stats.cacheHits,
      },
    };
  }

  // ── build index ─────────────────────────────────────────────────

  buildIndex(): void {
    // Force rebuild: reset index state before building
    this._index.built = false;

    const entries: MemoryEntry[] = [];
    for (const m of this._episodic.getRecent(500)) {
      entries.push({ id: (m as any).id || (m as any).metadata?.id || m.timestamp || "0", content: m.content });
    }
    for (const m of this._semantic.getAll()) {
      entries.push({ id: (m as { id?: string }).id || m.timestamp || "0", content: m.content });
    }
    this._index.loadOrBuild(entries);
  }

  // ── factory ─────────────────────────────────────────────────────

  get factory(): ComponentFactory { return this._factory; }

  // ── transcript API (v6.28.0) ─────────────────────────────────────

  /** Get transcript storage instance */
  get transcript(): TranscriptStorage | null { return this._transcript; }

  /** Get transcript content by sessionId */
  getTranscript(sessionId: string): string | null {
    return this._transcript?.getTranscript(sessionId) ?? null;
  }

  /** Get transcript file path */
  getTranscriptPath(sessionId: string, date?: string): string | null {
    return this._transcript?.getTranscriptPath(sessionId, date) ?? null;
  }

  /** Search transcripts by keyword */
  searchTranscripts(query: string, options?: { limit?: number }): TranscriptMatch[] {
    return this._transcript?.searchTranscripts(query, options) ?? [];
  }

  /** Append message to current transcript session */
  appendTranscriptMessage(entry: TranscriptEntry): void {
    this._transcript?.appendMessage(entry);
  }

  /** Start a new transcript session */
  startTranscriptSession(sessionId: string, channel?: string): void {
    this._transcript?.startSession(sessionId, channel);
  }

  /** End current transcript session */
  endTranscriptSession(): void {
    this._transcript?.endSession();
  }

  // ── hybrid search API (v6.29.0) ─────────────────────────────────────

  /** Get hybrid retriever instance (lazy initialization) */
  get hybridRetriever(): HybridRetriever | null {
    if (!this._hybridRetriever) {
      this._hybridRetriever = new HybridRetriever({
        semanticSearchFn: (query: string, limit: number) => {
          // Use existing search as semantic search
          return this.search(query, undefined, limit).map((m: any) => ({
            id: m.id ?? m.timestamp ?? String(Date.now()),
            text: m.content ?? "",
            score: m.score ?? 0.5,
            metadata: m.metadata ?? {},
            source: "semantic",
            memory_type: m.type,
            tags: m.tags,
            timestamp: m.timestamp,
          }));
        },
      });
      // Index existing memories (lazy)
      this._indexHybridRetriever();
    }
    return this._hybridRetriever;
  }

  /**
   * Hybrid search: semantic + keyword + filter + fusion rerank.
   * Returns results with completeness score.
   */
  hybridSearch(query: string, options?: HybridSearchOptions): HybridSearchResult {
    if (!this._hybridRetriever) {
      // Fallback to regular search
      const results = this.search(query, undefined, options?.topK ?? 10);
      return {
        results: results.map((m: any) => ({
          id: m.id ?? m.timestamp ?? String(Date.now()),
          text: m.content ?? "",
          score: m.score ?? 0.5,
          metadata: m.metadata ?? {},
          source: "semantic",
          memory_type: m.type,
          tags: m.tags,
          timestamp: m.timestamp,
        })),
        completenessScore: undefined,
        metadata: { semanticCount: results.length, keywordCount: 0, afterFilterCount: results.length, latencyMs: 0 },
      };
    }
    return this._hybridRetriever.search(query, options);
  }

  /** Rebuild hybrid retriever index */
  rebuildHybridIndex(): void {
    this._indexHybridRetriever();
  }

  /** Index existing memories for hybrid retrieval */
  private _indexHybridRetriever(): void {
    if (!this._hybridRetriever) return;

    const documents: Array<{ id: string; text: string; metadata?: Record<string, unknown> }> = [];

    // Index episodic memories
    for (const m of this._episodic.getRecent(10000)) {
      documents.push({
        id: (m as any).id ?? m.timestamp ?? String(Date.now()),
        text: m.content ?? "",
        metadata: { type: "episodic", tags: m.tags, timestamp: m.timestamp, session_id: m.session_id },
      });
    }

    // Index semantic memories
    for (const m of this._semantic.getAll()) {
      documents.push({
        id: (m as any).id ?? m.timestamp ?? String(Date.now()),
        text: m.content ?? "",
        metadata: { type: "semantic", tags: m.tags, timestamp: m.timestamp },
      });
    }

    // Index procedural memories
    for (const m of this._procedural.getAll()) {
      documents.push({
        id: (m as any).id ?? m.timestamp ?? String(Date.now()),
        text: m.content ?? "",
        metadata: { type: "procedural", tags: m.tags, timestamp: m.timestamp },
      });
    }

    this._hybridRetriever.index(documents);
  }

  // ── strategy registry (6.33.0) ─────────────────────────────────────

  private _registerStrategies(): void {
    if (!this._strategyRegistry) return;
    this._strategyRegistry.register(new SessionSnapshotStrategy());
    this._strategyRegistry.register(new FactStrategy());
    this._strategyRegistry.register(new PreferenceStrategy());
    this._strategyRegistry.register(new SemanticStrategy());
    this._strategyRegistry.register(new ProceduralStrategy());
  }

  private _buildStrategyContext(): import("./storage/strategy-registry.js").StrategyContext {
    return {
      episodic: this._episodic,
      semantic: this._semantic,
      procedural: this._procedural,
      entityIndex: this._entityIndex,
      versionChain: this._versionChain!,
      workspace: this.workspace,
    };
  }

  // ── entity API (v6.30.0) ─────────────────────────────────────

  /** Get entity index instance */
  get entityIndex(): EntityIndex | null { return this._entityIndex; }

  /**
   * Search memories by entity name.
   * @param name - Entity name to search
   * @returns Entity search result with related entities
   */
  entitySearch(name: string): EntitySearchResult | null {
    return this._entityIndex?.search(name) ?? null;
  }

  /**
   * Resolve entity name to canonical form.
   * @param name - Entity name to resolve
   * @returns Resolution result with canonical name and alternatives
   */
  entityResolve(name: string): ResolutionResult | null {
    if (!this._entityIndex) return null;
    return this._entityIndex.resolve(name);
  }

  /**
   * List all entities in the index.
   * @param limit - Maximum number of entities to return (default: 100)
   * @param offset - Number of entities to skip (default: 0)
   * @returns Array of entity records
   */
  listEntities(limit: number = 100, offset: number = 0): EntityRecord[] {
    const all = this._entityIndex?.listAll() ?? [];
    return all.slice(offset, offset + limit);
  }

  /**
   * Get total entity count.
   * @returns Total number of entities
   */
  getEntityCount(): number {
    return this._entityIndex?.listAll().length ?? 0;
  }

  /**
   * Get entity index statistics.
   * @returns Entity stats or empty stats if disabled
   */
  getEntityStats(): Record<string, unknown> {
    return this._entityIndex?.getStats() ?? { entityCount: 0, coocCount: 0, totalMemoryLinks: 0, avgCoocPerEntity: 0 };
  }

  // ── strategy API (6.33.0) ─────────────────────────────────────

  /** List all registered strategies */
  listStrategies(): Array<{ name: string; memoryTypes: string[] }> {
    return this._strategyRegistry?.list() ?? [];
  }

  /** Get store strategy name for a memory type */
  getStoreStrategy(memoryType: string): string {
    return this._strategyRegistry?.resolve(memoryType)?.name ?? "episodic";
  }

  /** Get preference history */
  getPreferenceHistory(prefKey: string): VersionEntry[] {
    return this._versionChain?.getHistory(prefKey) ?? [];
  }

  /** Get current preference value by pref_key */
  getPreference(prefKey: string): { content: string; metadata?: Record<string, unknown> } | null {
    const results = this._semantic.searchByTag(`pref:${prefKey}`);
    if (results.length === 0) return null;
    const r = results[0];
    return { content: r.content, metadata: r.metadata };
  }

  /** Rollback preference to a previous version */
  rollbackPreference(prefKey: string, version: number): VersionEntry | null {
    if (!this._versionChain) return null;
    try {
      return this._versionChain.rollback(prefKey, version, { semantic: this._semantic });
    } catch {
      return null;
    }
  }

  // ── private ─────────────────────────────────────────────────────

  private _detectWorkspace(): string {
    const candidates = [
      path.join(os.homedir(), ".openclaw", "workspace"),
      path.join(os.homedir(), "workspace"),
      process.cwd(),
    ];
    for (const c of candidates) {
      try {
        const p = path.join(c, "MEMORY.md");
        if (fs.existsSync(p)) return c;
      } catch { continue; }
    }
    return candidates[0];
  }
}

// Singleton
interface MMOpts {
  workspace?: string; config?: MemoryConfig; autoDetect?: boolean;
  enableGating?: boolean; enableDecay?: boolean; enableGraph?: boolean;
  enableCompression?: boolean; factory?: ComponentFactory;
}
let _mm: MemoryManager | null = null;
export function getMemoryManager(opts?: MMOpts): MemoryManager {
  if (!_mm || opts) _mm = new MemoryManager(opts);
  return _mm;
}
export function resetMemoryManager(): void { _mm = null; }
