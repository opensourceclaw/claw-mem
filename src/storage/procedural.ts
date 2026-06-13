import type { ProceduralEntry } from "../types.js";
import * as fs from "fs";
import * as path from "path";

/**
 * Procedural Memory Storage.
 *
 * Storage: `memory/skills/*.md` — one Markdown file per skill.
 * No expiry. Skill name extracted from tags or defaults to "general".
 *
 * Behaviour matches Python ProceduralStorage exactly.
 */
export class ProceduralStorage {
  private skillsDir: string;

  constructor(workspace: string) {
    this.skillsDir = path.join(workspace, "memory", "skills");
    fs.mkdirSync(this.skillsDir, { recursive: true });
  }

  /** Store a procedural memory record (atomic write via temp + rename). */
  store(record: Record<string, unknown>): void {
    const skillName = this.extractSkillName(record);
    const filePath = this.skillsPath(skillName);
    const newContent = this.formatMemory(record) + "\n";
    const existing = fs.existsSync(filePath) ? fs.readFileSync(filePath, "utf-8") : "";
    const tmpPath = filePath + ".tmp." + Date.now();
    fs.writeFileSync(tmpPath, existing + newContent, "utf-8");
    fs.renameSync(tmpPath, filePath);
  }

  /** Get memories for a specific skill. */
  getSkill(skillName: string): ProceduralEntry[] {
    const filePath = this.skillsPath(skillName);
    return this.readFile(filePath);
  }

  /** Get all procedural memories across all skill files. */
  getAll(): ProceduralEntry[] {
    const memories: ProceduralEntry[] = [];
    for (const fname of this.globMdFiles()) {
      memories.push(...this.readFile(this.skillsPath(fname.replace(".md", ""))));
    }
    return memories;
  }

  /** Search skill memories by keyword in content. */
  searchByKeyword(keyword: string): ProceduralEntry[] {
    const results: ProceduralEntry[] = [];
    const kw = keyword.toLowerCase();
    for (const fname of this.globMdFiles()) {
      const entries = this.readFile(this.skillsPath(fname.replace(".md", "")));
      for (const e of entries) {
        if (e.content.toLowerCase().includes(kw)) {
          results.push(e);
        }
      }
    }
    return results;
  }

  /** Count total procedural records. */
  count(): number {
    let total = 0;
    for (const fname of this.globMdFiles()) {
      total += this.readFile(this.skillsPath(fname.replace(".md", ""))).length;
    }
    return total;
  }

  // ── helpers ─────────────────────────────────────────────────────

  private skillsPath(skillName: string): string {
    return path.join(this.skillsDir, `${skillName}.md`);
  }

  private extractSkillName(record: Record<string, unknown>): string {
    const tags = (record.tags as string[]) || [];
    for (const tag of tags) {
      if (tag !== "procedural" && tag !== "skill") {
        return this.sanitizeFilename(tag);
      }
    }
    return "general";
  }

  private sanitizeFilename(name: string): string {
    return name.replace(/[<>:"/\\|?*]/g, "_").toLowerCase().trim();
  }

  // ── format ──────────────────────────────────────────────────────

  private formatMemory(record: Record<string, unknown>): string {
    const timestamp = record.timestamp || new Date().toISOString();
    const content = record.content || "";
    const tags = (record.tags as string[]) || [];
    const metadata = (record.metadata as Record<string, unknown>) || {};
    const meta: string[] = [];
    if (tags.length) meta.push(`tags: ${tags.join(", ")}`);
    for (const [k, v] of Object.entries(metadata)) {
      meta.push(`${k}: ${v}`);
    }
    let lines = "";
    if (meta.length) lines += `<!-- ${meta.join("; ")} -->\n`;
    lines += `[${timestamp}] ${content}\n`;
    return lines;
  }

  // ── file IO ─────────────────────────────────────────────────────

  private globMdFiles(): string[] {
    try {
      return fs.readdirSync(this.skillsDir).filter((f) => f.endsWith(".md"));
    } catch { return []; }
  }

  private readFile(filePath: string): ProceduralEntry[] {
    if (!fs.existsSync(filePath)) return [];
    const entries: ProceduralEntry[] = [];
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
              currentMeta[trimmed.slice(0, idx).trim()] = trimmed.slice(idx + 1).trim();
            }
          }
          continue;
        }
        if (line.startsWith("[")) {
          const endIdx = line.indexOf("]");
          if (endIdx !== -1) {
            const timestamp = line.slice(1, endIdx);
            const content = line.slice(endIdx + 1).trim();
            const tagsStr = currentMeta["tags"] || "";
            const tags = tagsStr ? tagsStr.split(", ").filter(Boolean) : [];
            const metadata: Record<string, string> = {};
            for (const [k, v] of Object.entries(currentMeta)) {
              if (k !== "tags") metadata[k] = v;
            }
            entries.push({
              timestamp, content, tags, metadata,
              type: "procedural",
              source: filePath,
            });
            currentMeta = {};
          }
        }
      }
    } catch { /* read error → empty */ }
    return entries;
  }
}
