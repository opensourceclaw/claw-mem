// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * claw-mem merge module - Semantic memory merge pipeline (v4.7.0)
 */

export { ConflictDetector } from "./conflict_detector.js";
export type { ConflictReport, ConflictResolution } from "./conflict_detector.js";
export { SemanticMergeScheduler, cosineSimilarity } from "./semantic_merger.js";
