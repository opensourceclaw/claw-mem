// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — MemoryManager (TypeScript)
 *
 * Core orchestrator: storage, retrieval, gating, decay, graph, compression.
 * Lazy-loads subsystems on first access to keep startup fast.
 */

import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { EpisodicStorage } from "./storage/episodic";
import { SemanticStorage } from "./storage/semantic";
import { ProceduralStorage } from "./storage/procedural";
import { GroundTruthStore } from "./storage/ground_truth";
import { InMemoryIndex } from "./storage/index";
// MemoryEntry type for indexing
interface MemoryEntry { id: string; content: string; }
import { MemoryConfig } from "./config";
import { ComponentFactory, getDefaultFactory } from "./factories";
import { ConstitutionStore } from "./constitution";
// Import types only to avoid circular deps
import type { WriteTimeGating } from "./gating/write_time_gating";
import type { ThreeTierRetriever } from "./retrieval/three_tier";
import type { HybridRouter } from "./retrieval/hybrid_router";
import type { TieredDecayEngine } from "./decay/tiered_decay";
import type { ConceptMediatedGraph } from "./graph/concept_graph";
import type { MemoryCompressorV2 } from "./compression/memory_compression_v2";
import type { CompressionSpectrum } from "./compression/spectrum";

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
    this._index = new InMemoryIndex(3, path.join(os.homedir(), ".claw-mem", "index"), true);

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

    log(`claw-mem TS v6.6.0 initialized, workspace: ${this.workspace}`);
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

  private _startAsyncBuild(): void {
    // Defer index build to next tick so constructor returns fast
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
      const { TieredDecayEngine } = require("./decay/tiered_decay");
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

    const record = {
      content, tags, metadata,
      id: `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      timestamp: new Date().toISOString(),
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
      this._storeCount++;

      // Incremental index update
      try {
        if (this._index.built) {
          this._index.addMemory(content, record.id, true);
        }
      } catch { /* index update is best-effort */ }

      return true;
    } catch {
      return false;
    }
  }

  search(query: string, memoryType?: string, limit = 10): Array<Record<string, unknown>> {
    if (!query?.trim()) return [];
    this._searchCount++;

    // Gather all memories
    const all: Array<Record<string, unknown>> = [];
    if (!memoryType || memoryType === "episodic") {
      all.push(...this._episodic.getRecent(limit * 3) as unknown as Array<Record<string, unknown>>);
    }
    if (!memoryType || memoryType === "semantic") {
      all.push(...this._semantic.getAll() as unknown as Array<Record<string, unknown>>);
    }
    if (!memoryType || memoryType === "procedural") {
      all.push(...this._procedural.getAll() as unknown as Array<Record<string, unknown>>);
    }

    // Simple keyword matching (delegates to index when available)
    if (this._index.built) {
      const ids = this._index.search(query, limit);
      const idSet = new Set(ids);
      const matched = all.filter((m) => idSet.has(m.id as string));
      if (matched.length > 0) return matched.slice(0, limit);
    }

    // Fallback: substring match
    const q = query.toLowerCase();
    return all
      .filter((m) => {
        const c = String(m.content ?? "").toLowerCase();
        return c.includes(q);
      })
      .slice(0, limit);
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
      memoryMb: memMb,
      bm25DocCount: this._index.built ? this._index.bm25.doc_count : 0,
      indexDir: path.join(os.homedir(), ".claw-mem", "index"),
    };
  }

  /** Health check: storage integrity, index state, memory usage. */
  health(): Record<string, unknown> {
    const stats = this.getStats();
    const issues: string[] = [];
    if (!this._index.built) issues.push("index not built");
    if (!this._bm25Ready) issues.push("bm25 warmup pending");
    const epCount = this._episodic.count();
    const semCount = this._semantic.count();
    return {
      status: issues.length === 0 ? "healthy" : "degraded",
      issues,
      storage: { episodic: epCount, semantic: semCount, procedural: this._procedural.count() },
      index: { built: this._index.built, bm25Ready: this._bm25Ready },
      performance: { searches: stats.searches, stores: stats.stores, memoryMb: stats.memoryMb },
    };
  }

  // ── build index ─────────────────────────────────────────────────

  buildIndex(): void {
    const entries: MemoryEntry[] = [];
    for (const m of this._episodic.getRecent(500)) {
      entries.push({ id: m.timestamp || "0", content: m.content });
    }
    for (const m of this._semantic.getAll()) {
      entries.push({ id: (m as { id?: string }).id || m.timestamp || "0", content: m.content });
    }
    this._index.loadOrBuild(entries);
  }

  // ── factory ─────────────────────────────────────────────────────

  get factory(): ComponentFactory { return this._factory; }

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
