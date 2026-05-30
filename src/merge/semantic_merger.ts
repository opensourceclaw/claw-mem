// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * SemanticMergeScheduler (F1 - v4.7.0)
 *
 * Detects semantically similar memories, merges them via LLM generation,
 * and marks source memories as deprecated.
 */
import * as fs from "fs";
// ── External type stubs ────────────────────────────────────────────────

interface StorageBackend {
  filePath: string;
  getAll(): Record<string, unknown>[];
  _formatMemory(mem: Record<string, unknown>): string;
}

interface LLMProvider {
  generate(prompt: string, options?: { maxTokens?: number; system?: string }): string;
}

interface EmbeddingService {
  encode(texts: string[]): number[][];
}

interface MemoryManager {
  semantic: StorageBackend;
  store(
    content: string,
    memoryType: string,
    tags?: string[],
    metadata?: Record<string, string>,
    updateIndex?: boolean,
  ): void;
}

// ── Prompts ────────────────────────────────────────────────────────────

const MERGE_PROMPT_TEMPLATE =
  "You are a memory consolidation assistant. " +
  "Merge the following related memories into one concise, " +
  "factual statement. Preserve all unique information.\n\n" +
  "Memory A: {mem_a}\n\n" +
  "Memory B: {mem_b}\n\n" +
  "Merged memory:";

// ── Utility ────────────────────────────────────────────────────────────

/** Cosine similarity between two vectors (pure JS, no numpy). */
export function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  normA = Math.sqrt(normA);
  normB = Math.sqrt(normB);
  if (normA === 0 || normB === 0) return 0;
  return dot / (normA * normB);
}

// ── Scheduler ──────────────────────────────────────────────────────────

export class SemanticMergeScheduler {
  private _lastMergeAt: number = 0;
  private _mergeCount: number = 0;

  constructor(
    private _manager: MemoryManager,
    private _llmProvider: LLMProvider,
    private _embeddingService?: EmbeddingService,
    public mergeInterval: number = 100,
    public mergeCheck: string = "auto",
    public highSimThreshold: number = 0.85,
    public medSimThreshold: number = 0.65,
  ) {}

  /** Lazy-load EmbeddingService if not injected. */
  private get embeddingService(): EmbeddingService {
    if (!this._embeddingService) {
      // In a full implementation this would create a real EmbeddingService
      throw new Error("EmbeddingService not configured");
    }
    return this._embeddingService;
  }

  // ── lifecycle ────────────────────────────────────────────────────────

  /** Return True if enough interactions have passed since last merge. */
  shouldRun(interactionCount: number): boolean {
    if (interactionCount < this.mergeInterval) return false;
    return interactionCount % this.mergeInterval === 0;
  }

  // ── candidate detection ──────────────────────────────────────────────

  /** Find semantic memory pairs above the medium similarity threshold. */
  findMergeCandidates(): Array<{ id1: string; id2: string; similarity: number }> {
    const storage = this._manager.semantic;
    const allMemories = storage.getAll();

    // Filter out deprecated memories and those without IDs
    const active: Record<string, unknown>[] = [];
    for (const m of allMemories) {
      const meta = (m.metadata as Record<string, string>) || {};
      if (meta.deprecated === "true" || meta.deprecated === "True" || meta.deprecated === "1") {
        continue;
      }
      const mid = m.id as string | undefined;
      if (!mid) continue;
      const content = (m.content as string) || "";
      if (!content || !content.trim()) continue;
      active.push(m);
    }

    const n = active.length;
    if (n < 2) return [];

    // Compute embeddings for all active memories
    const texts = active.map((m) => m.content as string);
    const embeddings = this.embeddingService.encode(texts);

    // Pairwise similarity
    const candidates: Array<{ id1: string; id2: string; similarity: number }> = [];
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const sim = cosineSimilarity(embeddings[i], embeddings[j]);
        if (sim >= this.medSimThreshold) {
          candidates.push({
            id1: active[i].id as string,
            id2: active[j].id as string,
            similarity: sim,
          });
        }
      }
    }

    candidates.sort((a, b) => b.similarity - a.similarity);
    return candidates;
  }

  // ── merge single pair ────────────────────────────────────────────────

  /** Merge two memory records into one using LLM generation. */
  mergePair(
    mem1: Record<string, unknown>,
    mem2: Record<string, unknown>,
    similarity: number,
  ): Record<string, unknown> | null {
    const contentA = (mem1.content as string) || "";
    const contentB = (mem2.content as string) || "";
    if (!contentA || !contentB) return null;

    // Build prompt
    const prompt = MERGE_PROMPT_TEMPLATE.replace("{mem_a}", contentA).replace(
      "{mem_b}",
      contentB,
    );

    // Generate merged text via LLM
    const mergedText = this._llmProvider.generate(prompt, {
      maxTokens: 256,
      system: "",
    });
    if (!mergedText) return null;

    // Collect tags from both sources
    const tags = [
      ...new Set([
        ...((mem1.tags as string[]) || []),
        ...((mem2.tags as string[]) || []),
      ]),
    ];

    // Merge metadata (excluding internal keys)
    const mergedMeta: Record<string, string> = { ...(mem1.metadata as Record<string, string>) || {} };
    for (const [key, val] of Object.entries(
      (mem2.metadata as Record<string, string>) || {},
    )) {
      mergedMeta[key] = String(val);
    }
    mergedMeta.merged_from = `${mem1.id ?? "?"},${mem2.id ?? "?"}`;
    mergedMeta.merge_similarity = similarity.toFixed(4);

    // Store the merged memory
    try {
      this._manager.store(mergedText, "semantic", tags, mergedMeta, true);
    } catch {
      return null;
    }

    // Mark source memories as deprecated
    this._markDeprecated([(mem1.id as string) || "", (mem2.id as string) || ""]);

    this._mergeCount++;
    return { content: mergedText, tags, metadata: mergedMeta };
  }

  private _markDeprecated(memoryIds: string[]): void {
    const validIds = new Set(memoryIds.filter(Boolean));
    if (validIds.size === 0) return;

    const storage = this._manager.semantic;
    const allMemories = storage.getAll();
    for (const mem of allMemories) {
      if (validIds.has(mem.id as string)) {
        const meta = (mem.metadata as Record<string, string>) || {};
        meta.deprecated = "true";
        mem.metadata = meta;
      }
    }

    this._rewriteSemanticFile(storage, allMemories);
  }

  private _rewriteSemanticFile(
    storage: StorageBackend,
    memories: Record<string, unknown>[],
  ): void {

    const lines: string[] = [];
    lines.push("# MEMORY.md\n");
    lines.push("<!-- Core Memory - Permanent Storage -->\n");
    for (const mem of memories) {
      lines.push(storage._formatMemory(mem));
    }
    fs.writeFileSync(storage.filePath, lines.join("\n"), "utf-8");
  }

  // ── full cycle ───────────────────────────────────────────────────────

  /** Run a complete merge cycle. Returns stats dict. */
  runMergeCycle(): Record<string, unknown> {
    const t0 = Date.now();
    const stats: Record<string, unknown> = {
      mergedCount: 0,
      skippedCount: 0,
      errors: 0,
      candidatesFound: 0,
    };

    // Find candidates
    const candidates = this.findMergeCandidates();
    stats.candidatesFound = candidates.length;

    // Track already-merged IDs to avoid re-merging
    const processed = new Set<string>();

    for (const { id1, id2, similarity } of candidates) {
      if (processed.has(id1) || processed.has(id2)) {
        stats.skippedCount = (stats.skippedCount as number) + 1;
        continue;
      }

      // Look up memory records
      const storage = this._manager.semantic;
      const allM = storage.getAll();
      const mem1 = allM.find((m) => (m.id as string) === id1);
      const mem2 = allM.find((m) => (m.id as string) === id2);
      if (!mem1 || !mem2) {
        stats.skippedCount = (stats.skippedCount as number) + 1;
        continue;
      }

      // Adjust merge strategy based on similarity
      try {
        const result = this.mergePair(mem1, mem2, similarity);
        if (result !== null) {
          stats.mergedCount = (stats.mergedCount as number) + 1;
          processed.add(id1);
          processed.add(id2);
        } else {
          stats.skippedCount = (stats.skippedCount as number) + 1;
        }
      } catch {
        stats.errors = (stats.errors as number) + 1;
      }
    }

    stats.pairsProcessed = (stats.mergedCount as number) + (stats.skippedCount as number);
    stats.durationMs = Math.round(Date.now() - t0);
    this._lastMergeAt = Date.now() / 1000;
    return stats;
  }

  toString(): string {
    return `SemanticMergeScheduler(interval=${this.mergeInterval}, merged=${this._mergeCount})`;
  }
}
