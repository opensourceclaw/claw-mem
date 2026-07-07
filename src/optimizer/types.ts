// claw-mem v6.35.0 — Optimizer Types (TypeScript)
//
// Type definitions for the StructureOptimizer module.
// Supports index health assessment and optimization suggestions.
//
// Licensed under the Apache License, Version 2.0

// ============================================================================
// Index Types
// ============================================================================

/** Index type enumeration */
export enum IndexType {
  BM25 = "bm25",
  ENTITY_COOC = "entity_cooc",
  NGRAM = "ngram",
  SEMANTIC = "semantic",
  TRANSCRIPT_TIME = "transcript_time",
  PREFERENCE_KEY = "preference_key",
}

/** Index statistics */
export interface IndexStat {
  name: string;
  type: IndexType;
  hitRate: number;
  avgLatency: number;
  size: number;
  lastUsed: number;
  queryCount: number;
  createdAt: number;
  metrics?: IndexMetrics;
}

/** Additional index metrics */
export interface IndexMetrics {
  entryCount?: number;
  avgEntrySize?: number;
  fragmentation?: number;
  memoryUsage?: number;
}

// ============================================================================
// Health Report Types
// ============================================================================

/** Health assessment report */
export interface HealthReport {
  overallScore: number;
  timestamp: number;
  indexStats: IndexStat[];
  unusedIndexes: string[];
  missingIndexes: MissingIndexSuggestion[];
  degradedQueries: DegradedQuery[];
  metadata: HealthReportMetadata;
}

/** Health report metadata */
export interface HealthReportMetadata {
  assessmentTimeMs: number;
  queriesAnalyzed: number;
  indexesAnalyzed: number;
  cacheHit: boolean;
}

// ============================================================================
// Suggestion Types
// ============================================================================

/** Reason for index suggestion */
export enum SuggestionReason {
  FREQUENT_UNINDEXED = "frequent_unindexed",
  SLOW_PERFORMANCE = "slow_performance",
  MISSING_ENTITY_COVERAGE = "missing_entity_coverage",
  TIME_BASED_OPTIMIZATION = "time_based_optimization",
}

/** Suggestion priority */
export enum SuggestionPriority {
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

/** Query pattern for missing index detection */
export interface QueryPattern {
  pattern: string;
  frequency: number;
  avgLatency: number;
  lastSeen: number;
}

/** Suggestion for missing index */
export interface MissingIndexSuggestion {
  id: string;
  type: IndexType;
  reason: SuggestionReason;
  targetPatterns: QueryPattern[];
  estimatedImprovement: number;
  confidence: number;
  priority: SuggestionPriority;
}

/** Degraded query detection */
export interface DegradedQuery {
  patternId: string;
  query: string;
  avgLatency: number;
  expectedLatency: number;
  degradationFactor: number;
  occurrenceCount: number;
  lastOccurrence: number;
  potentialCauses: string[];
}

/** Optimization suggestion type */
export enum OptimizeSuggestionType {
  CREATE_INDEX = "create_index",
  DELETE_INDEX = "delete_index",
  MERGE_INDEXES = "merge_indexes",
  SPLIT_INDEX = "split_index",
  REBUILD_INDEX = "rebuild_index",
  UPDATE_PARAMS = "update_params",
}

/** Optimization suggestion */
export interface OptimizeSuggestion {
  id: string;
  type: OptimizeSuggestionType;
  targetIndex?: string;
  description: string;
  estimatedBenefit: number;
  estimatedRisk: number;
  confidence: number;
  details: OptimizeSuggestionDetails;
  timestamp: number;
}

/** Optimization suggestion details */
export interface OptimizeSuggestionDetails {
  indexes: string[];
  params?: Record<string, unknown>;
  steps?: string[];
}

/** Optimization result */
export interface OptimizeResult {
  executed: boolean;
  suggestions: OptimizeSuggestion[];
  duration: number;
  estimatedImprovement: number;
}

/** Optimization record for history */
export interface OptimizeRecord {
  id: string;
  timestamp: number;
  suggestionsApplied: OptimizeSuggestion[];
  result: "success" | "partial" | "failed" | "skipped";
  duration: number;
  healthBefore: number;
  healthAfter?: number;
}

// ============================================================================
// Options Types
// ============================================================================

/** StructureOptimizer options */
export interface StructureOptimizerOptions {
  enableCache?: boolean;
  cacheTtlMs?: number;
  minQueryCount?: number;
  unusedDaysThreshold?: number;
  minHitRateThreshold?: number;
  maxSuggestions?: number;
}

/** Default optimizer options */
export const DEFAULT_OPTIMIZER_OPTIONS: Required<StructureOptimizerOptions> = {
  enableCache: true,
  cacheTtlMs: 60000,
  minQueryCount: 100,
  unusedDaysThreshold: 7,
  minHitRateThreshold: 0.3,
  maxSuggestions: 20,
};

/** Optimize options */
export interface OptimizeOptions {
  autoApply?: boolean;
  types?: OptimizeSuggestionType[];
  maxChanges?: number;
}

/** Default optimize options */
export const DEFAULT_OPTIMIZE_OPTIONS: Required<OptimizeOptions> = {
  autoApply: false,
  types: [],
  maxChanges: 5,
};

// ============================================================================
// Statistics Types
// ============================================================================

/** Optimizer statistics */
export interface OptimizerStats {
  totalAssessments: number;
  totalSuggestions: number;
  avgAssessmentTimeMs: number;
  avgHealthScore: number;
  lastAssessmentTime: number;
}
