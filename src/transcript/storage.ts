// claw-mem v6.28.0 — Transcript Storage
// Stores complete conversation transcripts for recovery

import * as fs from 'fs';
import * as path from 'path';
import { TranscriptFormatter, type TranscriptEntry, type TranscriptMetadata } from './formatter.js';
import type { Recap, RecapGenerator } from './recap-generator.js';
import { type TranscriptStorageConfig, DEFAULT_TRANSCRIPT_STORAGE_CONFIG } from '../config/TranscriptStorageConfig.js';

export interface TranscriptConfig {
  enabled: boolean;           // Default: true
  ttlDays: number;           // Default: 30
  format: 'markdown' | 'json';  // Default: markdown
}

export interface TranscriptMatch {
  sessionId: string;
  date: string;
  snippet: string;
  score: number;
}

export interface TranscriptLogger {
  info?: (msg: string) => void;
  warn?: (msg: string) => void;
  error?: (msg: string) => void;
  debug?: (msg: string) => void;
}

const DEFAULT_CONFIG: TranscriptConfig = {
  enabled: true,
  ttlDays: 30,
  format: 'markdown',
};

export class TranscriptStorage {
  private workspace: string;
  private config: TranscriptConfig;
  private formatter: TranscriptFormatter;
  private logger?: TranscriptLogger;
  private currentSession: string | null = null;
  private currentFile: string | null = null;
  private currentMetadata: TranscriptMetadata | null = null;
  private entries: TranscriptEntry[] = [];

  /** v6.36.0: Maximum entries to keep in memory buffer */
  private static readonly MAX_ENTRIES_BUFFER = 500;

  constructor(workspace: string, config?: Partial<TranscriptConfig>, logger?: TranscriptLogger) {
    this.workspace = workspace;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.formatter = new TranscriptFormatter();
    this.logger = logger;

    // Ensure transcripts directory exists
    const transcriptsDir = path.join(workspace, 'transcripts');
    if (!fs.existsSync(transcriptsDir)) {
      fs.mkdirSync(transcriptsDir, { recursive: true });
      this.logger?.debug?.(`[TranscriptStorage] Created transcripts directory: ${transcriptsDir}`);
    }
  }

  /**
   * Start a new transcript session.
   */
  startSession(sessionId: string, channel: string = 'api'): void {
    if (!this.config.enabled) {
      this.logger?.warn?.('[TranscriptStorage] startSession called but disabled');
      return;
    }

    try {
      this.currentSession = sessionId;
      this.entries = [];
      this.currentMetadata = {
        session: sessionId,
        started: new Date().toISOString(),
        channel,
      };

      // Create date directory and file path
      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(this.workspace, 'transcripts', today);
      if (!fs.existsSync(dateDir)) {
        fs.mkdirSync(dateDir, { recursive: true });
      }

      this.currentFile = path.join(dateDir, `session-${sessionId}.md`);

      // Write initial header
      const header = this.formatter.buildHeader(this.currentMetadata);
      fs.writeFileSync(this.currentFile, header, 'utf-8');
      this.logger?.debug?.(`[TranscriptStorage] Started session ${sessionId}, file: ${this.currentFile}`);
    } catch (err) {
      this.logger?.error?.(`[TranscriptStorage] startSession error: ${err}`);
      this.currentFile = null;
      this.currentSession = null;
    }
  }

  /**
   * Append a message to the current transcript.
   * v6.36.0: Limits in-memory buffer to MAX_ENTRIES_BUFFER.
   */
  appendMessage(entry: TranscriptEntry): void {
    if (!this.config.enabled) {
      this.logger?.warn?.('[TranscriptStorage] appendMessage called but disabled');
      return;
    }

    if (!this.currentFile || !this.currentSession) {
      this.logger?.warn?.('[TranscriptStorage] appendMessage called but no active session');
      return;
    }

    try {
      this.entries.push(entry);

      // v6.36.0: Trim buffer if exceeds limit (keep most recent)
      if (this.entries.length > TranscriptStorage.MAX_ENTRIES_BUFFER) {
        this.entries = this.entries.slice(-TranscriptStorage.MAX_ENTRIES_BUFFER);
        this.logger?.debug?.(`[TranscriptStorage] Trimmed entries buffer to ${TranscriptStorage.MAX_ENTRIES_BUFFER}`);
      }

      // v6.42.0: Check file size before appending
      this.checkFileSizeAndRotate();

      // Append to file
      const formatted = this.formatter.formatMessage(entry);
      fs.appendFileSync(this.currentFile, formatted + '\n', 'utf-8');
      this.logger?.debug?.(`[TranscriptStorage] Appended ${entry.role} message to ${this.currentFile}`);
    } catch (err) {
      this.logger?.error?.(`[TranscriptStorage] appendMessage error: ${err}`);
    }
  }

  /**
   * End the current transcript session.
   * v6.33.0: Optionally generate recap before ending.
   */
  endSession(recapGenerator?: RecapGenerator): Recap | null {
    let recap: Recap | null = null;

    // Generate recap if generator provided and we have entries
    if (recapGenerator && this.currentSession && this.entries.length > 0) {
      try {
        recap = recapGenerator.generateSync(this.currentSession, this.entries);
        this.logger?.info?.(`[TranscriptStorage] Generated recap for session ${this.currentSession}`);
      } catch (err) {
        this.logger?.error?.(`[TranscriptStorage] Recap generation failed: ${err}`);
      }
    }

    this.currentSession = null;
    this.currentFile = null;
    this.currentMetadata = null;
    this.entries = [];

    return recap;
  }

  /**
   * Get current session entries (for recap generation).
   * v6.33.0: Added for recap generation support.
   */
  getEntries(): TranscriptEntry[] {
    return [...this.entries];
  }

  /**
   * Get current session ID.
   * v6.33.0: Added for recap generation support.
   */
  getCurrentSessionId(): string | null {
    return this.currentSession;
  }

  /**
   * Get transcript content by sessionId.
   */
  getTranscript(sessionId: string): string | null {
    if (!this.config.enabled) return null;

    // Search all date directories
    const transcriptsDir = path.join(this.workspace, 'transcripts');
    if (!fs.existsSync(transcriptsDir)) return null;

    const dateDirs = fs.readdirSync(transcriptsDir).sort().reverse();
    for (const dateDir of dateDirs) {
      const filePath = path.join(transcriptsDir, dateDir, `session-${sessionId}.md`);
      if (fs.existsSync(filePath)) {
        return fs.readFileSync(filePath, 'utf-8');
      }
    }

    return null;
  }

  /**
   * Get the file path for a transcript.
   */
  getTranscriptPath(sessionId: string, date?: string): string | null {
    if (!this.config.enabled) return null;

    const transcriptsDir = path.join(this.workspace, 'transcripts');
    if (!fs.existsSync(transcriptsDir)) return null;

    if (date) {
      const filePath = path.join(transcriptsDir, date, `session-${sessionId}.md`);
      return fs.existsSync(filePath) ? filePath : null;
    }

    // Search all date directories
    const dateDirs = fs.readdirSync(transcriptsDir).sort().reverse();
    for (const dir of dateDirs) {
      const filePath = path.join(transcriptsDir, dir, `session-${sessionId}.md`);
      if (fs.existsSync(filePath)) {
        return filePath;
      }
    }

    return null;
  }

  /**
   * Search transcripts by keyword.
   */
  searchTranscripts(query: string, options?: { limit?: number }): TranscriptMatch[] {
    if (!this.config.enabled) return [];

    const limit = options?.limit ?? 10;
    const results: TranscriptMatch[] = [];
    const queryLower = query.toLowerCase();

    const transcriptsDir = path.join(this.workspace, 'transcripts');
    if (!fs.existsSync(transcriptsDir)) return [];

    const dateDirs = fs.readdirSync(transcriptsDir).sort().reverse();
    for (const dateDir of dateDirs) {
      const dirPath = path.join(transcriptsDir, dateDir);
      if (!fs.statSync(dirPath).isDirectory()) continue;

      const files = fs.readdirSync(dirPath).filter((f) => f.endsWith('.md'));
      for (const file of files) {
        const filePath = path.join(dirPath, file);
        const content = fs.readFileSync(filePath, 'utf-8');
        const contentLower = content.toLowerCase();

        if (contentLower.includes(queryLower)) {
          // Extract sessionId from filename
          const match = file.match(/^session-(.+)\.md$/);
          const sessionId = match ? match[1] : file;

          // Find snippet around match
          const idx = contentLower.indexOf(queryLower);
          const snippetStart = Math.max(0, idx - 50);
          const snippetEnd = Math.min(content.length, idx + query.length + 50);
          const snippet = content.slice(snippetStart, snippetEnd);

          // Simple score based on frequency
          const matches = contentLower.split(queryLower).length - 1;
          const score = Math.min(1.0, matches * 0.1 + 0.5);

          results.push({
            sessionId,
            date: dateDir,
            snippet: snippet.trim(),
            score,
          });

          if (results.length >= limit) {
            return results;
          }
        }
      }
    }

    return results;
  }

  /**
   * Clean up expired transcripts.
   */
  cleanupExpired(): number {
    if (!this.config.enabled) return 0;

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - this.config.ttlDays);

    const transcriptsDir = path.join(this.workspace, 'transcripts');
    if (!fs.existsSync(transcriptsDir)) return 0;

    let deletedCount = 0;
    const dateDirs = fs.readdirSync(transcriptsDir);

    for (const dateDir of dateDirs) {
      try {
        const [year, month, day] = dateDir.split('-').map(Number);
        const dirDate = new Date(year, month - 1, day);

        if (dirDate < cutoff) {
          fs.rmSync(path.join(transcriptsDir, dateDir), { recursive: true, force: true });
          deletedCount++;
        }
      } catch {
        // Skip directories that don't match date format
      }
    }

    return deletedCount;
  }

  /**
   * Check if transcript storage is enabled.
   */
  isEnabled(): boolean {
    return this.config.enabled;
  }

  /**
   * Clear the in-memory entries buffer.
   * v6.36.0: Memory leak prevention - call after file write.
   */
  clearBuffer(): void {
    this.entries = [];
    this.logger?.debug?.('[TranscriptStorage] Cleared entries buffer');
  }

  /**
   * Get current buffer size (for monitoring).
   * v6.36.0: Memory monitoring support.
   */
  getBufferSize(): number {
    return this.entries.length;
  }

  /**
   * Flush current entries to file and optionally clear buffer.
   * v6.36.0: Memory leak prevention - periodic flush support.
   */
  flush(clearBuffer: boolean = false): void {
    if (!this.currentFile || this.entries.length === 0) return;

    // Entries are already written to file via appendFileSync in appendMessage
    // This method exists for explicit control
    if (clearBuffer) {
      this.clearBuffer();
    }
    this.logger?.debug?.('[TranscriptStorage] Flush completed');
  }

  // ── v6.42.0 File Size Limit ──────────────────────────────────

  private storageConfig: TranscriptStorageConfig = { ...DEFAULT_TRANSCRIPT_STORAGE_CONFIG };

  private checkFileSizeAndRotate(): void {
    if (!this.currentFile || !this.storageConfig.autoRotate) return;
    try {
      const stats = fs.statSync(this.currentFile);
      const ratio = stats.size / this.storageConfig.maxFileSize;
      if (ratio >= this.storageConfig.warningThreshold) {
        this.logger?.warn?.(`[TranscriptStorage] ${Math.round(ratio*100)}% of limit`);
      }
      if (stats.size >= this.storageConfig.maxFileSize) this.rotateFile();
    } catch { /* file may not exist yet */ }
  }

  private rotateFile(): void {
    if (!this.currentFile) return;
    const oldFile = this.currentFile;
    const newFile = oldFile.replace('.md', `-${Date.now()}.md`);
    fs.renameSync(oldFile, newFile);
    this.logger?.info?.(`[TranscriptStorage] Rotated: ${oldFile} -> ${newFile}`);
    if (this.currentSession && this.currentMetadata) {
      fs.writeFileSync(this.currentFile!, this.formatter.buildHeader(this.currentMetadata), 'utf-8');
    }
  }
}
