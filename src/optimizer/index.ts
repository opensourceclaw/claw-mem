// claw-mem v6.35.0 — Optimizer Module Index
//
// Exports for the StructureOptimizer module.
//
// Licensed under the Apache License, Version 2.0

export { StructureOptimizer } from "./structure-optimizer.js";

export { HealthReporter } from "./health-reporter.js";
export { IndexEvolver } from "./index-evolver.js";

export {
  // Enums
  IndexType,
  SuggestionReason,
  SuggestionPriority,
  OptimizeSuggestionType,

  // Interfaces
  type IndexStat,
  type IndexMetrics,
  type HealthReport,
  type HealthReportMetadata,
  type MissingIndexSuggestion,
  type QueryPattern,
  type DegradedQuery,
  type OptimizeSuggestion,
  type OptimizeSuggestionDetails,
  type OptimizeResult,
  type OptimizeRecord,
  type StructureOptimizerOptions,
  type OptimizeOptions,
  type OptimizerStats,

  // Defaults
  DEFAULT_OPTIMIZER_OPTIONS,
  DEFAULT_OPTIMIZE_OPTIONS,
} from "./types.js";
