import type { SemanticEntry } from "../types.js";
import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

/**
 * Semantic Memory Storage.
 *
 * Storage: `MEMORY.md` — single permanent Markdown file.
 * No expiry. Supports in-place update via rewrite.
 *
 * Behaviour matches Python SemanticStorage exactly.
 */
export class SemanticStorage {
  private filePath: string;

  constructor(workspace: string) {
    this.filePath = path.join(workspace, "MEMORY.md");
    if (!fs.existsSync(this.filePath)) {
      this.initializeFile();
    }
  }

  /** Store a memory record to MEMORY.md (atomic write via temp + rename). */
  store(record: Record<string, unknown>): void {
    const newContent = this.formatMemory(record) + "\n";
    const existing = fs.existsSync(this.filePath) ? fs.readFileSync(this.filePath, "utf-8") : "";
    const tmpPath = this.filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, existing + newContent, "utf-8");
    fs.renameSync(tmpPath, this.filePath);
  }

  /** Get all semantic memories. */
  getAll(): SemanticEntry[] {
    return this.readFile();
  }

  /** Search memories by tag. */
  searchByTag(tag: string): SemanticEntry[] {
    return this.getAll().filter((m) => m.tags.includes(tag));
  }

  /** Update memory content by ID. Rewrites the whole file. */
  update(memoryId: string, newContent: string): boolean {
    const memories = this.getAll();
    for (let i = 0; i < memories.length; i++) {
      if (memories[i].id === memoryId) {
        memories[i].content = newContent;
        memories[i].metadata = {
          ...memories[i].metadata,
          updated_at: new Date().toISOString(),
        };
        this.rewriteFile(memories);
        return true;
      }
    }
    return false;
  }

  /**
   * v7.6.0 (ADR-003): full-record update by ID — content and/or tags and/or
   * metadata (merge), stamps updated_at. Used by the error-pattern-card
   * strategy whose structured face lives in metadata (content-only `update`
   * would drop it). Rewrites the whole file.
   */
  updateRecord(
    memoryId: string,
    changes: { content?: string; tags?: string[]; metadata?: Record<string, string> },
  ): boolean {
    const memories = this.getAll();
    for (let i = 0; i < memories.length; i++) {
      if (memories[i].id === memoryId) {
        if (changes.content !== undefined) memories[i].content = changes.content;
        if (changes.tags !== undefined) memories[i].tags = changes.tags;
        if (changes.metadata !== undefined) {
          memories[i].metadata = { ...memories[i].metadata, ...changes.metadata };
        }
        memories[i].metadata = {
          ...memories[i].metadata,
          updated_at: new Date().toISOString(),
        };
        this.rewriteFile(memories);
        return true;
      }
    }
    return false;
  }

  /** Count memories. */
  count(): number {
    return this.getAll().length;
  }

  // ── format ──────────────────────────────────────────────────────

  private formatMemory(record: Record<string, unknown>): string {
    const timestamp = record.timestamp || new Date().toISOString();
    const content = record.content || "";
    const tags = (record.tags as string[]) || [];
    const memoryId = (record.id as string) || this.generateId();
    const metadata = (record.metadata as Record<string, unknown>) || {};
    const meta: string[] = [];
    if (tags.length) meta.push(`tags: ${tags.join(", ")}`);
    if (memoryId) meta.push(`id: ${memoryId}`);
    for (const [k, v] of Object.entries(metadata)) {
      meta.push(`${k}: ${v}`);
    }
    // v6.27.2: Timestamp moved to trailing HTML comment for cache stability
    return `<!-- ${meta.join("; ")} -->\n${content} <!-- ts:${timestamp} -->\n`;
  }

  private generateId(): string {
    return crypto.randomUUID().slice(0, 8);
  }

  // ── file IO ─────────────────────────────────────────────────────

  private initializeFile(): void {
    const header = "# MEMORY.md\n\n<!-- Core Memory - Permanent Storage -->\n\n";
    fs.writeFileSync(this.filePath, header, "utf-8");
  }

  private readFile(): SemanticEntry[] {
    if (!fs.existsSync(this.filePath)) return [];
    const entries: SemanticEntry[] = [];
    let currentMeta: Record<string, string> = {};
    try {
      const lines = fs.readFileSync(this.filePath, "utf-8").split("\n");
      for (const raw of lines) {
        const line = raw.trim();
        if (!line || line.startsWith("#")) continue;
        if (line.startsWith("<!--") && line.endsWith("-->")) {
          const metaContent = line.slice(4, -3).trim();
          const delimiter = metaContent.includes("; ") ? "; " : ";";
          for (const item of metaContent.split(delimiter)) {
            const trimmed = item.trim();
            const idx = trimmed.indexOf(":");
            if (idx !== -1) {
              currentMeta[trimmed.slice(0, idx).trim()] = trimmed.slice(idx + 1).trim();
            }
          }
          continue;
        }
        // v6.27.2: Support both old and new timestamp formats
        let timestamp = "";
        let content = "";

        // Try new format first: content <!-- ts:TIMESTAMP -->
        const tsMatch = line.match(/^(.+?)\s*<!-- ts:([^>]+) -->$/);
        if (tsMatch) {
          content = tsMatch[1].trim();
          timestamp = tsMatch[2];
        } else if (line.startsWith("[")) {
          // Fallback to old format: [TIMESTAMP] content
          const endIdx = line.indexOf("]");
          if (endIdx !== -1) {
            timestamp = line.slice(1, endIdx);
            content = line.slice(endIdx + 1).trim();
          }
        }

        if (timestamp || content) {
          const memoryId = currentMeta["id"];
          const tagsStr = currentMeta["tags"] || "";
          const tags = tagsStr ? tagsStr.split(", ").filter(Boolean) : [];
          const metadata: Record<string, string> = {};
          for (const [k, v] of Object.entries(currentMeta)) {
            if (k !== "tags" && k !== "id") metadata[k] = v;
          }
          entries.push({
            id: memoryId,
            timestamp,
            content,
            tags,
            metadata,
            type: "semantic",
            source: this.filePath,
          });
          currentMeta = {};
        }
      }
    } catch { /* read error → empty */ }
    return entries;
  }

  private rewriteFile(memories: SemanticEntry[]): void {
    let content = "# MEMORY.md\n\n<!-- Core Memory - Permanent Storage -->\n\n";
    for (const m of memories) {
      const meta: string[] = [];
      if (m.tags.length) meta.push(`tags: ${m.tags.join(", ")}`);
      if (m.id) meta.push(`id: ${m.id}`);
      for (const [k, v] of Object.entries(m.metadata)) {
        meta.push(`${k}: ${v}`);
      }
      // v6.27.2: New format with trailing timestamp
      content += `<!-- ${meta.join("; ")} -->\n${m.content} <!-- ts:${m.timestamp} -->\n\n`;
    }
    const tmpPath = this.filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, content, "utf-8");
    fs.renameSync(tmpPath, this.filePath);
  }
}
