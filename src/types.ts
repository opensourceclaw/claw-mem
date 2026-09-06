// claw-mem v5.0.0 — Global Type Definitions

/** Memory types supported by storage strategies */
export type MemoryType = "episodic" | "semantic" | "procedural" | "session_snapshot" | "fact" | "preference" | "error_pattern_card" | string;

// ============================================================================
// Error Pattern Card Types (v7.6.0, ADR-003/004)
// ============================================================================

/**
 * Dominant component attribution for an error pattern card (ADR-004).
 * Semantics mapped from Recuris E/W/rho/C (arXiv 2608.24876 v1) onto the
 * claw-mem operation surface — the layer the fix must touch:
 *   skill-defect        (E): card/resolution content wrong or missing → fix card content
 *   state-defect        (W): runtime state not recorded/updated → fix state records
 *   invocation-timing   (rho): card exists but recall timing/condition misfires → fix recall rules
 *   transition-judgment (C): completion/verification predicate wrong → fix verification standard
 * One card carries ONE dominant category; multi-cause failures explain the rest
 * in the narrative and enumerate the main fix target.
 * Alignment note: claw-rsi's card contract (T3) is not finalized — claw-mem is
 * the source of truth; the stub alignment test locks both sides against drift.
 */
export type RootCauseCategory =
  | "skill-defect"
  | "state-defect"
  | "invocation-timing"
  | "transition-judgment"
  | (string & {}); // tolerant future extension, same convention as MemoryType

export function isRootCauseCategory(v: unknown): v is RootCauseCategory {
  return (
    typeof v === "string" &&
    (v === "skill-defect" ||
      v === "state-defect" ||
      v === "invocation-timing" ||
      v === "transition-judgment")
  );
}

/** Trigger/symptom signature: when the card should be recalled, and how the error looks. */
export interface ErrorSignature {
  trigger: string; // 触发条件(何时该想起这张卡)
  symptom: string; // 表象(错误的可观察特征)
}

/** Card effectiveness evidence (ADR-005). System-writable only; never caller-set. */
export interface CardEffectiveness {
  hitCount: number;
  avoidedCount: number;
  lastHitAt?: string; // ISO-8601
  inactive: boolean; // demotion flag — never deleted
  inactivatedAt?: string; // ISO-8601
}

export const DEFAULT_CARD_EFFECTIVENESS: CardEffectiveness = {
  hitCount: 0,
  avoidedCount: 0,
  inactive: false,
};

/** Structured error pattern card (full schema, ADR-003). */
export interface ErrorPatternCard {
  cardId: string; // stable id = version-chain primary key (semantic slug `epc:...`)
  errorSignature: ErrorSignature;
  rootCauseCategory: RootCauseCategory;
  resolution: string; // correct-resolution essentials (human readable)
  verification?: string; // optional associated verification command/assertion
  effectiveness: CardEffectiveness;
  provenance: { source: string; author?: string };
  createdAt: string; // ISO-8601
  updatedAt?: string; // ISO-8601
}

/** Write input for storeErrorPatternCard (effectiveness/createdAt are server-side). */
export interface ErrorPatternCardInput {
  cardId?: string; // semantic slug; system-generated (`epc:...`) when omitted
  errorSignature: ErrorSignature;
  rootCauseCategory: RootCauseCategory;
  resolution: string;
  verification?: string;
  provenance: { source: string; author?: string };
}

/** Memory record as stored in all backends. */
export interface MemoryRecord {
  id: string;
  text: string;
  memory_type: MemoryType;
  created_at: string; // ISO-8601
  updated_at?: string;
  metadata: Record<string, unknown>;
  tags: string[];
}

/** Episodic memory dict (read from Markdown file). */
export interface EpisodicEntry {
  timestamp: string;
  content: string;
  tags: string[];
  session_id?: string;
  id?: string;
  metadata: Record<string, string>;
  type: "episodic";
  source: string;
}

/** Semantic memory dict (read from Markdown file). */
export interface SemanticEntry {
  id?: string;
  timestamp: string;
  content: string;
  tags: string[];
  metadata: Record<string, string>;
  type: "semantic";
  source: string;
}

/** Procedural memory dict (read from Markdown file). */
export interface ProceduralEntry {
  timestamp: string;
  content: string;
  tags: string[];
  metadata: Record<string, string>;
  type: "procedural";
  source: string;
}

/** Ground truth session record. */
export interface GroundTruthSessionRecord {
  record_id: string;
  session_id: string;
  messages: Array<{ role: string; content: string }>;
  timestamp: number;
  metadata: Record<string, unknown>;
}

/** N-gram index structure. */
export interface NGramIndex {
  version: string;
  ngram_index: Record<string, string[]>;
  bm25: BM25Params;
  timestamp: number;
}

/** BM25 index parameters. */
export interface BM25Params {
  doc_freq: number;
  doc_count: number;
  avg_doc_len: number;
}

/** Raw memory entry for indexing. */
export interface MemoryEntry {
  id: string;
  content: string;
}

// ============================================================================
// Entity-Relation Index Types (v6.30.0)
// ============================================================================

/** Entity types for extraction */
export type EntityType = "person" | "project" | "tool" | "concept" | "file" | "event" | "other";

/** Extracted entity from text */
export interface Entity {
  name: string;
  type: EntityType;
  position: number;    // character offset in text
  confidence: number;  // 0-1
}

/** Extraction rule configuration */
export interface ExtractionRule {
  pattern: RegExp;
  type: EntityType;
  confidence: number;
  nameTransform?: (match: string) => string;
}

/** Entity record stored in index */
export interface EntityRecord {
  name: string;
  type: EntityType;
  memoryIds: string[];       // All memory IDs containing this entity
  firstSeen: number;         // First occurrence timestamp
  lastSeen: number;          // Most recent occurrence timestamp
  occurrenceCount: number;   // Total occurrence count
}

/** Co-occurrence entry */
export interface CoocEntry {
  entityA: string;
  entityB: string;
  count: number;             // Co-occurrence count
  lastCooc: number;          // Last co-occurrence timestamp
}

/** Entity search result */
export interface EntitySearchResult {
  entity: EntityRecord;
  related: string[];         // Co-occurring entity names (sorted by count desc)
}

/** Resolution result */
export interface ResolutionResult {
  canonical: string;        // Normalized name
  alternatives: string[];   // Known aliases
  isNew: boolean;           // Is this a new entity?
}

/** Entity index configuration */
export interface EntityConfig {
  /** Enable entity indexing (default: true) */
  enabled: boolean;
  /** Maximum entities per memory (default: 50) */
  maxEntitiesPerMemory: number;
  /** Custom extraction rules */
  customRules?: ExtractionRule[];
  /** Custom stopwords */
  customStopwords?: string[];
  /** Custom alias mappings */
  customAliases?: Record<string, string[]>;
}

/** Default entity configuration */
export const DEFAULT_ENTITY_CONFIG: EntityConfig = {
  enabled: true,
  maxEntitiesPerMemory: 50,
};
