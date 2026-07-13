// claw-mem v5.0.0 — Public API (TypeScript)
export { EpisodicStorage } from "./storage/episodic.js";
export { SemanticStorage } from "./storage/semantic.js";
export { ProceduralStorage } from "./storage/procedural.js";
export { GroundTruthStore } from "./storage/ground_truth.js";
export { InMemoryIndex } from "./storage/index.js";
export { BaseStorage } from "./storage/base.js";
export * from "./errors.js";
export type { MemoryRecord, EpisodicEntry, SemanticEntry, ProceduralEntry, NGramIndex, BM25Params } from "./types.js";

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
} from "./retrieval/index.js";
export type { RetrievalResult, RetrievalDocument, MemoryResult, LayerRetrievalContext } from "./retrieval/index.js";

// Core (beta.3)
export { MemoryManager, getMemoryManager, resetMemoryManager } from "./memory_manager.js";
export { ComponentFactory, getDefaultFactory, resetDefaultFactory } from "./factories.js";
export type { FactoryConfig } from "./factories.js";
export { MemoryConfig, ConfigManager, getConfig, reloadConfig } from "./config.js";
export { ContextFormatter, ContextInjector, formatMemoryContext, injectMemoriesToPrompt } from "./context_injection.js";
export type { InjectedContext } from "./context_injection.js";
export { handleRequest, plugin } from "./bridge.js";
export type { JsonRpcRequest, JsonRpcResponse } from "./bridge.js";
export { DataPortability } from "./data_portability.js";
export { ImportanceScorer } from "./importance.js";
export type { ImportanceResult } from "./importance.js";
export { DriftHistoryStore, DEFAULT_DRIFT_HISTORY_CONFIG, type DriftRecord, type DriftTrend, type DriftHistoryConfig, type DriftSummary } from "./drift-history-store.js";
export { MemoryRelationshipEnhancer, EntityChaining, DecisionLineage, CausalGraph, type EntityNode, type EntityLink, type DecisionRecord, type LineageChain, type CausalEvent, type CausalLink } from "./memory-relationship-enhancer.js";
