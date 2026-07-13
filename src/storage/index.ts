import type { BM25Params } from "../types.js";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

interface MemoryEntry { id: string; content: string; }

const NGRAM_SIZE = 3;

/** Extract all 3-grams from a string. */
function ngrams(text: string): string[] {
  const lower = text.toLowerCase();
  const grams: string[] = [];
  for (let i = 0; i <= lower.length - NGRAM_SIZE; i++) {
    grams.push(lower.slice(i, i + NGRAM_SIZE));
  }
  return [...new Set(grams)];
}

export class InMemoryIndex {
  ngramIndex: Map<string, Set<string>>;
  bm25: BM25Params;
  built: boolean;
  private entries: Map<string, string>;
  private indexDir: string;
  private version: string;
  private enablePersistence: boolean;
  // v6.39.0: Lazy loading
  private _loaded: boolean = false;
  private _indexPath: string | null = null;
  private _pendingMemories: MemoryEntry[] | null = null;

  constructor(workspace: string, ngramSize: number = 3, enablePersistence: boolean = true) {
    this.ngramIndex = new Map();
    this.bm25 = { doc_freq: 0, doc_count: 0, avg_doc_len: 0 };
    this.built = false;
    this.entries = new Map();
    // Store index in workspace for consistency
    this.indexDir = path.join(workspace, ".claw-mem-index");
    this.version = "5.0.0";
    this.enablePersistence = enablePersistence;
    if (enablePersistence) {
      fs.mkdirSync(this.indexDir, { recursive: true });
    }

    // v6.39.0: Don't load immediately — cache path and load on first use
    const jsonPath = path.join(this.indexDir, "index_v5.0.0.json");
    if (fs.existsSync(jsonPath)) {
      this._indexPath = jsonPath;
    }
  }

  /**
   * Load existing JSON index or rebuild from memories.
   * Returns true if loaded from disk, false if rebuilt.
   */
  loadOrBuild(memories: MemoryEntry[]): boolean {
    // v6.39.0: If we already have a cached index path, use lazy loading
    if (this._indexPath) {
      this._pendingMemories = memories;
      return false; // Will be loaded lazily on first search
    }

    const jsonPath = path.join(this.indexDir, "index_v5.0.0.json");
    if (fs.existsSync(jsonPath)) {
      this.loadFromJson(jsonPath);
      if (this.built) return true;
    }

    const oldFiles = fs.existsSync(this.indexDir)
      ? fs.readdirSync(this.indexDir).filter(f => f.startsWith("index_v") && f.endsWith(".pkl.gz") && !f.includes(".migrated"))
      : [];
    if (oldFiles.length > 0) {
      try {
        const { execSync } = require("child_process");
        const cwd = process.cwd();
        execSync("python3 scripts/migrate_index.py", { cwd, stdio: "pipe" });
        if (fs.existsSync(jsonPath)) {
          this.loadFromJson(jsonPath);
          if (this.built) return true;
        }
      } catch { /* Migration failed → build from scratch below */ }
    }

    this.buildFromMemories(memories);
    if (this.enablePersistence) {
      this.saveToJson(jsonPath);
    }
    return false;
  }

  // v6.39.0: Lazy loading — triggered on first search or addMemory
  private _ensureLoaded(): void {
    if (this._loaded) return;

    if (this._indexPath && fs.existsSync(this._indexPath)) {
      this.loadFromJson(this._indexPath);
      this._loaded = true;
      this.built = this.ngramIndex.size > 0;
    } else if (this._pendingMemories) {
      this.buildFromMemories(this._pendingMemories);
      this._pendingMemories = null;
      this._loaded = true;
      this.built = true;
    } else {
      this._loaded = true;
    }
  }

  /** Preload the index eagerly (for warmup). */
  preload(): void {
    this._ensureLoaded();
  }

  /** Add a single memory to the index incrementally. */
  addMemory(content: string, id: string, saveAsync: boolean = true): void {
    this._ensureLoaded();
    this.entries.set(id, content);
    const grams = ngrams(content);
    for (const g of grams) {
      if (!this.ngramIndex.has(g)) {
        this.ngramIndex.set(g, new Set());
      }
      this.ngramIndex.get(g)!.add(id);
    }
    this.bm25.doc_count++;
    this.bm25.doc_freq += grams.length;
    this.bm25.avg_doc_len =
      this.bm25.doc_count > 0
        ? this.bm25.doc_freq / this.bm25.doc_count
        : 0;
    this.built = true;
    if (saveAsync && this.enablePersistence) {
      try {
        this.saveToJson(path.join(this.indexDir, "index_v5.0.0.json"));
      } catch { /* silent — persistence is best-effort */ }
    }
  }

  /** Search by keyword using n-gram intersection. */
  search(query: string, limit: number = 10): string[] {
    this._ensureLoaded();
    if (!this.built) return [];
    const qGrams = ngrams(query);
    const scores = new Map<string, number>();
    for (const g of qGrams) {
      const ids = this.ngramIndex.get(g);
      if (!ids) continue;
      const idf = Math.log((this.bm25.doc_count + 1) / (ids.size + 1)) + 1;
      for (const id of ids) {
        scores.set(id, (scores.get(id) || 0) + idf);
      }
    }
    return [...scores.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([id]) => id);
  }

  // ── persistence ─────────────────────────────────────────────────

  private buildFromMemories(memories: MemoryEntry[]): void {
    this.ngramIndex.clear();
    this.entries.clear();
    let totalGrams = 0;
    for (const mem of memories) {
      if (!mem.content) continue;
      this.entries.set(mem.id, mem.content);
      const grams = ngrams(mem.content);
      totalGrams += grams.length;
      for (const g of grams) {
        if (!this.ngramIndex.has(g)) this.ngramIndex.set(g, new Set());
        this.ngramIndex.get(g)!.add(mem.id);
      }
    }
    const docCount = memories.filter((m) => m.content).length;
    this.bm25 = {
      doc_freq: totalGrams,
      doc_count: docCount,
      avg_doc_len: docCount > 0 ? totalGrams / docCount : 0,
    };
    this.built = true;
  }

  private loadFromJson(filePath: string): void {
    try {
      const raw = fs.readFileSync(filePath, "utf-8");
      const data = JSON.parse(raw);
      if (!data.version || !data.ngram_index || !data.bm25) {
        throw new Error("Index JSON missing required fields");
      }
      if (data.bm25.doc_count < 0 || data.bm25.avg_doc_len < 0) {
        throw new Error("Index BM25 parameters invalid");
      }
      this.ngramIndex = new Map();
      if (data.ngram_index) {
        for (const [k, v] of Object.entries(data.ngram_index)) {
          if (Array.isArray(v)) {
            this.ngramIndex.set(k, new Set(v as string[]));
          }
        }
      }
      this.bm25 = data.bm25;
      this.built = this.ngramIndex.size > 0;
      this.entries.clear();
    } catch {
      try { fs.unlinkSync(filePath); } catch { /* ignore */ }
      this.built = false;
    }
  }

  private saveToJson(filePath: string): void {
    const ngIdx: Record<string, string[]> = {};
    for (const [k, v] of this.ngramIndex.entries()) {
      ngIdx[k] = [...v];
    }
    const data = {
      version: this.version,
      ngram_index: ngIdx,
      bm25: this.bm25,
      timestamp: Date.now(),
    };
    fs.writeFileSync(filePath, JSON.stringify(data), "utf-8");
  }
}
