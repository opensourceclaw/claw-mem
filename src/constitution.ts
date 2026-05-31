// Copyright 2026 Peter Cheng — Licensed Apache-2.0
// claw-mem v5.1.0 — ConstitutionStore (TypeScript)
//
// Three-layer persistent identity store, immune to decay and compression.
// L0 = file-system sources (AGENTS.md, IDENTITY.md, etc.)
// L1 = auto-detected rules via scan_and_suggest
// L2 = direct RPC storage

import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";

// ── Types ──────────────────────────────────────────────────────────

export interface ConstitutionEntry {
  id: string;
  layer: 0 | 1 | 2;
  source: string;
  content: string;
  createdAt: string;
  tags: string[];
}

export interface Suggestion {
  content: string;
  source: string;
  confidence: number;
  reason: string;
  sourceMessage: string;
}

// ── Constants ──────────────────────────────────────────────────────

const L0_FILES = ["AGENTS.md", "IDENTITY.md", "MEMORY.md", "TOOLS.md", "USER.md"];
const L1_STORAGE_DIR = ".claw-mem/constitution";

// ── L1 scan patterns ───────────────────────────────────────────────

const SCAN_PATTERNS: Array<{
  name: string;
  regex: RegExp;
  confidence: number;
  reason: string;
}> = [
  { name: "tech_stack", regex: /use\s+(TypeScript|Python|Rust|Go|JavaScript|Java|C\+\+|Ruby|Kotlin|Swift)\b/gi, confidence: 0.95, reason: "Tech stack mentioned with commitment language" },
  { name: "protocol", regex: /communication\s+(protocol|method|via)\s+(\w[\w\s]*)/gi, confidence: 0.90, reason: "Communication protocol specified" },
  { name: "role", regex: /(\w[\w\s]+?)\s+(is responsible for|role is|job is to)\s+/gi, confidence: 0.90, reason: "Role definition detected" },
  { name: "rule", regex: /(always use|never use|must always|do not use)\s+/gi, confidence: 0.85, reason: "Rule pattern detected" },
  { name: "decision", regex: /(let'?s?\s+(use|go with|stick with)|we'?ll?\s+(use|go with)|decided to)\s+/gi, confidence: 0.85, reason: "Team decision pattern" },
];

// ── Helpers ────────────────────────────────────────────────────────

function uid(): string {
  return crypto.randomUUID().slice(0, 8);
}

function now(): string {
  return new Date().toISOString();
}

// ── ConstitutionStore ──────────────────────────────────────────────

export class ConstitutionStore {
  private workspace: string;
  private storageDir: string;

  constructor(workspace: string) {
    this.workspace = workspace;
    this.storageDir = path.join(workspace, L1_STORAGE_DIR);
    fs.mkdirSync(this.storageDir, { recursive: true });
  }

  // ── L0: file-system sources ─────────────────────────────────────

  private loadL0(): ConstitutionEntry[] {
    const entries: ConstitutionEntry[] = [];
    for (const filename of L0_FILES) {
      const filePath = path.join(this.workspace, filename);
      if (!fs.existsSync(filePath)) continue;
      try {
        const text = fs.readFileSync(filePath, "utf-8");
        const lines = text.split("\n").map(l => l.trim()).filter(l =>
          l.length > 10 && !l.startsWith("#") && !l.startsWith("```") && !l.startsWith("<!--")
        );
        for (const line of lines) {
          entries.push({
            id: `l0_${filename.replace(".md","")}_${uid()}`,
            layer: 0, source: filename,
            content: line.slice(0, 500), createdAt: now(), tags: [`l0_${filename.replace(".md","")}`],
          });
        }
      } catch { /* skip unreadable files */ }
    }
    return entries;
  }

  // ── L1/L2: JSON persistence ─────────────────────────────────────

  private loadL1L2(): ConstitutionEntry[] {
    const entries: ConstitutionEntry[] = [];
    if (!fs.existsSync(this.storageDir)) return entries;
    for (const fname of fs.readdirSync(this.storageDir)) {
      if (!fname.endsWith(".json")) continue;
      try {
        const data = JSON.parse(fs.readFileSync(path.join(this.storageDir, fname), "utf-8"));
        if (data && data.id && typeof data.layer === "number") {
          entries.push(data as ConstitutionEntry);
        }
      } catch { /* skip corrupt files */ }
    }
    return entries;
  }

  private saveL1L2(entry: ConstitutionEntry): void {
    const fp = path.join(this.storageDir, `${entry.id}.json`);
    const tmp = fp + ".tmp." + Date.now();
    fs.writeFileSync(tmp, JSON.stringify(entry, null, 2), "utf-8");
    fs.renameSync(tmp, fp);
  }

  // ── Public API ──────────────────────────────────────────────────

  /** Assemble all entries: L0 + L1 + L2, sorted by layer then creation time. */
  assemble(): ConstitutionEntry[] {
    const l0 = this.loadL0();
    const l1l2 = this.loadL1L2();
    return [...l0, ...l1l2].sort((a, b) => a.layer - b.layer || a.createdAt.localeCompare(b.createdAt));
  }

  /** Assemble as formatted text block for prompt injection. */
  assembleText(): string {
    const entries = this.assemble();
    if (!entries.length) return "";
    let text = "## Constitution (Immutable Identity)\n";
    text += "The following are fundamental truths about this workspace:\n\n";
    for (const e of entries) {
      const prefix = { 0: "[CORE]", 1: "[RULE]", 2: "[ANCHOR]" }[e.layer];
      text += `- ${prefix}: ${e.content}\n`;
    }
    return text;
  }

  /** Scan conversations for L1 rule candidates. */
  scanAndSuggest(conversations: Array<{ content: string }>): Suggestion[] {
    const suggestions: Suggestion[] = [];
    const seen = new Set<string>();

    for (const msg of conversations) {
      const text = msg.content || "";
      if (!text) continue;
      for (const pattern of SCAN_PATTERNS) {
        pattern.regex.lastIndex = 0; // reset global regex
        const match = pattern.regex.exec(text);
        if (match && !seen.has(match[0])) {
          seen.add(match[0]);
          suggestions.push({
            content: `[${pattern.name}] ${match[0].trim()}`,
            source: "auto_detect",
            confidence: pattern.confidence,
            reason: pattern.reason,
            sourceMessage: text.slice(0, 200),
          });
        }
      }
    }
    return suggestions;
  }

  /** Promote content to L1 (auto-detected, pending human approval). */
  promoteToL1(content: string, source = "auto_detect"): string | null {
    try {
      const entry: ConstitutionEntry = {
        id: `l1_${uid()}`, layer: 1, source, content,
        createdAt: now(), tags: ["l1_auto_detected"],
      };
      this.saveL1L2(entry);
      return entry.id;
    } catch { return null; }
  }

  /** Promote content to L2 (operator-validated via bridge RPC). */
  promoteToL2(content: string, tags: string[] = [],
               metadata: Record<string, string> = {}): string | null {
    try {
      const entry: ConstitutionEntry = {
        id: `l2_${uid()}`, layer: 2,
        source: metadata._migrated_from || (tags.includes("migrated_v5.1") ? "migration" : "rpc"),
        content, createdAt: now(), tags: [...tags, "constitution_l2"],
      };
      this.saveL1L2(entry);
      return entry.id;
    } catch { return null; }
  }

  /** Delete an L1 or L2 entry (L0 is immutable via API). */
  delete(entryId: string): boolean {
    const fp = path.join(this.storageDir, `${entryId}.json`);
    if (fs.existsSync(fp)) {
      fs.unlinkSync(fp);
      return true;
    }
    return false;
  }

  getAll(): ConstitutionEntry[] {
    return this.assemble();
  }

  getStats(): Record<string, unknown> {
    const all = this.assemble();
    const byLayer: Record<number, number> = { 0: 0, 1: 0, 2: 0 };
    for (const e of all) byLayer[e.layer] = (byLayer[e.layer] || 0) + 1;
    return { totalEntries: all.length, byLayer };
  }
}
