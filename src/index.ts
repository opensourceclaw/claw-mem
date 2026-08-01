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
export { MemoryGovernance, DEFAULT_GOVERNANCE_CONFIG, type MemoryGovernanceConfig, type MaintainDecision, type GovernanceMetrics } from "./memory/governance.js";
// v6.41.0 Governance API
export { MemoryGovernanceManager, DefaultGovernancePolicy } from "./governance/memory-governance.js";
export type { GovernedEntry, PolicyDecision, GovernancePolicy } from "./governance/memory-governance.js";
export { DeletionPropagator, EntityRelationshipGraph } from "./governance/deletion-propagator.js";
export type { CascadeOptions, DeletionResult } from "./governance/deletion-propagator.js";
export { AuditTrail } from "./governance/audit-trail.js";
export type { AuditEntry, AuditQuery } from "./governance/audit-trail.js";
// v6.43.0: MemoryContextBridge
export { MemoryContextBridge } from "./bridge/MemoryContextBridge.js";
export type { MemoryContextReport, CompressionRecommendation, CompressionResult } from "./bridge/types.js";
export { type MemoryBridgeConfig, DEFAULT_MEMORY_BRIDGE_CONFIG } from "./config/MemoryBridgeConfig.js";
export { TruncateStrategy, SummarizeStrategy } from "./compression/CompressionStrategy.js";
export type { CompressionStrategy } from "./compression/CompressionStrategy.js";

// v6.44.0: Unified Memory Monitor
export { MemoryMonitor, DEFAULT_MEMORY_MONITOR_CONFIG } from "./monitoring/index.js";
export type { MemoryMetrics, MemoryMonitorConfig } from "./monitoring/index.js";

// v7.0.0: Capability Layer
export { MemoryCapability } from "./capability/index.js";
export type {
  IMemoryCapability,
  MemorySearchOptions, MemorySearchResult,
  MemoryContextResult, MemoryStatsResult,
} from "./capability/index.js";
