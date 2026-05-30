// claw-mem v5.0.0 — Public API (TypeScript)
export { EpisodicStorage } from "./storage/episodic";
export { SemanticStorage } from "./storage/semantic";
export { ProceduralStorage } from "./storage/procedural";
export { GroundTruthStore } from "./storage/ground_truth";
export { InMemoryIndex } from "./storage/index";
export { BaseStorage } from "./storage/base";
export * from "./errors";
export type { MemoryRecord, EpisodicEntry, SemanticEntry, ProceduralEntry, NGramIndex, BM25Params } from "./types";

// Retrieval module
export {
  BaseRetriever,
  BM25,
  KeywordRetriever,
  tokenize,
  ThreeTierRetriever,
  MemoryLayer,
  detectIntent,
  HybridRouter,
  QueryType,
  QueryCache,
  getQueryCache,
  resetQueryCache,
  SynonymExpander,
  BUILTIN_SYNONYMS,
} from "./retrieval";
export type { RetrievalResult, RetrievalDocument, MemoryResult, LayerRetrievalContext } from "./retrieval";
