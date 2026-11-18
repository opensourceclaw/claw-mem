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
import { createHash } from "crypto";
import { VERSION } from "./version.js";
import { EpisodicStorage } from "./storage/episodic.js";
import { SemanticStorage } from "./storage/semantic.js";
import { ProceduralStorage } from "./storage/procedural.js";
import { GroundTruthStore } from "./storage/ground_truth.js";
import { InMemoryIndex } from "./storage/index.js";
// MemoryEntry type for indexing
interface MemoryEntry { id: string; content: string; }
import { MemoryConfig } from "./config.js";
import { RetentionScoreEngine, type RetentionState } from "./retention/retention-engine.js";

/** v6.36.0: Maximum working memory size to prevent unbounded growth */
const WORKING_MAX_SIZE = 500;

// ── v7.10.0 (ADR-007): evidence pointers + event time ────────────────────
// Evidence is persisted inside the existing metadata comment so no storage
// format change is needed. The JSON is base64-encoded because the metadata
// comment parser splits on ";" and evidence spans may contain any character.
const EVIDENCE_META_KEY = "_clawmem_evidence";
const EVENT_TIME_META_KEY = "_clawmem_event_time";
const EVENT_TIME_RE = /^\d{4}(?:-\d{2}(?:-\d{2}(?:T[\d:.+-]+)?)?)?$/;

// ADR-008 hard caps: bounded read-only navigation.
const SOURCE_MAX_REFS = 10;
const SOURCE_MAX_CHARS = 2048;

/** Optional write extras for evidence pointers / event time (ADR-007). */
export interface MemoryStoreExtras {
  evidence?: import("./types.js").MemoryEvidence[];
  eventTime?: string;
}

/** Optional time semantics for retrieval (ADR-007 §3). */
export interface MemorySearchOptions {
  /** Inclusive lower bound on `eventTime ?? created_at`. */
  since?: string;
  /** Inclusive upper bound on `eventTime ?? created_at`. */
  until?: string;
  /** `relevance` (default) keeps score order; `time` sorts newest effective time first. */
  orderBy?: "relevance" | "time";
}

// ── v7.10.0 (ADR-008): read-only navigation surface ─────────────────────

/** Metadata-only list row (never carries full text). */
export interface MemoryListItem {
  id: string;
  title: string;
  time?: string;
  tags: string[];
  layer: "episodic" | "semantic" | "procedural" | "preference";
}

/** Single-record read result; `lines` is a 1-based inclusive range. */
export interface MemoryGetResult {
  id: string;
  title: string;
  text: string;
  memory_type: string;
  created_at?: string;
  time?: string;
  tags: string[];
  evidence?: MemoryEvidence[];
  eventTime?: string;
  lineRange?: [number, number];
  totalLines: number;
}

export interface MemoryLinkOut {
  ref: string;
  type: "transcript" | "path" | "unknown";
}

export interface MemoryBacklink {
  id: string;
  title: string;
  time?: string;
}

export interface MemoryLinksResult {
  id: string;
  direction: "out" | "in" | "both";
  out: MemoryLinkOut[];
  in: MemoryBacklink[];
}

export interface MemorySource {
  ref: string;
  type: "transcript" | "path" | "unknown";
  found: boolean;
  text?: string;
  truncated?: boolean;
  sessionId?: string;
  date?: string;
}

export interface MemorySourcesResult {
  sources: MemorySource[];
  requested: number;
  returned: number;
  maxRefsPerCall: number;
  maxCharsPerItem: number;
}

interface MemoryRecordView {
  id: string;
  title: string;
  text: string;
  layer: "episodic" | "semantic" | "procedural";
  created_at?: string;
  tags: string[];
  metadata?: Record<string, unknown>;
}

function encodeEvidenceMetadata(evidence: MemoryEvidence[]): string {
  return Buffer.from(JSON.stringify(evidence), "utf-8").toString("base64");
}

function decodeEvidenceMetadata(raw: unknown): MemoryEvidence[] | undefined {
  if (typeof raw !== "string" || raw === "") return undefined;
  try {
    const parsed = JSON.parse(Buffer.from(raw, "base64").toString("utf-8"));
    return Array.isArray(parsed) ? (parsed as MemoryEvidence[]) : undefined;
  } catch {
    return undefined; // corrupt/legacy payload → behave as no evidence
  }
}
import { ComponentFactory, getDefaultFactory } from "./factories.js";
import { ConstitutionStore } from "./constitution.js";
import { TranscriptStorage, type TranscriptEntry, type TranscriptMatch, type TranscriptConfig } from "./transcript/index.js";
import { HybridRetriever, type HybridSearchOptions, type HybridSearchResult } from "./retrieval/hybrid-retriever.js";
import { SynonymExpander } from "./retrieval/synonym.js";
import { EntityIndex } from "./entity/entity-index.js";
import { EntityExtractor } from "./entity/entity-extractor.js";
import { EntityResolver } from "./entity/entity-resolver.js";
import type { EntityRecord, EntitySearchResult, ResolutionResult, EntityConfig, DEFAULT_ENTITY_CONFIG, MemoryEvidence } from "./types.js";
import { isRootCauseCategory, DEFAULT_CARD_EFFECTIVENESS } from "./types.js";
import { StrategyRegistry } from "./storage/strategy-registry.js";
import { VersionChain } from "./storage/version-chain.js";
import type { VersionEntry } from "./storage/version-chain.js";
import { EpisodicStrategy, SessionSnapshotStrategy, FactStrategy, PreferenceStrategy, SemanticStrategy, ProceduralStrategy, ErrorPatternCardStrategy } from "./storage/strategies/index.js";
import { decodeErrorPatternCard, ERROR_PATTERN_TAG, encodeCardMetadata } from "./storage/strategies/error-pattern-card.js";
import { GRACE_PERIOD_DAYS, HIT_WINDOW, RESOLUTION_MIN_CHARS, SIMILARITY_THRESHOLD } from "./storage/error-pattern-card/constants.js";
import { triggerSimilarity } from "./storage/error-pattern-card/similarity.js";
import { MemoryGovernance } from "./memory/governance.js";
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
  private _synonymExpander = new SynonymExpander();
  private _entityIndex: EntityIndex | null = null;
  private _strategyRegistry: StrategyRegistry | null = null;
  private _versionChain: VersionChain | null = null;
  // v7.6.0 (ADR-003): per-domain version chain for error pattern cards
  private _errorPatternChain: VersionChain | null = null;
  // v7.5.0 (ADR-002): Usage-based retention scoring
  private _retention: RetentionScoreEngine | null = null;
  // v7.5.0: suppress search() events while running the hybrid semantic leg
  // (partial candidates there are not final selections; hybrid reports once)
  private _retentionSuppressSearch = false;
  // v6.40.0: MemoryGovernance for self-organizing memory
  private _governance: MemoryGovernance | null = null;
  // v6.40.0: Progressive loading state
  private _progressiveLoadState: {
    episodic: boolean;
    semantic: boolean;
    procedural: boolean;
    index: boolean;
  } = { episodic: false, semantic: false, procedural: false, index: false };
  private _backgroundLoadPromise: Promise<void> | null = null;
  // Future: private _injector: ContextInjector | null = null;
  // Future: private _confidenceGate: ConfidenceGate | null = null;

  constructor(opts?: Partial<{
    workspace?: string; storagePath?: string; config?: MemoryConfig; autoDetect?: boolean;
    enableGating?: boolean; enableDecay?: boolean; enableGraph?: boolean;
    enableCompression?: boolean; factory?: ComponentFactory;
    enableProgressiveLoading?: boolean;  // v6.40.0: Progressive loading option
  }>) {
    this._factory = opts?.factory ?? getDefaultFactory();
    this.config = opts?.config ?? new MemoryConfig(opts);
    // storagePath is the pre-existing README alias for workspace
    const requestedWorkspace = this.config.workspace || opts?.storagePath;

    if (this.config.autoDetect) {
      this.workspace = requestedWorkspace || this._detectWorkspace();
    } else {
      this.workspace = requestedWorkspace || path.join(os.homedir(), ".openclaw", "workspace");
    }
    // Ensure workspace exists
    fs.mkdirSync(this.workspace, { recursive: true });

    // v6.40.0: Support progressive loading for memory optimization
    const useProgressiveLoading = opts?.enableProgressiveLoading ?? false;

    if (useProgressiveLoading) {
      // Defer storage initialization to background
      this._episodic = null as any;
      this._semantic = null as any;
      this._procedural = null as any;
      this._index = null as any;
      this._startBackgroundPrefetch();
    } else {
      // Legacy eager-init (backward compatible)
      this._episodic = new EpisodicStorage(this.workspace);
      this._semantic = new SemanticStorage(this.workspace);
      this._procedural = new ProceduralStorage(this.workspace);
      this._index = new InMemoryIndex(this.workspace);
      this._progressiveLoadState = { episodic: true, semantic: true, procedural: true, index: false };
    }

    // Stats tracking
    this._searchCount = 0;
    this._storeCount = 0;
    this._cacheHits = 0;

    // Async BM25 warmup (non-blocking)
    this._bm25Ready = false;
    if (!useProgressiveLoading) {
      this._startAsyncBuild();
    }

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
        log(`Archived ${deleted} expired transcript directories to _archive/`);
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
      // v6.39.0: Entity index is now lazy-loaded on first access
    }

    // 6.33.0: Version Chain for preferences
    this._versionChain = new VersionChain(this.workspace);

    // v7.6.0 (ADR-003): independent version chain for error pattern cards
    this._errorPatternChain = new VersionChain(this.workspace, "error-pattern-cards");

    // 6.33.0: Strategy Registry
    this._strategyRegistry = new StrategyRegistry(new EpisodicStrategy());
    this._registerStrategies();

    // v7.5.0 (ADR-002): Retention score engine (params from config)
    this._retention = new RetentionScoreEngine({
      rho: this.config.retentionRho,
      maxStreak: this.config.retentionMaxStreak,
      selectedBoost: this.config.retentionSelectedBoost,
      successScore: this.config.retentionSuccessScore,
      failureScore: this.config.retentionFailureScore,
    });

    log(`claw-mem TS ${VERSION} initialized, workspace: ${this.workspace}`);
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

  // ── retention helpers (v7.5.0, ADR-002) ──────────────────────

  private _retentionEnabled(): boolean {
    return this.config.retentionEnabled === true && this._retention !== null;
  }

  /** Read persisted retention state from record metadata (JSON string or object). */
  private _readRetention(meta: Record<string, unknown> | undefined): RetentionState | null {
    if (!meta) return null;
    let raw: unknown = meta.retention;
    if (typeof raw === "string") {
      try { raw = JSON.parse(raw); } catch { return null; }
    }
    if (!raw || typeof raw !== "object") return null;
    const s = raw as Partial<RetentionState>;
    if (typeof s.score !== "number" || typeof s.missedStreak !== "number") return null;
    return {
      score: s.score,
      missedStreak: s.missedStreak,
      lastSelected: typeof s.lastSelected === "string" ? s.lastSelected : "",
      initializedAt: typeof s.initializedAt === "string" ? s.initializedAt : new Date().toISOString(),
    };
  }

  /**
   * Apply a selection/miss event to a record: lazy-hydrate from persisted
   * metadata, update the engine, write back (JSON string for storage compat).
   */
  private _retentionEvent(
    record: { id?: string; metadata?: Record<string, unknown> } | null | undefined,
    event: "selected" | "missed",
  ): void {
    if (!this._retentionEnabled()) return;
    const id = record?.id;
    if (!id) return;
    if (this._retention!.getState(id) === null) {
      const persisted = this._readRetention(record?.metadata);
      if (persisted) this._retention!.setState(id, persisted);
    }
    const state = event === "selected"
      ? this._retention!.onSelected(id)
      : this._retention!.onCandidateMissed(id);
    if (record?.metadata) record.metadata.retention = JSON.stringify(state);
  }

  private _estimateTokens(text: string): number {
    const cjkChars = (text.match(/[\u4e00-\u9fff\u3400-\u4dbf]/g) || []).length;
    const latinChars = text.length - cjkChars;
    return Math.ceil(cjkChars / 1.5 + latinChars / 4);
  }

  private _startAsyncBuild(): void {
    // Defer index build to next tick so constructor returns fast
    // Fallback substring search works before index is built
    //
    // CI flake fix (2026-11-10, run 42831455554): the deferred build used to
    // log via console.warn when the workspace had already been removed by a
    // finished test, and that log raced worker teardown → EnvironmentTeardownError
    // ("Closing rpc while \"onUserConsoleLog\" was pending"). A workspace that no
    // longer exists is not an error worth reporting: skip silently. The timer is
    // also unref'd so it never keeps the process alive.
    const timer = setTimeout(() => {
      try {
        if (!fs.existsSync(this.workspace)) return; // torn-down test workspace
        this.buildIndex();
        this._bm25Ready = true;
        this._progressiveLoadState.index = true;
      } catch (err) {
        if (!fs.existsSync(this.workspace)) return; // raced with teardown
        console.warn("[claw-mem] async index build failed:", err);
      }
    }, 10);
    if (typeof timer.unref === "function") timer.unref();
  }

  // v6.40.0: Background prefetch for progressive loading
  private _startBackgroundPrefetch(): void {
    this._backgroundLoadPromise = (async () => {
      try {
        // Phase 1: Load episodic (most used)
        if (!this._progressiveLoadState.episodic) {
          this._episodic = new EpisodicStorage(this.workspace);
          this._progressiveLoadState.episodic = true;
        }

        // Phase 2: Initialize index and build
        await new Promise(resolve => setTimeout(resolve, 50));
        this._index = new InMemoryIndex(this.workspace);

        // Build index (requires episodic and semantic)
        if (this._episodic) {
          this.buildIndex();
          this._bm25Ready = true;
        }

        // Phase 3: Semantic/procedural stay lazy (on demand via getters)
      } catch (err) {
        // Same CI-teardown guard as _startAsyncBuild: a removed workspace is not
        // an error, and logging after teardown races worker RPC shutdown.
        if (fs.existsSync(this.workspace)) {
          console.error("[claw-mem] Background prefetch failed:", err);
        }
      }
    })();
  }

  /**
   * v6.40.0: Wait for background loading to complete.
   * Use this to ensure critical subsystems are ready before operations.
   */
  async waitForReady(): Promise<void> {
    if (this._backgroundLoadPromise) {
      await this._backgroundLoadPromise;
    }
  }

  /**
   * v6.40.0: Check if critical subsystems are ready.
   */
  isReady(): boolean {
    // Ready if episodic storage is loaded and index exists
    const episodicReady = this._episodic != null || this._progressiveLoadState.episodic;
    const indexReady = this._index != null;
    return episodicReady && indexReady;
  }

  /**
   * v6.40.0: Get progressive loading state.
   */
  getLoadState(): { episodic: boolean; semantic: boolean; procedural: boolean; index: boolean } {
    return { ...this._progressiveLoadState };
  }

  // ── storage accessors ──────────────────────────────────────────

  get episodic(): EpisodicStorage {
    if (!this._progressiveLoadState.episodic) {
      this._episodic = new EpisodicStorage(this.workspace);
      this._progressiveLoadState.episodic = true;
    }
    return this._episodic;
  }

  get semantic(): SemanticStorage {
    if (!this._progressiveLoadState.semantic) {
      this._semantic = new SemanticStorage(this.workspace);
      this._progressiveLoadState.semantic = true;
    }
    return this._semantic;
  }

  get procedural(): ProceduralStorage {
    if (!this._progressiveLoadState.procedural) {
      this._procedural = new ProceduralStorage(this.workspace);
      this._progressiveLoadState.procedural = true;
    }
    return this._procedural;
  }

  get groundTruth(): GroundTruthStore {
    if (!this._gt) this._gt = new GroundTruthStore();
    return this._gt;
  }

  get index(): InMemoryIndex {
    // In legacy mode, _index is already initialized in constructor
    // Just return it if already set
    if (this._index) {
      return this._index;
    }
    // In progressive mode, initialize on first access
    if (!this._progressiveLoadState.index) {
      this._index = new InMemoryIndex(this.workspace);
      this._progressiveLoadState.index = true;
    }
    return this._index;
  }

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

  // v6.40.0: MemoryGovernance getter
  get governance(): MemoryGovernance {
    if (!this._governance) {
      this._governance = new MemoryGovernance();
    }
    return this._governance;
  }

  // ── core operations ─────────────────────────────────────────────

  /**
   * v6.40.0: Store with governance check.
   * @param content - Memory content
   * @param importance - Intrinsic importance (0-1)
   * @param relevance - Relevance to context (0-1)
   * @returns true if stored, false if rejected by governance
   */
  storeWithGovernance(
    content: string,
    importance: number,
    relevance: number,
    memoryType: string = "episodic",
    tags: string[] = [],
    metadata: Record<string, unknown> = {}
  ): boolean {
    if (!this.governance.select(importance, relevance)) {
      return false;
    }
    return this.store(content, memoryType, tags, metadata);
  }

  store(content: string, memoryType: string = "episodic",
        tags: string[] = [], metadata: Record<string, unknown> = {},
        extras: MemoryStoreExtras = {}): boolean {
    if (!content?.trim()) return false;

    // v7.10.0 (ADR-007): V-ref write gate. Evidence is optional; when present,
    // every sourceRef must resolve and every span must be a substring of the
    // record text. Rejections are traced (append-only) before returning false.
    const gate = this._validateEvidence(content, extras, metadata);
    if (!gate.ok) {
      const rawEvidence = extras.evidence ?? metadata.evidence;
      const rawEventTime = extras.eventTime ?? metadata.eventTime;
      this._traceEvidenceGate({
        action: "reject",
        ruleId: gate.ruleId,
        reason: gate.reason,
        input: {
          contentPreview: content.slice(0, 120),
          evidenceCount: Array.isArray(rawEvidence) ? rawEvidence.length : undefined,
          eventTime: typeof rawEventTime === "string" ? rawEventTime : undefined,
        },
        caller: "store",
      });
      return false;
    }

    // Persist evidence/time in reserved metadata keys; strip the convenience
    // top-level metadata keys so they never reach storage in raw form.
    const cleanMetadata: Record<string, unknown> = { ...metadata };
    delete cleanMetadata.evidence;
    delete cleanMetadata.eventTime;
    if (gate.evidence) cleanMetadata[EVIDENCE_META_KEY] = encodeEvidenceMetadata(gate.evidence);
    if (gate.eventTime) cleanMetadata[EVENT_TIME_META_KEY] = gate.eventTime;
    metadata = cleanMetadata;

    const id = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    const timestamp = new Date().toISOString();

    // 6.33.0: Strategy-based dispatch
    if (this._strategyRegistry) {
      // v7.6.0 (ADR-003/006): cards are strongly schema'd — route through the
      // dedicated storeErrorPatternCard entry; refuse here before registry
      // resolution so the default fallback never silently swallows a card.
      // (Rejection tracing: full jsonl log lands with the ADR-006 gate.)
      if (memoryType === "error_pattern_card") {
        console.warn("[claw-mem] error_pattern_card must be stored via storeErrorPatternCard; generic store refused");
        this._traceCardGate({
          action: "reject",
          ruleId: "generic-store-refusal",
          reason: "error_pattern_card must be stored via storeErrorPatternCard",
          input: { contentPreview: content.slice(0, 120), tags },
          caller: "unknown",
        });
        return false;
      }
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

        // v7.5.0 (ADR-002): initialize retention from write-time outcome
        // (success 0.75 / failure 0.30 / absent 0.5); persisted via the
        // same record object the strategy just stored (metadata reference)
        if (this._retentionEnabled()) {
          const outcome = metadata.outcome === "success" || metadata.outcome === "failure"
            ? (metadata.outcome as "success" | "failure")
            : undefined;
          const state = this._retention!.initialize(result.id, outcome);
          if (record.metadata) record.metadata.retention = JSON.stringify(state);
        }

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
        // A cached miss must not survive a successful write (F-1).
        this._searchCache.clear();

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
      // v7.5.0 (ADR-002): legacy fallback path — same retention init
      if (this._retentionEnabled()) {
        const outcome = metadata.outcome === "success" || metadata.outcome === "failure"
          ? (metadata.outcome as "success" | "failure")
          : undefined;
        const state = this._retention!.initialize(id, outcome);
        if (record.metadata) record.metadata.retention = JSON.stringify(state);
      }
      this._working.push(record);
      // v6.36.0: LRU eviction for working memory
      if (this._working.length > WORKING_MAX_SIZE) {
        this._working = this._working.slice(-WORKING_MAX_SIZE);
      }
      this._storeCount++;
      this._tokenCount += this._estimateTokens(content);
      // A cached miss must not survive a successful write (F-1).
      this._searchCache.clear();

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

  // ── error pattern cards (v7.6.0, ADR-003) ──────────────────────────

  /**
   * Store (create or edit) an error pattern card. Same cardId = edit —
   * archived and re-stored through the card version chain
   * (`memory/error-pattern-cards/{cardId}.json`). effectiveness/createdAt are
   * server-side only (V2). ADR-006 validation gate runs before the commit:
   * V1 completeness / V3c enum / V3b resolution floor reject + trace; V3a
   * trigger-similarity warns (suggestUpdate) on create against active cards —
   * never rejects. All reject/warn events land in
   * `memory/error-pattern-card-rejections/` (append-only jsonl).
   */
  storeErrorPatternCard(
    input: import("./types.js").ErrorPatternCardInput,
  ):
    | {
        ok: true; cardId: string; version: number; edited: boolean;
        warning?: { ruleId: string; similarCardId: string; similarity: number };
      }
    | { ok: false; reason: string; ruleId?: string } {
    const sig = input?.errorSignature;
    if (
      !sig ||
      typeof sig.trigger !== "string" || !sig.trigger.trim() ||
      typeof sig.symptom !== "string" || !sig.symptom.trim()
    ) {
      return this._rejectCardGate("V1", "errorSignature.trigger and errorSignature.symptom must be non-empty strings", input);
    }
    if (!isRootCauseCategory(input.rootCauseCategory)) {
      return this._rejectCardGate("V3c", `invalid rootCauseCategory: ${String(input.rootCauseCategory)}`, input);
    }
    if (typeof input.resolution !== "string" || !input.resolution.trim()) {
      return this._rejectCardGate("V1", "resolution must be a non-empty string", input);
    }
    if (input.resolution.trim().length < RESOLUTION_MIN_CHARS) {
      return this._rejectCardGate("V3b", `resolution must be at least ${RESOLUTION_MIN_CHARS} characters`, input);
    }
    if (!input.provenance || typeof input.provenance.source !== "string" || !input.provenance.source.trim()) {
      return this._rejectCardGate("V2", "provenance.source is required", input);
    }
    // V1' (v7.8.0 additive): dual-state guard — success-strategy requires a
    // well-formed payload; error-pattern (the absent default) must NOT carry one.
    if (input.cardType !== undefined && input.cardType !== "error-pattern" && input.cardType !== "success-strategy") {
      return this._rejectCardGate("V1'", `invalid cardType: ${String(input.cardType)}`, input);
    }
    if (input.cardType === "success-strategy") {
      const ss = input.successStrategy;
      if (!ss || typeof ss !== "object") {
        return this._rejectCardGate("V1'", 'cardType "success-strategy" requires a successStrategy payload', input);
      }
      if (ss.subtype !== "procedural" && ss.subtype !== "strategic" && ss.subtype !== "tool-usage") {
        return this._rejectCardGate("V1'", `invalid successStrategy.subtype: ${String(ss.subtype)}`, input);
      }
      if (typeof ss.applicableWhen !== "string" || !ss.applicableWhen.trim()) {
        return this._rejectCardGate("V1'", "successStrategy.applicableWhen must be a non-empty string", input);
      }
      if (!Array.isArray(ss.steps) || ss.steps.length < 1 ||
          !ss.steps.every((s) => typeof s === "string" && s.trim())) {
        return this._rejectCardGate("V1'", "successStrategy.steps must be a non-empty array of non-empty strings", input);
      }
    } else if (input.successStrategy) {
      return this._rejectCardGate("V1'", 'successStrategy is only valid with cardType "success-strategy" (dual-state guard)', input);
    }
    const effIn = (input as unknown as Record<string, unknown>).effectiveness as
      { hitCount?: number; avoidedCount?: number; attempts?: unknown } | undefined;
    // v7.11 (SIM): attempts are host-written only — reject caller-supplied
    // attempt ledgers (forgery guard, acceptance-discipline §5 mirror).
    if (effIn && typeof effIn === "object" && "attempts" in effIn) {
      return this._rejectCardGate(
        "V1",
        "effectiveness.attempts is host-written only (recordCardAttempt/backfillCardAttempt); caller cannot set it",
        input,
      );
    }
    if (effIn && typeof effIn === "object" &&
      ((typeof effIn.hitCount === "number" && effIn.hitCount < 0) ||
       (typeof effIn.avoidedCount === "number" && effIn.avoidedCount < 0))) {
      return this._rejectCardGate("V1", "effectiveness counts must be >= 0 (server-owned field)", input);
    }

    const cardId =
      input.cardId && input.cardId.trim()
        ? input.cardId.trim()
        : `epc:${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
    const card: import("./types.js").ErrorPatternCard = {
      cardId,
      errorSignature: { trigger: sig.trigger.trim(), symptom: sig.symptom.trim() },
      rootCauseCategory: input.rootCauseCategory,
      resolution: input.resolution.trim(),
      verification: input.verification?.trim() || undefined,
      effectiveness: { ...DEFAULT_CARD_EFFECTIVENESS },
      provenance: input.provenance,
      createdAt: new Date().toISOString(),
    };
    // v7.8.0: normalise cardType — absent/`"error-pattern"` stays absent (v7.6/v7.7
    // metadata byte-identical); success cards carry the discriminated payload.
    if (input.cardType === "success-strategy") {
      const ss = input.successStrategy!;
      card.cardType = "success-strategy";
      card.successStrategy = {
        subtype: ss.subtype,
        applicableWhen: ss.applicableWhen.trim(),
        steps: ss.steps.map((s) => s.trim()),
      };
    }

    // V3a: on create, a trigger ~duplicate of an active card means the author
    // should edit the existing card instead — advisory only, never reject.
    const isNew = !this._semantic.searchByTag(`card:${cardId}`)[0];
    let warning: { ruleId: string; similarCardId: string; similarity: number } | undefined;
    if (isNew) {
      let best: { similarCardId: string; similarity: number } | undefined;
      for (const e of this._semantic.getAll()) {
        if (!e.tags?.includes(ERROR_PATTERN_TAG)) continue;
        const existing = decodeErrorPatternCard(e);
        if (!existing || existing.cardId === cardId || existing.effectiveness.inactive) continue;
        const sim = triggerSimilarity(card.errorSignature.trigger, existing.errorSignature.trigger);
        if (!best || sim > best.similarity) best = { similarCardId: existing.cardId, similarity: sim };
      }
      if (best && best.similarity >= SIMILARITY_THRESHOLD) {
        warning = { ruleId: "V3a-trigger-similarity", similarCardId: best.similarCardId, similarity: best.similarity };
        this._traceCardGate({
          action: "warn",
          ruleId: "V3a-trigger-similarity",
          reason: `trigger ~duplicates active card ${best.similarCardId} (similarity ${best.similarity.toFixed(3)}) — prefer editing that cardId`,
          input: { cardId, trigger: card.errorSignature.trigger, symptom: card.errorSignature.symptom },
          caller: card.provenance.source,
        });
      }
    }

    const committed = this._commitCard(card);
    if (!committed.ok) {
      return { ok: false, reason: committed.reason, ruleId: "V1" };
    }
    return { ok: true, cardId, version: committed.version, edited: committed.edited, ...(warning ? { warning } : {}) };
  }

  /**
   * ADR-006 reject: trace the gate event, return the failure. Every reject is
   * persisted (never silent) before the caller sees it.
   */
  private _rejectCardGate(
    ruleId: string,
    reason: string,
    input: import("./types.js").ErrorPatternCardInput,
  ): { ok: false; reason: string; ruleId: string } {
    const sig = input?.errorSignature as { trigger?: string; symptom?: string } | undefined;
    this._traceCardGate({
      action: "reject",
      ruleId,
      reason,
      input: {
        cardId: typeof input?.cardId === "string" ? input.cardId : undefined,
        trigger: sig?.trigger,
        symptom: sig?.symptom,
        rootCauseCategory: input?.rootCauseCategory,
        resolutionLen: typeof input?.resolution === "string" ? input.resolution.length : undefined,
        provenanceSource: input?.provenance?.source,
        cardType: input?.cardType,
      },
      caller: input?.provenance?.source?.trim() || "unknown",
    });
    return { ok: false, reason, ruleId };
  }

  /**
   * Query the ADR-006 gate trail: `memory/error-pattern-card-rejections/*.jsonl`
   * (append-only, one event per file). Newest first; since (ISO, inclusive) and
   * action filters; default limit 50.
   */
  listErrorPatternRejections(
    filter: { since?: string; action?: "reject" | "warn"; limit?: number } = {},
  ): Array<{
    ts: string; action: "reject" | "warn"; ruleId: string; reason: string;
    input: Record<string, unknown>; caller: string;
  }> {
    const dir = this._cardGateDir();
    let events: Array<{ ts: string; action: "reject" | "warn"; ruleId: string; reason: string; input: Record<string, unknown>; caller: string }> = [];
    if (fs.existsSync(dir)) {
      for (const file of fs.readdirSync(dir)) {
        if (!file.endsWith(".jsonl")) continue;
        let text = "";
        try {
          text = fs.readFileSync(path.join(dir, file), "utf-8");
        } catch {
          continue;
        }
        for (const line of text.split("\n")) {
          if (!line.trim()) continue;
          try {
            events.push(JSON.parse(line));
          } catch {
            // skip corrupt lines — the trail must never break reads
          }
        }
      }
    }
    events = events.filter((e) => {
      if (filter.action && e.action !== filter.action) return false;
      if (filter.since && e.ts < filter.since) return false;
      return true;
    });
    events.sort((a, b) => b.ts.localeCompare(a.ts));
    return events.slice(0, filter.limit ?? 50);
  }

  private _cardGateDir(): string {
    return path.join(this.workspace, "memory", "error-pattern-card-rejections");
  }

  /** Append-only gate event: one jsonl file per event, never rewritten. */
  private _traceCardGate(entry: {
    action: "reject" | "warn"; ruleId: string; reason: string;
    input: Record<string, unknown>; caller: string;
  }): void {
    try {
      const dir = this._cardGateDir();
      fs.mkdirSync(dir, { recursive: true });
      const ts = new Date().toISOString();
      const file = path.join(dir, `${ts.replace(/[:.]/g, "-")}-${Math.random().toString(36).slice(2, 6)}.jsonl`);
      fs.appendFileSync(file, JSON.stringify({ ts, ...entry }) + "\n", "utf-8");
    } catch (err) {
      console.warn(`[claw-mem] card gate trace failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  // ── v7.10.0 (ADR-007): V-ref evidence gate + event time ──────────────

  /** Validate optional evidence against the record text and resolvable refs. */
  private _validateEvidence(
    content: string,
    extras: MemoryStoreExtras,
    metadata: Record<string, unknown>,
  ):
    | { ok: true; evidence?: MemoryEvidence[]; eventTime?: string }
    | { ok: false; ruleId: string; reason: string } {
    const rawEvidence = extras.evidence ?? metadata.evidence;
    const rawEventTime = extras.eventTime ?? metadata.eventTime;

    let eventTime: string | undefined;
    if (rawEventTime !== undefined) {
      if (typeof rawEventTime !== "string" || !EVENT_TIME_RE.test(rawEventTime)) {
        return {
          ok: false,
          ruleId: "event-time-format",
          reason: `eventTime must be ISO-8601 (YYYY / YYYY-MM / YYYY-MM-DD): ${JSON.stringify(rawEventTime)}`,
        };
      }
      eventTime = rawEventTime;
    }

    if (rawEvidence === undefined) return { ok: true, ...(eventTime ? { eventTime } : {}) };
    if (!Array.isArray(rawEvidence)) {
      return { ok: false, ruleId: "v-ref-malformed", reason: "evidence must be an array" };
    }

    const evidence: MemoryEvidence[] = [];
    for (let i = 0; i < rawEvidence.length; i++) {
      const entry = rawEvidence[i] as Partial<MemoryEvidence> | null | undefined;
      if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
        return { ok: false, ruleId: "v-ref-malformed", reason: `evidence[${i}] must be an object` };
      }
      const span = typeof entry.span === "string" ? entry.span : "";
      if (!span.trim()) {
        return { ok: false, ruleId: "v-ref-span-missing", reason: `evidence[${i}].span must be a non-empty string` };
      }
      if (!content.includes(span)) {
        return {
          ok: false,
          ruleId: "v-ref-span-not-substring",
          reason: `evidence[${i}].span is not a substring of the record text`,
        };
      }
      if (!Array.isArray(entry.sourceRefs) || entry.sourceRefs.some((ref) => typeof ref !== "string")) {
        return {
          ok: false,
          ruleId: "v-ref-refs-missing",
          reason: `evidence[${i}].sourceRefs must be a string array`,
        };
      }
      if (
        entry.offset !== undefined &&
        (typeof entry.offset !== "number" || !Number.isInteger(entry.offset) || entry.offset < 0)
      ) {
        return {
          ok: false,
          ruleId: "v-ref-offset-invalid",
          reason: `evidence[${i}].offset must be a non-negative integer`,
        };
      }
      if (entry.eventTime !== undefined && (typeof entry.eventTime !== "string" || !EVENT_TIME_RE.test(entry.eventTime))) {
        return {
          ok: false,
          ruleId: "event-time-format",
          reason: `evidence[${i}].eventTime must be ISO-8601 (YYYY / YYYY-MM / YYYY-MM-DD)`,
        };
      }
      // ADR-007: refs are checked only when non-empty; an empty array is legal.
      for (const rawRef of entry.sourceRefs) {
        const ref = rawRef.trim();
        if (!ref || !this._isResolvableSourceRef(ref)) {
          return {
            ok: false,
            ruleId: "v-ref-unresolvable",
            reason: `evidence[${i}].sourceRefs cannot resolve ${JSON.stringify(ref)}`,
          };
        }
      }
      evidence.push({
        span,
        ...(entry.offset !== undefined ? { offset: entry.offset } : {}),
        ...(entry.eventTime !== undefined ? { eventTime: entry.eventTime } : {}),
        sourceRefs: [...entry.sourceRefs],
      });
    }

    return { ok: true, evidence, ...(eventTime ? { eventTime } : {}) };
  }

  /**
   * A ref is a transcript id unless it looks like a path. Paths must stay
   * inside the workspace (or resolve to a soft-deleted daily note); transcript
   * ids resolve through TranscriptStorage (including `_archive/`).
   */
  private _isResolvableSourceRef(ref: string): boolean {
    const cleaned = ref.replace(/^`+|`+$/g, "");
    const looksLikePath = /[\\/]/.test(cleaned) || /\.md$/i.test(cleaned);
    if (!looksLikePath) {
      return (this._transcript?.getTranscriptByIds([cleaned]).length ?? 0) > 0;
    }
    const root = path.resolve(this.workspace);
    const abs = path.isAbsolute(cleaned) ? path.resolve(cleaned) : path.resolve(root, cleaned);
    if (abs !== root && !abs.startsWith(root + path.sep)) return false;
    if (fs.existsSync(abs)) return true;
    // Daily notes soft-delete into memory/_archive/<file>.
    return fs.existsSync(path.join(root, "memory", "_archive", path.basename(cleaned)));
  }

  /** Read the reserved evidence/time keys back out of record metadata. */
  private _decodeEvidenceFields(metadata: unknown): { evidence?: MemoryEvidence[]; eventTime?: string } {
    if (!metadata || typeof metadata !== "object") return {};
    const meta = metadata as Record<string, unknown>;
    const evidence = decodeEvidenceMetadata(meta[EVIDENCE_META_KEY]);
    const eventTime = typeof meta[EVENT_TIME_META_KEY] === "string" && meta[EVENT_TIME_META_KEY]
      ? meta[EVENT_TIME_META_KEY]
      : undefined;
    return {
      ...(evidence ? { evidence } : {}),
      ...(eventTime ? { eventTime } : {}),
    };
  }

  /** ADR-007 §3: the time axis is eventTime when present, else created_at. */
  private _effectiveTimeOf(record: {
    eventTime?: unknown;
    timestamp?: unknown;
    created_at?: unknown;
    metadata?: unknown;
  }): string | undefined {
    const decoded = this._decodeEvidenceFields(record.metadata);
    const candidates = [record.eventTime, decoded.eventTime, record.created_at, record.timestamp];
    for (const c of candidates) {
      if (typeof c === "string" && c.trim()) return c;
    }
    return undefined;
  }

  /** ADR-007 §4: evidence/eventTime coverage over the current record sample. */
  private _evidenceCoverageStats(): {
    sampleSize: number; withEvidence: number; withEventTime: number; coverage: number;
  } {
    const sample = [
      ...this._episodic.getRecent(1000),
      ...this._semantic.getAll().slice(0, 1000),
      ...this._procedural.getAll().slice(0, 1000),
    ] as Array<{ metadata?: unknown }>;
    let withEvidence = 0;
    let withEventTime = 0;
    for (const record of sample) {
      const decoded = this._decodeEvidenceFields(record.metadata);
      if (decoded.evidence?.length) withEvidence++;
      if (decoded.eventTime) withEventTime++;
    }
    return {
      sampleSize: sample.length,
      withEvidence,
      withEventTime,
      coverage: sample.length > 0 ? withEvidence / sample.length : 0,
    };
  }

  /**
   * Decorate results with evidence/eventTime and apply ADR-007 time semantics.
   * Decoration is additive (keys appear only when the record carries them);
   * filtering/sorting use `eventTime ?? created_at`.
   */
  private _applyTimeOptions<T extends Record<string, unknown>>(
    results: T[],
    options?: MemorySearchOptions,
  ): T[] {
    const wantsRange = Boolean(options?.since || options?.until);
    const wantsSort = options?.orderBy === "time";
    const decorated = results.map((record) => {
      const decoded = this._decodeEvidenceFields(record.metadata);
      const out: Record<string, unknown> = { ...record };
      if (decoded.evidence) out.evidence = decoded.evidence;
      if (decoded.eventTime) out.eventTime = decoded.eventTime;
      return { record: out as T, effectiveTime: this._effectiveTimeOf(record) };
    });

    if (!wantsRange && !wantsSort) return decorated.map((d) => d.record);

    let selected = decorated;
    if (wantsRange) {
      const since = options?.since ? Date.parse(options.since) : NaN;
      const until = options?.until ? Date.parse(options.until) : NaN;
      selected = selected.filter(({ effectiveTime }) => {
        const t = effectiveTime ? Date.parse(effectiveTime) : NaN;
        if (Number.isNaN(t)) return false; // no usable time → cannot prove it is in range
        if (!Number.isNaN(since) && t < since) return false;
        if (!Number.isNaN(until) && t > until) return false;
        return true;
      });
    }
    if (wantsSort) {
      selected = [...selected].sort((a, b) => {
        const at = a.effectiveTime ? Date.parse(a.effectiveTime) : NaN;
        const bt = b.effectiveTime ? Date.parse(b.effectiveTime) : NaN;
        return (Number.isNaN(bt) ? 0 : bt) - (Number.isNaN(at) ? 0 : at);
      });
    }
    return selected.map((d) => d.record);
  }

  /**
   * Query the ADR-007 evidence-gate trail:
   * `memory/evidence-rejections/*.jsonl` (append-only, one event per file).
   */
  listEvidenceRejections(
    filter: { since?: string; ruleId?: string; limit?: number } = {},
  ): Array<{
    ts: string; action: "reject"; ruleId: string; reason: string;
    input: Record<string, unknown>; caller: string;
  }> {
    const dir = this._evidenceGateDir();
    let events: Array<{ ts: string; action: "reject"; ruleId: string; reason: string; input: Record<string, unknown>; caller: string }> = [];
    if (fs.existsSync(dir)) {
      for (const file of fs.readdirSync(dir)) {
        if (!file.endsWith(".jsonl")) continue;
        let text = "";
        try {
          text = fs.readFileSync(path.join(dir, file), "utf-8");
        } catch {
          continue;
        }
        for (const line of text.split("\n")) {
          if (!line.trim()) continue;
          try {
            events.push(JSON.parse(line));
          } catch {
            // skip corrupt lines — the trail must never break reads
          }
        }
      }
    }
    events = events.filter((e) => {
      if (filter.ruleId && e.ruleId !== filter.ruleId) return false;
      if (filter.since && e.ts < filter.since) return false;
      return true;
    });
    events.sort((a, b) => b.ts.localeCompare(a.ts));
    return events.slice(0, filter.limit ?? 50);
  }

  private _evidenceGateDir(): string {
    return path.join(this.workspace, "memory", "evidence-rejections");
  }

  /** Append-only gate event: one jsonl file per event, never rewritten. */
  private _traceEvidenceGate(entry: {
    action: "reject"; ruleId: string; reason: string;
    input: Record<string, unknown>; caller: string;
  }): void {
    try {
      const dir = this._evidenceGateDir();
      fs.mkdirSync(dir, { recursive: true });
      const ts = new Date().toISOString();
      const file = path.join(dir, `${ts.replace(/[:.]/g, "-")}-${Math.random().toString(36).slice(2, 6)}.jsonl`);
      fs.appendFileSync(file, JSON.stringify({ ts, ...entry }) + "\n", "utf-8");
    } catch (err) {
      console.warn(`[claw-mem] evidence gate trace failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  /**
   * Record an error pattern card hit (ADR-005). The update goes through the
   * same archive->store version-chain path as an edit — every hit appends a
   * chain version carrying the updated effectiveness, so the last
   * HIT_WINDOW consecutive hits are auditable from the chain tail.
   * avoided=true revives an inactive card; a run of HIT_WINDOW non-avoided
   * hits demotes the card (inactive — never deleted).
   */
  recordErrorPatternHit(
    cardId: string,
    opts: {
      avoided: boolean;
      at?: string;
      /** v7.8.0: host-supplied lifecycle stats (contract §6.3) — merged only when present; absent keys are never fabricated. */
      lifecycle?: { stableRuns?: number; backwardRetention?: number; pathAttribution?: string };
    } = { avoided: false },
  ):
    | { ok: true; cardId: string; hitCount: number; avoidedCount: number; inactive: boolean; version: number }
    | { ok: false; reason: string } {
    if (!cardId) return { ok: false, reason: "cardId required" };
    const entry = this._semantic.searchByTag(`card:${cardId}`)[0];
    const card = entry ? decodeErrorPatternCard(entry) : null;
    if (!card) return { ok: false, reason: "not-found" };

    const now = opts.at ?? new Date().toISOString();
    const prevEff = card.effectiveness;
    const eff = { ...prevEff, hitCount: prevEff.hitCount + 1, lastHitAt: now };
    if (opts.lifecycle) eff.lifecycle = { ...prevEff.lifecycle, ...opts.lifecycle };

    if (opts.avoided) {
      eff.avoidedCount += 1;
      if (prevEff.inactive) {
        // auto-revive on the first avoided hit after demotion
        eff.inactive = false;
        eff.inactivatedAt = undefined;
      }
    } else if (!prevEff.inactive) {
      // Non-avoided run = archived hit versions on the chain (commit of the
      // previous hit not yet archived lives in the entry state) + this hit.
      const run = this._effectiveNonAvoidedRun(cardId, prevEff) + 1;
      if (run >= HIT_WINDOW) {
        eff.inactive = true;
        eff.inactivatedAt = now;
      }
    }

    const updated: import("./types.js").ErrorPatternCard = { ...card, effectiveness: eff, updatedAt: now };
    const committed = this._commitCard(updated);
    if (!committed.ok) return { ok: false, reason: committed.reason };
    return {
      ok: true,
      cardId,
      hitCount: eff.hitCount,
      avoidedCount: eff.avoidedCount,
      inactive: eff.inactive,
      version: committed.version,
    };
  }

  // ── v7.11 (SIM, arXiv 2611.18856): predicted → fixed/missed attempts ─────

  /**
   * Register a prediction BEFORE adopting/using a card. Host write-back only.
   * The attempt starts unbackfilled and is excluded from effectiveness stats
   * until backfillCardAttempt() completes it.
   */
  recordCardAttempt(
    cardId: string,
    opts: { runId: string; predictedIssueIds: string[]; at?: string },
  ):
    | { ok: true; cardId: string; runId: string; attempts: number; version: number }
    | { ok: false; reason: string } {
    if (!cardId) return { ok: false, reason: "cardId required" };
    if (!opts || typeof opts.runId !== "string" || opts.runId.trim() === "") {
      return { ok: false, reason: "runId required" };
    }
    const predicted = this._normalizeIssueIds(opts.predictedIssueIds, false);
    if (!predicted.ok) return { ok: false, reason: predicted.reason };

    const entry = this._semantic.searchByTag(`card:${cardId}`)[0];
    const card = entry ? decodeErrorPatternCard(entry) : null;
    if (!card) return { ok: false, reason: "not-found" };

    const attempts = [...(card.effectiveness.attempts ?? [])];
    const runId = opts.runId.trim();
    if (attempts.some((attempt) => attempt.runId === runId)) {
      return { ok: false, reason: `attempt already exists for runId ${runId}` };
    }

    const now = opts.at ?? new Date().toISOString();
    attempts.push({
      runId,
      predictedIssueIds: predicted.ids,
      fixedIds: [],
      missedIds: [],
      backfilled: false,
      observedAt: now,
    });
    const updated: import("./types.js").ErrorPatternCard = {
      ...card,
      effectiveness: { ...card.effectiveness, attempts },
      updatedAt: now,
    };
    const committed = this._commitCard(updated);
    if (!committed.ok) return { ok: false, reason: committed.reason };
    return { ok: true, cardId, runId, attempts: attempts.length, version: committed.version };
  }

  /**
   * Backfill fixed/missed for a registered attempt. The partition must exactly
   * cover predictedIssueIds: fixed ∪ missed = predicted, and fixed ∩ missed = ∅.
   * A completed attempt is immutable — a second backfill is rejected.
   */
  backfillCardAttempt(
    cardId: string,
    runId: string,
    opts: { fixedIds: string[]; missedIds: string[]; at?: string },
  ):
    | { ok: true; cardId: string; runId: string; fixed: number; missed: number; version: number }
    | { ok: false; reason: string } {
    if (!cardId) return { ok: false, reason: "cardId required" };
    if (!runId || !runId.trim()) return { ok: false, reason: "runId required" };
    const entry = this._semantic.searchByTag(`card:${cardId}`)[0];
    const card = entry ? decodeErrorPatternCard(entry) : null;
    if (!card) return { ok: false, reason: "not-found" };

    const attempts = [...(card.effectiveness.attempts ?? [])];
    const index = attempts.findIndex((attempt) => attempt.runId === runId.trim());
    if (index < 0) return { ok: false, reason: `attempt not found for runId ${runId.trim()}` };
    const attempt = attempts[index];
    if (attempt.backfilled) {
      return { ok: false, reason: `attempt ${runId.trim()} is already backfilled` };
    }

    const fixed = this._normalizeIssueIds(opts?.fixedIds, true);
    if (!fixed.ok) return { ok: false, reason: fixed.reason };
    const missed = this._normalizeIssueIds(opts?.missedIds, true);
    if (!missed.ok) return { ok: false, reason: missed.reason };

    const predictedSet = new Set(attempt.predictedIssueIds);
    const fixedSet = new Set(fixed.ids);
    const missedSet = new Set(missed.ids);
    for (const id of fixedSet) {
      if (!predictedSet.has(id)) return { ok: false, reason: `fixedId ${id} is not in predictedIssueIds` };
    }
    for (const id of missedSet) {
      if (!predictedSet.has(id)) return { ok: false, reason: `missedId ${id} is not in predictedIssueIds` };
    }
    for (const id of fixedSet) {
      if (missedSet.has(id)) return { ok: false, reason: `issue ${id} cannot be both fixed and missed` };
    }
    const union = new Set([...fixedSet, ...missedSet]);
    if (union.size !== predictedSet.size) {
      const missing = [...predictedSet].filter((id) => !union.has(id));
      return {
        ok: false,
        reason: `backfill incomplete — unclassified predicted ids: ${missing.join(", ")}`,
      };
    }

    const now = opts?.at ?? new Date().toISOString();
    attempts[index] = { ...attempt, fixedIds: fixed.ids, missedIds: missed.ids, backfilled: true };
    const updated: import("./types.js").ErrorPatternCard = {
      ...card,
      effectiveness: { ...card.effectiveness, attempts },
      updatedAt: now,
    };
    const committed = this._commitCard(updated);
    if (!committed.ok) return { ok: false, reason: committed.reason };
    return {
      ok: true,
      cardId,
      runId: attempt.runId,
      fixed: fixed.ids.length,
      missed: missed.ids.length,
      version: committed.version,
    };
  }

  /**
   * Effectiveness stats over BACKFILLED attempts only. Non-backfilled attempts
   * are excluded (honest-backfill rule); zero denominator ⇒ null, never 0.
   */
  getCardAttemptStats(cardId: string):
    | {
        ok: true;
        attempts: number;
        backfilled: number;
        predicted: number;
        fixed: number;
        missed: number;
        fixedRate: number | null;
      }
    | { ok: false; reason: string } {
    if (!cardId) return { ok: false, reason: "cardId required" };
    const entry = this._semantic.searchByTag(`card:${cardId}`)[0];
    const card = entry ? decodeErrorPatternCard(entry) : null;
    if (!card) return { ok: false, reason: "not-found" };

    const all = card.effectiveness.attempts ?? [];
    const completed = all.filter((attempt) => attempt.backfilled === true);
    let predicted = 0;
    let fixed = 0;
    let missed = 0;
    for (const attempt of completed) {
      predicted += attempt.predictedIssueIds.length;
      fixed += attempt.fixedIds.length;
      missed += attempt.missedIds.length;
    }
    return {
      ok: true,
      attempts: all.length,
      backfilled: completed.length,
      predicted,
      fixed,
      missed,
      fixedRate: predicted > 0 ? fixed / predicted : null,
    };
  }

  /** Normalize an id list: array of non-empty strings, de-duplicated, order kept. */
  private _normalizeIssueIds(
    value: unknown,
    allowEmpty: boolean,
  ): { ok: true; ids: string[] } | { ok: false; reason: string } {
    if (!Array.isArray(value)) return { ok: false, reason: "issue ids must be an array" };
    const ids: string[] = [];
    for (const entry of value) {
      if (typeof entry !== "string" || entry.trim() === "") {
        return { ok: false, reason: "issue ids must be non-empty strings" };
      }
      const id = entry.trim();
      if (!ids.includes(id)) ids.push(id);
    }
    if (!allowEmpty && ids.length === 0) {
      return { ok: false, reason: "predictedIssueIds must be non-empty" };
    }
    return { ok: true, ids };
  }

  /** Structured card query — category filter, active-only by default. */
  queryErrorPatternCards(
    filter: {
      category?: string;
      includeInactive?: boolean;
      limit?: number;
      /** v7.8.0 additive; absent = both types (audit-face semantics). */
      cardType?: import("./types.js").CardType;
    } = {},
  ): Array<import("./types.js").ErrorPatternCard> {
    const limit = filter.limit ?? 20;
    let cards = this._semantic.getAll()
      .filter((e) => e.tags?.includes(ERROR_PATTERN_TAG))
      .map((e) => decodeErrorPatternCard(e))
      .filter((c): c is import("./types.js").ErrorPatternCard => c !== null)
      .map((c) => this._demoteIfIdle(c)); // lazy never-hit demotion on read
    if (filter.category) cards = cards.filter((c) => c.rootCauseCategory === filter.category);
    if (filter.cardType) {
      cards = cards.filter((c) => (c.cardType ?? "error-pattern") === filter.cardType);
    }
    if (!filter.includeInactive) cards = cards.filter((c) => !c.effectiveness.inactive);
    cards.sort((a, b) => {
      const at = a.effectiveness.lastHitAt ?? "";
      const bt = b.effectiveness.lastHitAt ?? "";
      return bt.localeCompare(at); // most recent hit first, never-hit last
    });
    return cards.slice(0, limit);
  }

  /** Signature matching — symptom/trigger substring hits first, text fallback; inactive downranked. */
  matchErrorPattern(symptomQuery: string, topK = 5): Array<import("./types.js").ErrorPatternCard> {
    const q = symptomQuery.trim().toLowerCase();
    if (!q) return [];
    const scored: Array<{ card: import("./types.js").ErrorPatternCard; score: number }> = [];
    for (const e of this._semantic.getAll()) {
      if (!e.tags?.includes(ERROR_PATTERN_TAG)) continue;
      const card = decodeErrorPatternCard(e);
      if (!card) continue;
      let score = 0;
      const symptom = card.errorSignature.symptom.toLowerCase();
      const trigger = card.errorSignature.trigger.toLowerCase();
      if (symptom.includes(q)) score += 2;
      else if (trigger.includes(q)) score += 2;
      else if (card.resolution.toLowerCase().includes(q)) score += 1;
      if (score > 0) scored.push({ card, score });
    }
    scored.sort((a, b) => {
      const byScore = b.score - a.score;
      if (byScore !== 0) return byScore;
      // inactive cards rank after active ones at equal score (ADR-005)
      return Number(a.card.effectiveness.inactive) - Number(b.card.effectiveness.inactive);
    });
    return scored.slice(0, topK).map((s) => s.card);
  }

  // ── injection path (v7.7.0, joint design §2 — thin adapter over v7.6.0) ──

  /**
   * Injection-grade card query (v7.7.0, contract §1): trigger similarity
   * against `card.errorSignature.trigger` (same `triggerSimilarity` and, by
   * default, the same SIMILARITY_THRESHOLD as ADR-006 V3a — one definition of
   * "similar" across dedup and recall) ∪ exact category filter. Active cards
   * only — a demoted card never enters the injection face. No triggerQuery →
   * category/recency path (queryErrorPatternCards semantics). No hit → []
   * (honest empty; nothing synthesized).
   */
  findCardsForInjection(
    query: {
      triggerQuery?: string;
      triggerThreshold?: number;
      category?: import("./types.js").RootCauseCategory;
      /** v7.8.0 additive; absent = "error-pattern" (v7.7.0 behaviour byte-identical). */
      cardType?: import("./types.js").CardType;
      /**
       * v7.8.0 T2 placeholder: accepted but NOT weighted yet — the caller passes
       * the ctx `statusSignalKey` product, ranking stays untouched this version
       * (weighting waits for ctx consumption data; plan §3).
       */
      statusKey?: string;
      limit?: number;
    } = {},
  ): Array<import("./types.js").ErrorPatternCard> {
    const threshold = query.triggerThreshold ?? SIMILARITY_THRESHOLD;
    const limit = query.limit ?? 3;
    const wantType = query.cardType ?? "error-pattern";
    let cards = this._semantic.getAll()
      .filter((e) => e.tags?.includes(ERROR_PATTERN_TAG))
      .map((e) => decodeErrorPatternCard(e))
      .filter((c): c is import("./types.js").ErrorPatternCard => c !== null)
      .map((c) => this._demoteIfIdle(c))
      .filter((c) => !c.effectiveness.inactive)
      .filter((c) => (c.cardType ?? "error-pattern") === wantType);
    if (query.category) cards = cards.filter((c) => c.rootCauseCategory === query.category);
    const triggerQuery = query.triggerQuery?.trim();
    if (triggerQuery) {
      const scored = cards
        .map((card) => ({ card, sim: triggerSimilarity(triggerQuery, card.errorSignature.trigger) }))
        .filter((s) => s.sim >= threshold);
      scored.sort((a, b) => {
        const bySim = b.sim - a.sim;
        if (bySim !== 0) return bySim;
        return (b.card.effectiveness.lastHitAt ?? "").localeCompare(a.card.effectiveness.lastHitAt ?? "");
      });
      return scored.slice(0, limit).map((s) => s.card);
    }
    cards.sort((a, b) => (b.effectiveness.lastHitAt ?? "").localeCompare(a.effectiveness.lastHitAt ?? ""));
    return cards.slice(0, limit);
  }

  /**
   * Card list → injection reminder text block (v7.7.0, contract §2 — the ONLY
   * producer of the `[Error Pattern Cards]` format). Pure: fresh string, input
   * untouched. Empty list → "" (honest empty, no bare header). Truncation
   * drops WHOLE cards (a half warning is noise) and appends a
   * `(+N more suppressed)` trailer; without maxChars nothing is truncated.
   */
  formatCardsAsReminder(
    cards: readonly import("./types.js").ErrorPatternCard[],
    opts?: { maxChars?: number },
  ): string {
    if (!cards || cards.length === 0) return "";
    const firstSentence = (s: string): string => {
      const m = s.match(/^[\s\S]*?[.!?。！？](?:\s|$)/);
      return (m ? m[0] : s).trim();
    };
    // v7.8.0 块头双态：纯错误卡输出逐字不变（[Error Pattern Cards]）；含策略卡时
    // 双侧统一头 [Experience Cards]（纯策略卡亦用此头）。
    const hasSuccess = cards.some((c) => c.cardType === "success-strategy");
    const lines: string[] = [hasSuccess ? "[Experience Cards]" : "[Error Pattern Cards]"];
    let suppressed = 0;
    for (const card of cards) {
      const line = card.cardType === "success-strategy"
        ? this._formatSuccessCardLine(card)
        : `- ⚠️ [${card.cardId} | root: ${card.rootCauseCategory} | from: ${card.provenance?.source ?? "unknown"}] ` +
          `${card.errorSignature.trigger} → ${firstSentence(card.resolution)}`;
      if (opts?.maxChars !== undefined && lines.join("\n").length + line.length + 1 > opts.maxChars) {
        suppressed = cards.length - (lines.length - 1);
        break;
      }
      lines.push(line);
    }
    if (suppressed > 0) lines.push(`(+${suppressed} more suppressed)`);
    return lines.join("\n");
  }

  /** v7.8.0 ✅ 行：`- ✅ [cardId | strategy: <subtype> | from: <source>] applicableWhen → steps[0]…` */
  private _formatSuccessCardLine(card: import("./types.js").ErrorPatternCard): string {
    const ss = card.successStrategy;
    const when = ss?.applicableWhen ?? card.errorSignature.trigger;
    const step = ss?.steps?.[0] ?? card.resolution;
    const more = (ss?.steps?.length ?? 0) > 1;
    return `- ✅ [${card.cardId} | strategy: ${ss?.subtype ?? "unknown"} | from: ${card.provenance?.source ?? "unknown"}] ` +
      `${when} → ${step}${more ? "…" : ""}`;
  }

  // ── error pattern card internals (v7.6.0, ADR-003/005) ───────────

  /** Serialize a card into the storage-face MemoryRecord (single source for create/edit/hit/demotion). */
  private _cardToRecord(card: import("./types.js").ErrorPatternCard): import("./types.js").MemoryRecord {
    return {
      id: `card_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      text: card.resolution,
      memory_type: "error_pattern_card",
      created_at: card.createdAt,
      metadata: encodeCardMetadata(card),
      tags: [ERROR_PATTERN_TAG, `category:${card.rootCauseCategory}`, `card:${card.cardId}`],
    };
  }

  /** Commit a card through the strategy (archive old version when editing). */
  private _commitCard(card: import("./types.js").ErrorPatternCard): {
    ok: boolean; reason: string; version: number; edited: boolean;
  } {
    const record = this._cardToRecord(card);
    try {
      const result = this._strategyRegistry!.resolve("error_pattern_card").store(
        record,
        this._buildStrategyContext(),
      );
      if (this._index.built) {
        this._index.addMemory(record.text, result.id, true);
      }
      return {
        ok: true,
        reason: "",
        version: result.version ?? 1,
        edited: Boolean(result.previousId),
      };
    } catch (err) {
      return { ok: false, reason: err instanceof Error ? err.message : String(err), version: 0, edited: false };
    }
  }

  /** Lazy never-hit demotion on read: created > GRACE_PERIOD_DAYS ago with no hits. */
  private _demoteIfIdle(card: import("./types.js").ErrorPatternCard): import("./types.js").ErrorPatternCard {
    const eff = card.effectiveness;
    if (eff.inactive || eff.hitCount > 0) return card;
    const created = Date.parse(card.createdAt);
    if (Number.isNaN(created)) return card;
    if (Date.now() - created <= GRACE_PERIOD_DAYS * 86_400_000) return card;
    const now = new Date().toISOString();
    const demoted: import("./types.js").ErrorPatternCard = {
      ...card,
      effectiveness: { ...eff, inactive: true, inactivatedAt: now },
      updatedAt: now,
    };
    const committed = this._commitCard(demoted);
    if (!committed.ok) {
      console.warn(`[claw-mem] idle card demotion persist failed for ${card.cardId}: ${committed.reason}`);
    }
    return demoted;
  }

  /**
   * Consecutive non-avoided hit run over completed hits (newest first): the
   * entry state — the completion of the most recent hit, archived only by
   * the *next* commit — followed by archived hit completions from the chain
   * tail. A completed hit is non-avoided iff its avoidedCount equals its
   * older neighbor's (creation baseline avoidedCount = 0); an avoided hit
   * terminates the run and is not counted.
   *
   * @param entryState effectiveness BEFORE the hit being judged was applied
   */
  private _effectiveNonAvoidedRun(
    cardId: string,
    entryState: import("./types.js").CardEffectiveness,
  ): number {
    const history = this._errorPatternChain?.getHistory(cardId) ?? [];
    const hits: import("./types.js").CardEffectiveness[] = [];
    if (entryState.hitCount > 0) hits.push(entryState);
    let lastSeenHit = entryState.hitCount;
    for (let i = history.length - 1; i >= 0; i--) {
      const raw = history[i].metadata?.effectiveness;
      if (typeof raw !== "string") continue;
      let eff: import("./types.js").CardEffectiveness;
      try {
        eff = JSON.parse(raw);
      } catch {
        continue;
      }
      if (!Number.isInteger(eff.hitCount) || !Number.isInteger(eff.avoidedCount)) continue;
      if (eff.hitCount <= 0) continue; // creation baselines — compare against, never count
      if (eff.hitCount >= lastSeenHit) continue; // duplicates (edit versions / entry state)
      lastSeenHit = eff.hitCount;
      hits.push(eff);
    }

    let run = 0;
    for (let i = 0; i < hits.length; i++) {
      const olderAvoided = i + 1 < hits.length ? hits[i + 1].avoidedCount : 0;
      if (hits[i].avoidedCount === olderAvoided) run += 1;
      else break; // avoided hit ends the run
    }
    return run;
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

  search(
    query: string,
    memoryType?: string,
    limit = 10,
    options?: MemorySearchOptions,
  ): Array<Record<string, unknown>> {
    if (!query?.trim()) return [];
    this._searchCount++;

    // Check cache with access-time update for LRU tracking
    const cacheKey =
      `${query}::${memoryType || "all"}::${limit}` +
      `::${options?.since ?? ""}::${options?.until ?? ""}::${options?.orderBy ?? ""}`;
    const cached = this._searchCache.get(cacheKey);

    // v7.5.0 (ADR-002): selection events BEFORE the cache check so cache
    // hits still update retention (PRD §6 risk table item 3). Cached results
    // were the selected topK when cached — boost them on every hit.
    if (cached && Date.now() - cached.ts < this._cacheTTL) {
      this._cacheHits++;
      cached.lastAccess = Date.now();
      if (!this._retentionSuppressSearch) {
        for (const m of cached.results) this._retentionEvent(m as Record<string, unknown>, "selected");
      }
      return this._applyTimeOptions(cached.results, options).slice(0, limit);
    }

    // v6.36.0: Index-first strategy - use index when available, avoid full scan
    if (this._index.built) {
      // Synonym expansion feeds the BM25 index only; the substring fallback
      // below stays on the original query to avoid false positives.
      const ids = this._index.search(this._synonymExpander.expand(query), limit * 3);
      const idSet = new Set(ids);

      // Load hits across all requested tiers, then order by index score.
      // Loading episodic only dropped semantic/procedural hits entirely.
      const byId = new Map<string, Record<string, unknown>>();
      const collect = (records: unknown[]) => {
        for (const m of records) {
          const rec = m as Record<string, unknown>;
          const recordId = (rec as any).id || (rec as any).metadata?.id;
          if (recordId && idSet.has(recordId) && !byId.has(recordId)) {
            byId.set(recordId, rec);
          }
        }
      };
      if (!memoryType || memoryType === "episodic") {
        collect(this._episodic.getRecent(500));
      }
      if (!memoryType || memoryType === "semantic") {
        collect(this._semantic.getAll());
      }
      if (!memoryType || memoryType === "procedural") {
        collect(this._procedural.getAll());
      }
      const indexedResults: Array<Record<string, unknown>> = ids
        .map((id) => byId.get(id))
        .filter((m): m is Record<string, unknown> => m !== undefined);

      // If we found results via index, cache and return
      if (indexedResults.length > 0) {
        // v7.5.0 (ADR-002): candidate pool = index hits present in storage;
        // selected = actual topK returned, rest = candidate missed
        if (!this._retentionSuppressSearch) {
          const selected = indexedResults.slice(0, limit);
          for (const m of selected) this._retentionEvent(m as Record<string, unknown>, "selected");
          for (const m of indexedResults.slice(limit)) this._retentionEvent(m as Record<string, unknown>, "missed");
        }
        const t = Date.now();
        this._searchCache.set(cacheKey, { results: indexedResults, ts: t, lastAccess: t });
        return this._applyTimeOptions(indexedResults, options).slice(0, limit);
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
    const matched = all.filter((m) => {
      const c = String(m.content ?? "").toLowerCase();
      return c.includes(q);
    });
    // v7.5.0 (ADR-002): candidate pool = all substring hits; selected = topK
    if (!this._retentionSuppressSearch) {
      const selected = matched.slice(0, limit);
      for (const m of selected) this._retentionEvent(m as Record<string, unknown>, "selected");
      for (const m of matched.slice(limit)) this._retentionEvent(m as Record<string, unknown>, "missed");
    }
    const now = Date.now();
    // Cache the full candidate pool so a later time-ordered query can sort
    // before truncation; the default (relevance) path slices identically.
    this._searchCache.set(cacheKey, { results: matched, ts: now, lastAccess: now });
    return this._applyTimeOptions(matched, options).slice(0, limit);
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
    // v7.5.0 (ADR-002): retention distribution for memory_stats
    const retentionStats = this._retention ? this._retention.getStats() : { count: 0, mean: 0, median: 0, belowThreshold: 0, threshold: 0.3 };
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
      retention: retentionStats,
      // v7.10.0 (ADR-007 §4): optional evidence coverage report.
      evidence: this._evidenceCoverageStats(),
    };
  }

  /** v6.39.0: Memory metrics for monitoring index loading state. */
  getMemoryMetrics(): {
    indexLoaded: boolean;
    entityLoaded: boolean;
    indexMemoryMB: number;
    entityMemoryMB: number;
    totalMemoryMB: number;
  } {
    const memMb = Math.round(process.memoryUsage().heapUsed / 1024 / 1024 * 100) / 100;
    const indexLoaded = this._index.built;
    const entityLoaded = this._entityIndex ? (this._entityIndex as any)._loaded === true : false;
    return {
      indexLoaded,
      entityLoaded,
      indexMemoryMB: indexLoaded ? Math.round(memMb * 0.7 * 100) / 100 : 0,
      entityMemoryMB: entityLoaded ? Math.round(memMb * 0.17 * 100) / 100 : 0,
      totalMemoryMB: memMb,
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

    // Use getters to ensure storage is loaded (progressive loading support)
    if (this._episodic) {
      for (const m of this._episodic.getRecent(500)) {
        entries.push({ id: (m as any).id || (m as any).metadata?.id || m.timestamp || "0", content: m.content });
      }
    }
    if (this._semantic) {
      for (const m of this._semantic.getAll()) {
        entries.push({ id: (m as { id?: string }).id || m.timestamp || "0", content: m.content });
      }
    }
    if (this._procedural) {
      for (const m of this._procedural.getAll()) {
        entries.push({ id: (m as { id?: string }).id || m.timestamp || "0", content: m.content });
      }
    }
    this._index.loadOrBuild(entries);
    this._progressiveLoadState.index = true;
    // A miss cached while the index was still building must not outlive the
    // build (F-1: symptom persisted up to the 5s TTL on the startup path).
    this._searchCache.clear();
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

  // ── v7.10.0 (ADR-008): read-only navigation API ─────────────────────

  /**
   * Enumerate record metadata without returning full text. Layers: episodic,
   * semantic, procedural, preference (version-chain keys). Newest first.
   */
  listMemories(options: { layer?: string; prefix?: string; limit?: number } = {}): MemoryListItem[] {
    const layer = options.layer?.trim();
    const prefix = options.prefix?.trim() ?? "";
    const limit = Math.min(Math.max(Math.floor(options.limit ?? 50), 1), 200);
    const items: MemoryListItem[] = [];

    if (!layer || layer === "all" || layer === "episodic" || layer === "semantic" || layer === "procedural") {
      for (const view of this._recordViews()) {
        if (layer && layer !== "all" && view.layer !== layer) continue;
        if (prefix && !view.id.startsWith(prefix) && !view.title.startsWith(prefix)) continue;
        items.push({
          id: view.id,
          title: view.title,
          time: this._effectiveTimeOf(view),
          tags: view.tags,
          layer: view.layer,
        });
      }
    }

    if (!layer || layer === "all" || layer === "preference") {
      for (const pref of this._preferenceIndex()) {
        const key = pref.id.slice("pref:".length);
        if (prefix && !pref.id.startsWith(prefix) && !key.startsWith(prefix)) continue;
        items.push({ id: pref.id, title: pref.title, time: pref.time, tags: ["preference"], layer: "preference" });
      }
    }

    items.sort((a, b) => (b.time ?? "").localeCompare(a.time ?? ""));
    return items.slice(0, limit);
  }

  /**
   * Fetch one record by id (ADR-008 decision 3). `lines` is a 1-based
   * inclusive range; absent = full text. Preferences are addressable as
   * `pref:<key>`.
   */
  getMemoryById(id: string, lines?: [number, number]): MemoryGetResult | null {
    const wanted = typeof id === "string" ? id.trim() : "";
    if (!wanted) return null;

    const view = this._recordViews().find((v) => v.id === wanted);
    if (view) return this._toGetResult(view, lines);

    if (wanted.startsWith("pref:")) {
      const pref = this.getPreference(wanted.slice("pref:".length));
      if (!pref) return null;
      return this._toGetResult({
        id: wanted,
        title: wanted.slice("pref:".length),
        text: pref.content,
        layer: "semantic",
        tags: ["preference"],
        metadata: pref.metadata,
      }, lines);
    }
    return null;
  }

  /**
   * Derive outgoing/incoming links from evidence source refs at read time
   * (ADR-008 decision 2). Out = refs cited by this record. In = records citing
   * this record's id or sharing at least one source ref. No evidence → out [].
   *
   * Explicit exclusion (R2-T1/F2): synthetic `pref:<key>` ids are outside the
   * link graph — preferences carry no evidence sourceRefs, so
   * `memoryLinks('pref:<key>')` returns null by design (documented semantics,
   * not an implicit empty state).
   */
  memoryLinks(id: string, direction: "out" | "in" | "both" = "both"): MemoryLinksResult | null {
    const wanted = typeof id === "string" ? id.trim() : "";
    if (!wanted) return null;

    const views = this._recordViews();
    const target = views.find((v) => v.id === wanted);
    if (!target) return null;

    const targetRefs = this._evidenceRefs(target.metadata);
    const refSet = new Set(targetRefs);
    const out: MemoryLinkOut[] = direction !== "in"
      ? targetRefs.map((ref) => ({ ref, type: this._refType(ref) }))
      : [];

    const backlinks: MemoryBacklink[] = [];
    if (direction !== "out") {
      for (const other of views) {
        if (other.id === target.id) continue;
        const otherRefs = this._evidenceRefs(other.metadata);
        const citesTarget = otherRefs.includes(target.id);
        const sharesSource = otherRefs.some((ref) => refSet.has(ref));
        if (!citesTarget && !sharesSource) continue;
        const time = this._effectiveTimeOf(other);
        backlinks.push({ id: other.id, title: other.title, ...(time ? { time } : {}) });
      }
    }

    return { id: target.id, direction, out, in: backlinks };
  }

  /**
   * Read original evidence text by transcript id or workspace path.
   * ADR-008 hard caps: ≤10 refs per call, ≤2KB (2048 chars) per item.
   */
  getSources(refs: string[]): MemorySourcesResult {
    const requested = Array.isArray(refs) ? refs.length : 0;
    const selected = Array.isArray(refs) ? refs.slice(0, SOURCE_MAX_REFS) : [];
    const sources = selected.map((ref) => this._resolveSource(ref));
    return {
      sources,
      requested,
      returned: sources.length,
      maxRefsPerCall: SOURCE_MAX_REFS,
      maxCharsPerItem: SOURCE_MAX_CHARS,
    };
  }

  /** All record views across the three opaque storage layers. */
  private _recordViews(): MemoryRecordView[] {
    const views: MemoryRecordView[] = [];
    const push = (
      layer: MemoryRecordView["layer"],
      entries: Array<{
        id?: string;
        content?: string;
        timestamp?: string;
        tags?: string[];
        metadata?: Record<string, unknown>;
      }>,
    ): void => {
      for (const entry of entries) {
        const text = entry.content ?? "";
        const id = entry.id && entry.id.trim()
          ? entry.id
          : this._syntheticLegacyId(layer, entry.timestamp ?? "", text);
        views.push({
          id,
          title: text.split(/\r?\n/)[0].trim().slice(0, 80),
          text,
          layer,
          created_at: entry.timestamp,
          tags: entry.tags ?? [],
          metadata: entry.metadata,
        });
      }
    };

    push("episodic", this._episodic.getAll());
    push("semantic", this._semantic.getAll());
    push("procedural", this._procedural.getAll());
    return views;
  }

  /** Stable id for legacy records written before ids were mandatory. */
  private _syntheticLegacyId(layer: string, timestamp: string, text: string): string {
    const hash = createHash("sha1")
      .update(`${layer}\u0000${timestamp}\u0000${text}`)
      .digest("hex")
      .slice(0, 16);
    return `legacy-${hash}`;
  }

  /**
   * Enumerate preference keys from the SAME authority as `getPreference()`:
   * the semantic `pref:<key>` tag (MEMORY.md). R2-T1/F2 fixed the dual-source
   * split — the version-chain directory is append-only history and is no
   * longer a live read source. Every listed `pref:<key>` is therefore readable
   * through `getMemoryById`, and every semantic preference is listed.
   */
  private _preferenceIndex(): Array<{ id: string; title: string; time?: string }> {
    const out: Array<{ id: string; title: string; time?: string }> = [];
    const seen = new Set<string>();
    for (const entry of this._semantic.getAll()) {
      const prefTag = entry.tags.find((tag) => tag.startsWith("pref:"));
      if (!prefTag) continue;
      const key = prefTag.slice("pref:".length);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      out.push({
        id: `pref:${key}`,
        title: key,
        // Prefer the update stamp so "newest first" reflects the last write.
        time: entry.metadata?.updated_at ?? entry.timestamp,
      });
    }
    return out;
  }

  private _toGetResult(view: MemoryRecordView, lines?: [number, number]): MemoryGetResult {
    const decoded = this._decodeEvidenceFields(view.metadata);
    const allLines = view.text.split(/\r?\n/);
    const totalLines = allLines.length;
    let text = view.text;
    let lineRange: [number, number] | undefined;

    if (lines && Array.isArray(lines) && lines.length >= 2) {
      const requestedStart = Math.floor(Number(lines[0]));
      const requestedEnd = Math.floor(Number(lines[1]));
      const start = Number.isFinite(requestedStart) ? Math.max(1, requestedStart) : 1;
      const end = Number.isFinite(requestedEnd) ? Math.min(totalLines, requestedEnd) : totalLines;
      if (end >= start) {
        text = allLines.slice(start - 1, end).join("\n");
        lineRange = [start, end];
      } else {
        text = "";
        lineRange = [start, start];
      }
    }

    const time = this._effectiveTimeOf(view);
    return {
      id: view.id,
      title: view.title,
      text,
      memory_type: view.layer,
      ...(view.created_at ? { created_at: view.created_at } : {}),
      ...(time ? { time } : {}),
      tags: view.tags,
      ...(decoded.evidence ? { evidence: decoded.evidence } : {}),
      ...(decoded.eventTime ? { eventTime: decoded.eventTime } : {}),
      ...(lineRange ? { lineRange } : {}),
      totalLines,
    };
  }

  private _evidenceRefs(metadata: unknown): string[] {
    const decoded = this._decodeEvidenceFields(metadata);
    const refs = new Set<string>();
    for (const entry of decoded.evidence ?? []) {
      for (const ref of entry.sourceRefs) {
        const trimmed = ref.trim();
        if (trimmed) refs.add(trimmed);
      }
    }
    return [...refs];
  }

  private _refType(ref: string): "transcript" | "path" | "unknown" {
    const cleaned = ref.replace(/^`+|`+$/g, "");
    if (!cleaned) return "unknown";
    return /[\\/]/.test(cleaned) || /\.md$/i.test(cleaned) ? "path" : "transcript";
  }

  private _resolveSource(rawRef: unknown): MemorySource {
    const ref = typeof rawRef === "string" ? rawRef.trim() : "";
    if (!ref) return { ref, type: "unknown", found: false };

    const type = this._refType(ref);
    if (type === "transcript") {
      const match = this._transcript?.getTranscriptByIds([ref])[0];
      if (!match) return { ref, type, found: false };
      return this._capSource({
        ref,
        type,
        found: true,
        text: match.content ?? match.snippet,
        sessionId: match.sessionId,
        date: match.date,
      });
    }

    if (type === "path") {
      const root = path.resolve(this.workspace);
      const abs = path.isAbsolute(ref) ? path.resolve(ref) : path.resolve(root, ref);
      if (abs !== root && !abs.startsWith(root + path.sep)) return { ref, type, found: false };
      let target = abs;
      if (!fs.existsSync(target)) {
        const archived = path.join(root, "memory", "_archive", path.basename(ref));
        if (!fs.existsSync(archived)) return { ref, type, found: false };
        target = archived;
      }
      try {
        return this._capSource({ ref, type, found: true, text: fs.readFileSync(target, "utf-8") });
      } catch {
        return { ref, type, found: false };
      }
    }

    return { ref, type: "unknown", found: false };
  }

  private _capSource(source: MemorySource): MemorySource {
    if (typeof source.text === "string" && source.text.length > SOURCE_MAX_CHARS) {
      return { ...source, text: source.text.slice(0, SOURCE_MAX_CHARS), truncated: true };
    }
    return source;
  }

  // ── hybrid search API (v6.29.0) ─────────────────────────────────────

  /** Get hybrid retriever instance (lazy initialization) */
  get hybridRetriever(): HybridRetriever | null {
    if (!this._hybridRetriever) {
      this._hybridRetriever = new HybridRetriever({
        // No embedding provider is configured out of the box; the semantic leg
        // stays disabled and reports that explicitly in result metadata.
        // v7.5.0 (ADR-002): retention provider for three-way fusion
        getRetentionScore: (id: string) => {
          if (!this._retentionEnabled()) return undefined;
          return this._retention!.getRetentionScore(id);
        },
        // v7.5.0 (ADR-002): selection events from the hybrid candidate pool
        // (mergeAndDedupe output, before topK/minScore truncation)
        onEvents: (selected, missed) => {
          if (!this._retentionEnabled()) return;
          for (const r of selected) this._retentionEvent(r as unknown as Record<string, unknown>, "selected");
          for (const r of missed) this._retentionEvent(r as unknown as Record<string, unknown>, "missed");
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
    // Initialize + index on first use. The old fallback to search() reported
    // keywordCount=0 forever because the retriever was never constructed.
    const retriever = this.hybridRetriever!;
    // ADR-007 §3: timeRange must use eventTime ?? created_at. The retriever's
    // structured filter only sees created_at, so strip the range there and
    // apply the effective-time range to the final result set here.
    const timeRange = options?.filters?.timeRange;
    const retrieverOptions = timeRange && options?.filters
      ? { ...options, filters: { ...options.filters, timeRange: undefined } }
      : options;
    // v7.5.0 (ADR-002): suppress search() events during the semantic leg —
    // those are partial candidates (limit = 2×topK), not final selections;
    // the hybrid retriever reports selected/missed once from the full pool
    this._retentionSuppressSearch = true;
    try {
      const result = retriever.search(query, retrieverOptions);
      return timeRange
        ? { ...result, results: this._applyTimeRangeToHybrid(result.results, timeRange) }
        : this._decorateHybridResults(result);
    } finally {
      this._retentionSuppressSearch = false;
    }
  }

  /** Additive evidence/eventTime decoration for hybrid results (ADR-007). */
  private _decorateHybridResults(result: HybridSearchResult): HybridSearchResult {
    return {
      ...result,
      results: result.results.map((r) => {
        const decoded = this._decodeEvidenceFields(r.metadata);
        return {
          ...r,
          ...(decoded.eventTime ? { eventTime: decoded.eventTime } : {}),
          ...(decoded.evidence ? { evidence: decoded.evidence } : {}),
        };
      }),
    };
  }

  /** Apply `eventTime ?? created_at` range filtering to hybrid results. */
  private _applyTimeRangeToHybrid(
    results: HybridSearchResult["results"],
    range: { start?: string; end?: string },
  ): HybridSearchResult["results"] {
    const since = range.start ? Date.parse(range.start) : NaN;
    const until = range.end ? Date.parse(range.end) : NaN;
    const decorated = results.map((r) => {
      const decoded = this._decodeEvidenceFields(r.metadata);
      const timestamp = typeof r.metadata?.timestamp === "string" ? r.metadata.timestamp : r.timestamp;
      return {
        out: {
          ...r,
          ...(decoded.eventTime ? { eventTime: decoded.eventTime } : {}),
          ...(decoded.evidence ? { evidence: decoded.evidence } : {}),
        },
        effectiveTime: decoded.eventTime ?? timestamp,
      };
    });
    return decorated
      .filter(({ effectiveTime }) => {
        const t = effectiveTime ? Date.parse(effectiveTime) : NaN;
        if (Number.isNaN(t)) return false; // no usable time → cannot prove it is in range
        if (!Number.isNaN(since) && t < since) return false;
        if (!Number.isNaN(until) && t > until) return false;
        return true;
      })
      .map((d) => d.out);
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
      const decoded = this._decodeEvidenceFields(m.metadata);
      documents.push({
        id: (m as any).id ?? m.timestamp ?? String(Date.now()),
        text: m.content ?? "",
        metadata: {
          type: "episodic", tags: m.tags, timestamp: m.timestamp, session_id: m.session_id,
          ...(decoded.eventTime ? { [EVENT_TIME_META_KEY]: decoded.eventTime } : {}),
          ...(decoded.evidence ? { [EVIDENCE_META_KEY]: encodeEvidenceMetadata(decoded.evidence) } : {}),
        },
      });
    }

    // Index semantic memories
    for (const m of this._semantic.getAll()) {
      const decoded = this._decodeEvidenceFields(m.metadata);
      documents.push({
        id: (m as any).id ?? m.timestamp ?? String(Date.now()),
        text: m.content ?? "",
        metadata: {
          type: "semantic", tags: m.tags, timestamp: m.timestamp,
          ...(decoded.eventTime ? { [EVENT_TIME_META_KEY]: decoded.eventTime } : {}),
          ...(decoded.evidence ? { [EVIDENCE_META_KEY]: encodeEvidenceMetadata(decoded.evidence) } : {}),
        },
      });
    }

    // Index procedural memories
    for (const m of this._procedural.getAll()) {
      const decoded = this._decodeEvidenceFields(m.metadata);
      documents.push({
        id: (m as any).id ?? m.timestamp ?? String(Date.now()),
        text: m.content ?? "",
        metadata: {
          type: "procedural", tags: m.tags, timestamp: m.timestamp,
          ...(decoded.eventTime ? { [EVENT_TIME_META_KEY]: decoded.eventTime } : {}),
          ...(decoded.evidence ? { [EVIDENCE_META_KEY]: encodeEvidenceMetadata(decoded.evidence) } : {}),
        },
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
    this._strategyRegistry.register(new ErrorPatternCardStrategy());
  }

  private _buildStrategyContext(): import("./storage/strategy-registry.js").StrategyContext {
    return {
      episodic: this._episodic,
      semantic: this._semantic,
      procedural: this._procedural,
      entityIndex: this._entityIndex,
      versionChain: this._versionChain!,
      errorPatternVersionChain: this._errorPatternChain!,
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

  /**
   * Rollback preference to a previous version.
   *
   * Known boundary (R2-T1/F2): when semantic has no record for `prefKey`, the
   * rollback only appends the version-chain entry — the live authority stays
   * absent (no semantic update). Split legacy data is not migrated; this ticket
   * only guarantees consistency for new writes/updates.
   */
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
