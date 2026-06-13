import type { GroundTruthSessionRecord } from "../types.js";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as crypto from "crypto";

/**
 * GroundTruthStore — preserves full raw conversation transcripts.
 *
 * Storage: `ground_truth/session_{id}.json` — one append-only JSON
 * array per session file. Design matches Python GroundTruthStore.
 */
export class GroundTruthStore {
  private baseDir: string;

  constructor(workspace?: string) {
    this.baseDir = path.join(workspace || path.join(os.homedir(), ".claw-mem"), "ground_truth");
    fs.mkdirSync(this.baseDir, { recursive: true });
  }

  /** Store one or more conversation turns. Returns record_id. */
  storeTurn(
    sessionId: string,
    messages: Array<{ role: string; content: string }>,
    metadata?: Record<string, unknown>
  ): string {
    const recordId = `gt_${crypto.randomUUID().replace(/-/g, "").slice(0, 16)}`;
    const record: GroundTruthSessionRecord = {
      record_id: recordId,
      session_id: sessionId,
      messages,
      timestamp: Date.now() / 1000,
      metadata: metadata || {},
    };
    const filePath = this.sessionPath(sessionId);
    const sessionData = this.loadSessionFile(filePath);
    sessionData.push(record);
    this.saveSessionFile(filePath, sessionData);
    return recordId;
  }

  /** Store an entire session at once. */
  storeSession(
    sessionId: string,
    allMessages: Array<{ role: string; content: string }>,
    metadata?: Record<string, unknown>
  ): string {
    return this.storeTurn(sessionId, allMessages, metadata);
  }

  /** Get all records for a session. */
  getSession(sessionId: string): GroundTruthSessionRecord[] {
    return this.loadSessionFile(this.sessionPath(sessionId));
  }

  /** Search raw conversations by session/keyword. */
  search(
    sessionId?: string,
    keyword?: string,
    limit: number = 50
  ): Array<{ session_id: string; message: unknown; timestamp: number }> {
    const results: Array<{ session_id: string; message: unknown; timestamp: number }> = [];
    const kwLower = keyword?.toLowerCase();
    const paths = sessionId
      ? [this.sessionPath(sessionId)]
      : this.listFiles().map((f) => path.join(this.baseDir, f));
    for (const fp of paths) {
      const sid = path.basename(fp).replace("session_", "").replace(".json", "");
      const records = this.loadSessionFile(fp);
      for (const r of records) {
        for (const m of r.messages) {
          if (kwLower && !JSON.stringify(m).toLowerCase().includes(kwLower)) continue;
          results.push({ session_id: sid, message: m, timestamp: r.timestamp });
          if (results.length >= limit) return results;
        }
      }
    }
    return results.slice(0, limit);
  }

  /** List all stored sessions with metadata. */
  listSessions(): Array<{ sessionId: string; fileSize: number; lastModified: number }> {
    const sessions: Array<{ sessionId: string; fileSize: number; lastModified: number }> = [];
    for (const fname of this.listFiles()) {
      const fp = path.join(this.baseDir, fname);
      try {
        const stat = fs.statSync(fp);
        sessions.push({
          sessionId: fname.replace("session_", "").replace(".json", ""),
          fileSize: stat.size,
          lastModified: stat.mtimeMs,
        });
      } catch { continue; }
    }
    sessions.sort((a, b) => b.lastModified - a.lastModified);
    return sessions;
  }

  /** Count total records across all sessions. */
  countRecords(): number {
    let total = 0;
    for (const fname of this.listFiles()) {
      total += this.loadSessionFile(path.join(this.baseDir, fname)).length;
    }
    return total;
  }

  // ── internal ────────────────────────────────────────────────────

  private sessionPath(sessionId: string): string {
    const safeId = sessionId.replace(/[/:]/g, "_");
    return path.join(this.baseDir, `session_${safeId}.json`);
  }

  private listFiles(): string[] {
    try {
      return fs.readdirSync(this.baseDir).filter((f) => f.startsWith("session_") && f.endsWith(".json"));
    } catch { return []; }
  }

  private loadSessionFile(filePath: string): GroundTruthSessionRecord[] {
    if (!fs.existsSync(filePath)) return [];
    try {
      return JSON.parse(fs.readFileSync(filePath, "utf-8")) as GroundTruthSessionRecord[];
    } catch { return []; }
  }

  private saveSessionFile(filePath: string, data: GroundTruthSessionRecord[]): void {
    const tmpPath = filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2), "utf-8");
    fs.renameSync(tmpPath, filePath);
  }
}
