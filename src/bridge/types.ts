/**
 * claw-mem v6.43.0 — Bridge Types
 * Type definitions for MemoryContextBridge.
 */

/** Task type from claw-ctx, redefined for fallback when claw-ctx unavailable. */
export type ContextTaskType = "simple_lookup" | "multi_lookup" | "summarization" | "complex_reasoning";

/** Memory size report with optional compression recommendation. */
export interface MemoryContextReport {
  sessionId: string;
  filePath: string;
  totalBytes: number;
  tokenEstimate: number;
  entryCount: number;
  oldestEntry?: Date;
  newestEntry?: Date;
  compressionRecommendation?: CompressionRecommendation;
}

/** Recommendation for compression based on budget analysis. */
export interface CompressionRecommendation {
  shouldCompact: boolean;
  reason: string;
  targetTokens: number;
  taskType: ContextTaskType;
  strategy: "truncate" | "summarize" | "compress";
}

/** Result of a compression operation. */
export interface CompressionResult {
  strategy: "truncate" | "summarize" | "compress";
  originalTokens: number;
  newTokens: number;
  savedTokens: number;
  error?: string;
}
