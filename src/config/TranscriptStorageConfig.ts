/**
 * claw-mem v6.42.0 — Transcript Storage Configuration
 */

export interface TranscriptStorageConfig {
  maxFileSize: number;           // Default: 102400 (100KB)
  maxEntriesPerFile: number;     // Default: 500
  warningThreshold: number;      // Default: 0.8 (80%)
  autoRotate: boolean;           // Default: true
  generateSummary: boolean;      // Default: true
  summaryMethod: "simple" | "llm"; // Default: "simple"
}

export const DEFAULT_TRANSCRIPT_STORAGE_CONFIG: TranscriptStorageConfig = {
  maxFileSize: 100 * 1024,       // 100KB
  maxEntriesPerFile: 500,
  warningThreshold: 0.8,
  autoRotate: true,
  generateSummary: true,
  summaryMethod: "simple",
};
