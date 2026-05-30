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
