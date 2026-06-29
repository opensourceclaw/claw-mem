// claw-mem v6.28.0 — Transcript Storage
// Stores complete conversation transcripts for recovery

import * as fs from 'fs';
import * as path from 'path';
import { TranscriptFormatter, type TranscriptEntry, type TranscriptMetadata } from './formatter.js';

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

const DEFAULT_CONFIG: TranscriptConfig = {
  enabled: true,
  ttlDays: 30,
  format: 'markdown',
};

export class TranscriptStorage {
  private workspace: string;
  private config: TranscriptConfig;
  private formatter: TranscriptFormatter;
  private currentSession: string | null = null;
  private currentFile: string | null = null;
  private currentMetadata: TranscriptMetadata | null = null;
  private entries: TranscriptEntry[] = [];

  constructor(workspace: string, config?: Partial<TranscriptConfig>) {
    this.workspace = workspace;
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.formatter = new TranscriptFormatter();

    // Ensure transcripts directory exists
    const transcriptsDir = path.join(workspace, 'transcripts');
    if (!fs.existsSync(transcriptsDir)) {
      fs.mkdirSync(transcriptsDir, { recursive: true });
    }
  }

  /**
   * Start a new transcript session.
   */
  startSession(sessionId: string, channel: string = 'api'): void {
    if (!this.config.enabled) return;

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
  }

  /**
   * Append a message to the current transcript.
   */
  appendMessage(entry: TranscriptEntry): void {
    if (!this.config.enabled || !this.currentFile || !this.currentSession) {
      return;
    }

    this.entries.push(entry);

    // Append to file
    const formatted = this.formatter.formatMessage(entry);
    fs.appendFileSync(this.currentFile, formatted + '\n', 'utf-8');
  }

  /**
   * End the current transcript session.
   */
  endSession(): void {
    this.currentSession = null;
    this.currentFile = null;
    this.currentMetadata = null;
    this.entries = [];
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
}
