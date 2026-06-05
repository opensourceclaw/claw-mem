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

// Core (beta.3)
export { MemoryManager, getMemoryManager, resetMemoryManager } from "./memory_manager";
export { ComponentFactory, getDefaultFactory, resetDefaultFactory } from "./factories";
export type { FactoryConfig } from "./factories";
export { MemoryConfig, ConfigManager, getConfig, reloadConfig } from "./config";
export { ContextFormatter, ContextInjector, formatMemoryContext, injectMemoriesToPrompt } from "./context_injection";
export type { InjectedContext } from "./context_injection";
export { handleRequest, plugin } from "./bridge";
export type { JsonRpcRequest, JsonRpcResponse } from "./bridge";
export { DataPortability } from "./data_portability";
export { ImportanceScorer } from "./importance";
export type { ImportanceResult } from "./importance";
export { extractSummary } from "./session_summary";
export type { SessionSummary } from "./session_summary";
export { DriftHistoryStore, DEFAULT_DRIFT_HISTORY_CONFIG, type DriftRecord, type DriftTrend, type DriftHistoryConfig, type DriftSummary } from "./drift-history-store";
export { MemoryRelationshipEnhancer, EntityChaining, DecisionLineage, CausalGraph, type EntityNode, type EntityLink, type DecisionRecord, type LineageChain, type CausalEvent, type CausalLink } from "./memory-relationship-enhancer";
