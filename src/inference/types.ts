// claw-mem v6.34.0 — Inference Types (TypeScript)
//
// Type definitions for the InferenceEngine module.
// Supports knowledge derivation, contradiction detection, and chain visualization.
//
// Licensed under the Apache License, Version 2.0

import type { MemoryId } from "./engine.js";

// ============================================================================
// Inference Step Types
// ============================================================================

/** Step type in an inference chain */
export enum InferenceStepType {
  /** Original memory or fact used as premise */
  PREMISE = "premise",
  /** Inference rule applied */
  RULE = "rule",
  /** Intermediate derivation result */
  DERIVATION = "derivation",
  /** Final conclusion */
  CONCLUSION = "conclusion",
}

/** Single step in an inference chain */
export interface InferenceStep {
  /** Unique step identifier */
  stepId: string;
  /** Step type classification */
  type: InferenceStepType;
  /** Human-readable content */
  content: string;
  /** Memory IDs referenced as evidence */
  memories: MemoryId[];
  /** Confidence score [0.0, 1.0] */
  confidence: number;
  /** Timestamp when step was created */
  timestamp: number;
}

/** Complete inference chain */
export interface InferenceChain {
  /** Unique chain identifier */
  chainId: string;
  /** Original query */
  query: string;
  /** Ordered inference steps */
  steps: InferenceStep[];
  /** Derived knowledge results */
  result: DerivedKnowledge[];
  /** Overall chain confidence */
  confidence: number;
  /** Creation timestamp */
  timestamp: number;
  /** Schema version */
  version: string;
}

// ============================================================================
// Derived Knowledge Types
// ============================================================================

/** Derivation type */
export enum DerivationType {
  /** A→B, B→C, therefore A→C */
  TRANSITIVE = "transitive",
  /** Multiple instances → general pattern */
  INDUCTIVE = "inductive",
  /** Co-occurrence → association */
  ASSOCIATIVE = "associative",
  /** Behavior pattern → preference */
  PREFERENCE = "preference",
}

/** Derived knowledge item */
export interface DerivedKnowledge {
  /** Unique knowledge identifier */
  id: string;
  /** Derivation type */
  type: DerivationType;
  /** Subject entity */
  subject: string;
  /** Predicate/relationship */
  predicate: string;
  /** Object entity or value */
  object: string;
  /** Confidence score [0.0, 1.0] */
  confidence: number;
  /** Source chain ID */
  chainId: string;
  /** Source memory IDs */
  sourceMemoryIds: MemoryId[];
  /** Creation timestamp */
  timestamp: number;
}

// ============================================================================
// Derivation Options
// ============================================================================

/** Options for knowledge derivation */
export interface DeriveOptions {
  /** Maximum inference steps (default: 10) */
  maxSteps?: number;
  /** Minimum confidence threshold (default: 0.5) */
  confidenceThreshold?: number;
  /** Derivation types to apply */
  derivationTypes?: DerivationType[];
  /** Maximum memories to analyze (default: 100) */
  maxMemories?: number;
  /** Enable caching (default: true) */
  useCache?: boolean;
  /** Cache TTL in milliseconds (default: 3600000) */
  cacheTtlMs?: number;
  /** Include visualization output */
  visualize?: boolean;
  /** Visualization formats */
  visualizationFormats?: ("text" | "json" | "mermaid")[];
}

/** Default derive options */
export const DEFAULT_DERIVE_OPTIONS: Required<Omit<DeriveOptions, "derivationTypes" | "visualizationFormats">> & {
  derivationTypes: DerivationType[];
  visualizationFormats: ("text" | "json")[];
} = {
  maxSteps: 10,
  confidenceThreshold: 0.5,
  derivationTypes: [DerivationType.TRANSITIVE],
  maxMemories: 100,
  useCache: true,
  cacheTtlMs: 3600000,
  visualize: false,
  visualizationFormats: ["text", "json"],
};

/** Result of knowledge derivation */
export interface DeriveResult {
  /** Derived knowledge items */
  knowledge: DerivedKnowledge[];
  /** Inference chain */
  chain: InferenceChain;
  /** Overall confidence */
  confidence: number;
  /** Cache hit status */
  cacheHit: boolean;
  /** Processing time */
  processingTimeMs: number;
  /** Visualization output (if requested) */
  visualization?: ChainOutput;
}

// ============================================================================
// Contradiction Types
// ============================================================================

/** Contradiction type */
export enum ContradictionType {
  /** Direct value conflict */
  DIRECT = "direct",
  /** Timeline impossibility */
  TEMPORAL = "temporal",
  /** Behavior vs declared preference */
  PREFERENCE = "preference",
  /** Entity attribute conflict */
  ENTITY = "entity",
}

/** Contradiction severity */
export enum ContradictionSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
}

/** Options for contradiction detection */
export interface ContradictionOptions {
  /** Contradiction types to detect */
  types?: ContradictionType[];
  /** Minimum confidence to report */
  minConfidence?: number;
  /** Entity ID to scope detection */
  entityId?: string;
  /** Include resolution suggestions */
  includeSuggestions?: boolean;
  /** Maximum results */
  maxResults?: number;
}

/** Default contradiction options */
export const DEFAULT_CONTRADICTION_OPTIONS: Required<Omit<ContradictionOptions, "entityId">> = {
  types: [ContradictionType.DIRECT],
  minConfidence: 0.7,
  includeSuggestions: true,
  maxResults: 50,
};

/** Conflict item in a contradiction */
export interface ConflictItem {
  memoryId: MemoryId;
  content: string;
  claim: string;
  confidence: number;
  timestamp: number;
}

/** Resolution suggestion */
export interface ContradictionSuggestion {
  type: "keep_newer" | "keep_higher_confidence" | "merge" | "ask_user" | "keep_both";
  explanation: string;
  preferredMemoryId?: MemoryId;
  confidence: number;
}

/** Contradiction report */
export interface ContradictionReport {
  id: string;
  type: ContradictionType;
  severity: ContradictionSeverity;
  description: string;
  conflicts: ConflictItem[];
  confidence: number;
  timestamp: number;
  suggestions?: ContradictionSuggestion[];
}

// ============================================================================
// Chain Visualization Types
// ============================================================================

/** Chain visualization output */
export interface ChainOutput {
  text: string;
  json: object;
  mermaid?: string;
}

/** Chain visualization options */
export interface ChainVisualizationOptions {
  formats: ("text" | "json" | "mermaid")[];
  showConfidence?: boolean;
  showMemoryRefs?: boolean;
  indentSize?: number;
}