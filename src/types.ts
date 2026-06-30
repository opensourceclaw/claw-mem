// claw-mem v5.0.0 — Global Type Definitions

/** Memory record as stored in all backends. */
export interface MemoryRecord {
  id: string;
  text: string;
  memory_type: "episodic" | "semantic" | "procedural";
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
