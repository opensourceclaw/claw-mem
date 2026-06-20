import type { EpisodicEntry } from "../types.js";
import * as fs from "fs";
import * as path from "path";

/**
 * Episodic Memory Storage.
 *
 * Storage: `memory/YYYY-MM-DD.md` — one Markdown file per day.
 * Markdown format with HTML comment metadata blocks.
 *
 * Behaviour matches Python EpisodicStorage exactly.
 */
export class EpisodicStorage {
  private memoryDir: string;
  private ttlDays: number;

  constructor(workspace: string, ttlDays: number = 30) {
    // Use workspace directly as memory storage directory
    this.memoryDir = workspace;
    this.ttlDays = ttlDays;
    fs.mkdirSync(this.memoryDir, { recursive: true });
  }

  /** Store a memory record to today's file (atomic write via temp + rename). */
  store(record: Record<string, unknown>): void {
    const today = new Date().toISOString().slice(0, 10);
    const filePath = path.join(this.memoryDir, `${today}.md`);
    const newContent = this.formatMemory(record) + "\n";
    const existing = fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf-8") : "";
    const tmpPath = filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, existing + newContent, "utf-8");
    fs.renameSync(tmpPath, filePath);
  }

  /** Batch store: append multiple records in a single file write. */
  storeBatch(records: Array<Record<string, unknown>>): void {
    if (records.length === 0) return;
    const today = new Date().toISOString().slice(0, 10);
    const filePath = path.join(this.memoryDir, `${today}.md`);
    const existing = fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf-8") : "";
    const newContent = records.map((r) => this.formatMemory(r)).join("\n") + "\n";
    const tmpPath = filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, existing + newContent, "utf-8");
    fs.renameSync(tmpPath, filePath);
  }

  /** Get all episodic memories across all files. */
  getAll(): EpisodicEntry[] {
    return this.readAllFiles();
  }

  /**
   * Get the most recent N entries from the newest date files.
   * Python equivalent: get_recent(limit) — reads newest files, returns up to limit entries.
   */
  getRecent(limit: number = 20): EpisodicEntry[] {
    const files = this.globMdFiles().sort().reverse();
    const memories: EpisodicEntry[] = [];
    for (const fp of files) {
      const filePath = path.join(this.memoryDir, fp);
      const entries = this.readFile(filePath);
      for (let i = entries.length - 1; i >= 0; i--) {
        memories.push(entries[i]);
        if (memories.length >= limit) return memories;
      }
    }
    return memories;
  }

  /** Get entries for a specific date (YYYY-MM-DD). */
  getByDate(date: string): EpisodicEntry[] {
    const filePath = path.join(this.memoryDir, `${date}.md`);
    return this.readFile(filePath);
  }

  /** Clean up files older than ttlDays. Returns count of deleted files. */
  cleanupExpired(): number {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - this.ttlDays);
    let deleted = 0;
    for (const fname of this.globMdFiles()) {
      try {
        const dateStr = fname.replace(".md", "");
        const [y, m, d] = dateStr.split("-").map(Number);
        const fileDate = new Date(y, m - 1, d);
        if (fileDate < cutoff) {
          fs.unlinkSync(path.join(this.memoryDir, fname));
          deleted++;
        }
      } catch { continue; }
    }
    return deleted;
  }

  /** Count total memory records. */
  count(): number {
    let total = 0;
    for (const fname of this.globMdFiles()) {
      total += this.readFile(path.join(this.memoryDir, fname)).length;
    }
    return total;
  }

  // ── format ──────────────────────────────────────────────────────

  private formatMemory(record: Record<string, unknown>): string {
    const timestamp = record.timestamp || new Date().toISOString();
    const content = record.content || "";
    const tags = (record.tags as string[]) || [];
    const metadata = (record.metadata as Record<string, unknown>) || {};
    const sessionId = record.session_id as string | undefined;
    const meta: string[] = [];
    if (tags.length) meta.push(`tags: ${tags.join(", ")}`);
    if (sessionId) meta.push(`session: ${sessionId}`);
    for (const [k, v] of Object.entries(metadata)) {
      meta.push(`${k}: ${v}`);
    }
    let lines = "";
    if (meta.length) lines += `<!-- ${meta.join("; ")} -->\n`;
    lines += `[${timestamp}] ${content}`;
    return lines;
  }

  // ── file IO ─────────────────────────────────────────────────────

  private globMdFiles(): string[] {
    try {
      return fs.readdirSync(this.memoryDir).filter((f) => f.endsWith(".md"));
    } catch { return []; }
  }

  private readAllFiles(): EpisodicEntry[] {
    const memories: EpisodicEntry[] = [];
    for (const fname of this.globMdFiles().sort().reverse()) {
      memories.push(...this.readFile(path.join(this.memoryDir, fname)));
    }
    return memories;
  }

  private readFile(filePath: string): EpisodicEntry[] {
    if (!fs.existsSync(filePath)) return [];
    const entries: EpisodicEntry[] = [];
    let currentMeta: Record<string, string> = {};
    try {
      const lines = fs.readFileSync(filePath, "utf-8").split("\n");
      for (const raw of lines) {
        const line = raw.trim();
        if (!line) continue;
        if (line.startsWith("<!--") && line.endsWith("-->")) {
          const metaContent = line.slice(4, -3).trim();
          for (const item of metaContent.split(";")) {
            const trimmed = item.trim();
            const idx = trimmed.indexOf(":");
            if (idx !== -1) {
              const key = trimmed.slice(0, idx).trim();
              const val = trimmed.slice(idx + 1).trim();
              currentMeta[key] = val;
            }
          }
          continue;
        }
        if (line.startsWith("[")) {
          const endIdx = line.indexOf("]");
          if (endIdx !== -1) {
            const timestamp = line.slice(1, endIdx);
            const content = line.slice(endIdx + 1).trim();
            const sessionId = currentMeta["session"];
            const tagsStr = currentMeta["tags"] || "";
            const tags = tagsStr ? tagsStr.split(", ").filter(Boolean) : [];
            const metadata: Record<string, string> = {};
            for (const [k, v] of Object.entries(currentMeta)) {
              if (k !== "tags" && k !== "session") metadata[k] = v;
            }
            entries.push({
              timestamp,
              content,
              tags,
              session_id: sessionId,
              id: metadata["id"] || undefined,
              metadata,
              type: "episodic",
              source: filePath,
            });
            currentMeta = {};
          }
        }
      }
    } catch { /* file read error → empty */ }
    return entries;
  }
}
