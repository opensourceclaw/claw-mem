/**
 * claw-mem v6.5.0 — DriftHistoryStore
 *
 * Persistent drift history storage for cross-session drift analysis.
 * Records drift events, provides trend analysis, and integrates with
 * DriftAwareRetriever for improved retrieval weighting.
 *
 * v6.5.0: Initial implementation
 */

import * as fs from "fs";
import * as path from "path";

// ── Types ──────────────────────────────────────────────────────────

export interface DriftRecord {
  sessionId: string;
  timestamp: number;
  driftScore: number;
  topicShift: string[];
  alertLevel?: "low" | "medium" | "high";
}

export interface DriftTrend {
  direction: "increasing" | "decreasing" | "stable";
  changeRate: number;
}

export interface DriftHistoryConfig {
  /** Maximum number of records to keep */
  maxRecords: number;
  /** Days to retain records before auto-cleanup */
  retentionDays: number;
  /** File path for persistence */
  storagePath: string;
}

export const DEFAULT_DRIFT_HISTORY_CONFIG: DriftHistoryConfig = {
  maxRecords: 1000,
  retentionDays: 30,
  storagePath: "memory/drift-history.json",
};

export interface DriftSummary {
  totalRecords: number;
  averageDrift: number;
  maxDrift: number;
  minDrift: number;
  recentTrend: DriftTrend;
  sessionCount: number;
  lastRecorded: number | null;
}

// ── DriftHistoryStore ───────────────────────────────────────────────

export class DriftHistoryStore {
  private config: DriftHistoryConfig;
  private records: DriftRecord[] = [];
  private persisted = false;

  constructor(config: Partial<DriftHistoryConfig> = {}) {
    this.config = { ...DEFAULT_DRIFT_HISTORY_CONFIG, ...config };
    this.load();
  }

  // ── CRUD ──────────────────────────────────────────────────────────

  /**
   * Record a drift event.
   */
  record(drift: DriftRecord): void {
    this.records.push({
      ...drift,
      timestamp: drift.timestamp || Date.now(),
    });

    // Enforce max records
    while (this.records.length > this.config.maxRecords) {
      this.records.shift();
    }

    // Cleanup expired records
    this.cleanup();

    this.persist();
  }

  /**
   * Record multiple drift events (batch).
   */
  recordBatch(drifts: DriftRecord[]): void {
    for (const d of drifts) {
      this.records.push({
        ...d,
        timestamp: d.timestamp || Date.now(),
      });
    }

    while (this.records.length > this.config.maxRecords) {
      this.records.shift();
    }

    this.cleanup();
    this.persist();
  }

  /**
   * Get all drift history for a specific session.
   */
  getHistory(sessionId?: string): DriftRecord[] {
    let filtered = this.records;
    if (sessionId) {
      filtered = filtered.filter((r) => r.sessionId === sessionId);
    }
    return [...filtered].sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * Get drift records within a time range.
   */
  getHistoryInRange(startTime: number, endTime: number): DriftRecord[] {
    return this.records
      .filter((r) => r.timestamp >= startTime && r.timestamp <= endTime)
      .sort((a, b) => b.timestamp - a.timestamp);
  }

  // ── Analytics ─────────────────────────────────────────────────────

  /**
   * Get the average drift score across all records.
   */
  getAverageDrift(): number {
    if (this.records.length === 0) return 0;
    const sum = this.records.reduce((s, r) => s + r.driftScore, 0);
    return sum / this.records.length;
  }

  /**
   * Get the average drift score for a specific session.
   */
  getAverageDriftForSession(sessionId: string): number {
    const sessionRecords = this.records.filter((r) => r.sessionId === sessionId);
    if (sessionRecords.length === 0) return 0;
    const sum = sessionRecords.reduce((s, r) => s + r.driftScore, 0);
    return sum / sessionRecords.length;
  }

  /**
   * Get drift trend over recent records.
   * Analyzes the last N records to determine if drift is increasing,
   * decreasing, or stable.
   */
  getDriftTrend(sampleSize: number = 10): DriftTrend {
    const recent = this.records.slice(-sampleSize);
    if (recent.length < 3) {
      return { direction: "stable", changeRate: 0 };
    }

    // Split into first half and second half
    const mid = Math.floor(recent.length / 2);
    const firstHalf = recent.slice(0, mid);
    const secondHalf = recent.slice(mid);

    const firstAvg = firstHalf.reduce((s, r) => s + r.driftScore, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((s, r) => s + r.driftScore, 0) / secondHalf.length;

    // Calculate average time span between records for rate
    let avgTimeDelta = 0;
    if (recent.length > 1) {
      const deltas: number[] = [];
      for (let i = 1; i < recent.length; i++) {
        deltas.push(recent[i].timestamp - recent[i - 1].timestamp);
      }
      avgTimeDelta = deltas.reduce((s, d) => s + d, 0) / deltas.length || 1;
    }

    const changeRate = (secondAvg - firstAvg) / (avgTimeDelta || 1);

    let direction: DriftTrend["direction"];
    if (changeRate > 0.0001) direction = "increasing";
    else if (changeRate < -0.0001) direction = "decreasing";
    else direction = "stable";

    return { direction, changeRate };
  }

  /**
   * Get a comprehensive summary of drift history.
   */
  getSummary(): DriftSummary {
    const scores = this.records.map((r) => r.driftScore);
    const sessions = new Set(this.records.map((r) => r.sessionId));

    return {
      totalRecords: this.records.length,
      averageDrift: scores.length > 0 ? scores.reduce((s, v) => s + v, 0) / scores.length : 0,
      maxDrift: scores.length > 0 ? Math.max(...scores) : 0,
      minDrift: scores.length > 0 ? Math.min(...scores) : 0,
      recentTrend: this.getDriftTrend(),
      sessionCount: sessions.size,
      lastRecorded: this.records.length > 0
        ? this.records[this.records.length - 1].timestamp
        : null,
    };
  }

  /**
   * Check if drift is trending upward (useful for DriftAwareRetriever).
   */
  isDriftIncreasing(threshold: number = 0.7): boolean {
    const trend = this.getDriftTrend();
    return trend.direction === "increasing" && this.getAverageDrift() > threshold;
  }

  // ── Persistence ───────────────────────────────────────────────────

  /**
   * Load records from disk.
   */
  private load(): void {
    try {
      const filePath = this.resolvePath();
      if (fs.existsSync(filePath)) {
        const data = fs.readFileSync(filePath, "utf-8");
        const parsed = JSON.parse(data);
        if (Array.isArray(parsed)) {
          this.records = parsed;
          this.cleanup();
        }
      }
    } catch {
      this.records = [];
    }
  }

  /**
   * Persist records to disk.
   */
  private persist(): void {
    try {
      const filePath = this.resolvePath();
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(filePath, JSON.stringify(this.records, null, 2), "utf-8");
      this.persisted = true;
    } catch {
      // Silently fail on persistence errors
    }
  }

  /**
   * Remove records older than retentionDays.
   */
  private cleanup(): void {
    const cutoff = Date.now() - this.config.retentionDays * 24 * 60 * 60 * 1000;
    const before = this.records.length;
    this.records = this.records.filter((r) => r.timestamp >= cutoff);
    if (this.records.length !== before) {
      this.persist();
    }
  }

  /**
   * Resolve storage path (relative to cwd or absolute).
   */
  private resolvePath(): string {
    if (path.isAbsolute(this.config.storagePath)) {
      return this.config.storagePath;
    }
    return path.resolve(process.cwd(), this.config.storagePath);
  }

  // ── Management ────────────────────────────────────────────────────

  /** Force save to disk */
  save(): void {
    this.persist();
  }

  /** Clear all records */
  clear(): void {
    this.records = [];
    this.persist();
  }

  /** Get total record count */
  get size(): number {
    return this.records.length;
  }

  /** Whether data has been persisted */
  get isPersisted(): boolean {
    return this.persisted;
  }

  /** Update configuration */
  updateConfig(config: Partial<DriftHistoryConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /** Get current configuration */
  getConfig(): DriftHistoryConfig {
    return { ...this.config };
  }
}
