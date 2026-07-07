// claw-mem v6.34.0 — Inference Module Index
//
// Exports for the InferenceEngine module.
//
// Licensed under the Apache License, Version 2.0

export { InferenceEngine, type InferenceEngineOptions, type MemoryForInference, type InferenceEngineStats } from "./engine.js";
export type { MemoryId } from "./engine.js";

export { KnowledgeDeriver } from "./knowledge-deriver.js";
export { ContradictionDetector } from "./contradiction-detector.js";
export { ChainVisualizer } from "./chain-visualizer.js";

export {
  // Enums
  InferenceStepType,
  DerivationType,
  ContradictionType,
  ContradictionSeverity,

  // Interfaces
  type InferenceStep,
  type InferenceChain,
  type DerivedKnowledge,
  type DeriveOptions,
  type DeriveResult,
  DEFAULT_DERIVE_OPTIONS,
  type ContradictionOptions,
  DEFAULT_CONTRADICTION_OPTIONS,
  type ContradictionReport,
  type ConflictItem,
  type ContradictionSuggestion,
  type ChainOutput,
  type ChainVisualizationOptions,
} from "./types.js";
