// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * ConflictDetector (F3 - v4.7.0)
 *
 * Detects contradictory or inconsistent semantic memories and resolves them
 * by keeping the higher-confidence version with optional LLM arbitration.
 */

import { cosineSimilarity } from "./semantic_merger.js";

// ── External type stubs ────────────────────────────────────────────────

interface StorageBackend {
  getAll(): Record<string, unknown>[];
}

interface LLMProvider {
  generate(prompt: string, options?: { maxTokens?: number; system?: string }): string;
}

interface EmbeddingService {
  encode(texts: string[]): number[][];
}

interface MemoryManager {
  semantic: StorageBackend;
}

// ── Data types ─────────────────────────────────────────────────────────

export interface ConflictReport {
  conflictType: string; // "entity" | "timeline" | "semantic"
  memoryIdA: string;
  memoryIdB: string;
  contentA: string;
  contentB: string;
  description: string;
  similarity: number;
  resolved: boolean;
  resolution: ConflictResolution | null;
}

export function conflictReportToDict(r: ConflictReport): Record<string, unknown> {
  return {
    conflict_type: r.conflictType,
    memory_id_a: r.memoryIdA,
    memory_id_b: r.memoryIdB,
    content_a: r.contentA,
    content_b: r.contentB,
    description: r.description,
    similarity: r.similarity,
    resolved: r.resolved,
    resolution: r.resolution ? conflictResolutionToDict(r.resolution) : null,
  };
}

export interface ConflictResolution {
  action: string; // "keep_a" | "keep_b" | "merge" | "manual"
  winnerId: string;
  mergedContent: string;
  reasoning: string;
}

export function conflictResolutionToDict(r: ConflictResolution): Record<string, unknown> {
  return {
    action: r.action,
    winner_id: r.winnerId,
    merged_content: r.mergedContent,
    reasoning: r.reasoning,
  };
}

// ── LLM prompts ────────────────────────────────────────────────────────

const CONFLICT_CHECK_PROMPT =
  "Are these two statements contradictory or inconsistent? " +
  "Answer YES or NO, then explain briefly.\n\n" +
  "Statement A: {a}\nStatement B: {b}";

const CONFLICT_RESOLVE_PROMPT =
  "Choose the correct version from two conflicting memories. " +
  "Pick the one that is more specific, more recent, or more authoritative. " +
  "Reply with 'A', 'B', or 'MERGE'. If MERGE, provide the merged text.\n\n" +
  "Memory A: {a}\nMemory B: {b}\n\nAnswer:";

// ── entity extraction helpers ──────────────────────────────────────────

/** Extract candidate entity names from text using simple heuristics. */
function extractEntities(text: string): string[] {
  const entities: string[] = [];
  const patterns: RegExp[] = [
    /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g,
    /@(\w+)/g,
    /(?:city|country|company|person|project)\s*[:=]\s*(\S+)/gi,
  ];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null;
    while ((match = pattern.exec(text)) !== null) {
      const name = match[1].trim().toLowerCase();
      if (name.length >= 2 && !entities.includes(name)) {
        entities.push(name);
      }
    }
  }
  return entities;
}

/** Extract attribute key-value pairs (e.g., "age: 30", "location: Beijing"). */
function extractAttributes(text: string): Record<string, string> {
  const attrPattern = /(\w+)\s*[:=]\s*([^,;.\n]+)/gi;
  const attrs: Record<string, string> = {};
  let match: RegExpExecArray | null;
  while ((match = attrPattern.exec(text)) !== null) {
    const key = match[1].trim().toLowerCase();
    const val = match[2].trim();
    attrs[key] = val;
  }
  return attrs;
}

// ── ConflictDetector ───────────────────────────────────────────────────

export class ConflictDetector {
  private _conflictHistory: ConflictReport[] = [];

  constructor(
    private _manager: MemoryManager,
    private _llmProvider: LLMProvider,
    private _embeddingService?: EmbeddingService,
    public simThreshold: number = 0.7,
  ) {}

  private get embeddingService(): EmbeddingService {
    if (!this._embeddingService) {
      throw new Error("EmbeddingService not configured");
    }
    return this._embeddingService;
  }

  // ── detection ────────────────────────────────────────────────────────

  /** Run all three conflict detection strategies. Returns a (possibly empty) list. */
  detectConflicts(): ConflictReport[] {
    const storage = this._manager.semantic;
    const allMemories = storage.getAll();
    const active = allMemories.filter(
      (m) =>
        m.id &&
        m.content &&
        (m.metadata as Record<string, string>)?.deprecated !== "true" &&
        (m.metadata as Record<string, string>)?.deprecated !== "True" &&
        (m.metadata as Record<string, string>)?.deprecated !== "1",
    ) as Array<Record<string, string>>;

    if (active.length < 2) return [];

    const conflicts: ConflictReport[] = [];

    // Strategy 1: entity attribute conflicts
    conflicts.push(...this._detectEntityConflicts(active));

    // Strategy 2: timeline conflicts
    conflicts.push(...this._detectTimelineConflicts(active));

    // Strategy 3: semantic conflicts (high similarity, contradictory)
    conflicts.push(...this._detectSemanticConflicts(active));

    this._conflictHistory.push(...conflicts);
    return conflicts;
  }

  /** Detect same-entity, different-attribute-value conflicts. */
  private _detectEntityConflicts(
    active: Array<Record<string, string>>,
  ): ConflictReport[] {
    const conflicts: ConflictReport[] = [];

    // Index memories by entities they mention
    const entityIndex: Record<string, Array<Record<string, string>>> = {};
    for (const mem of active) {
      for (const entity of extractEntities(mem.content)) {
        if (!entityIndex[entity]) entityIndex[entity] = [];
        entityIndex[entity].push(mem);
      }
    }

    const seenPairs = new Set<string>();
    for (const [entity, mems] of Object.entries(entityIndex)) {
      if (mems.length < 2) continue;
      for (let i = 0; i < mems.length; i++) {
        for (let j = i + 1; j < mems.length; j++) {
          const midA = mems[i].id;
          const midB = mems[j].id;
          const pairKey = [midA, midB].sort().join("|");
          if (seenPairs.has(pairKey)) continue;
          seenPairs.add(pairKey);

          const attrsA = extractAttributes(mems[i].content);
          const attrsB = extractAttributes(mems[j].content);
          const conflictsFound: string[] = [];
          for (const key of Object.keys(attrsA)) {
            if (key in attrsB && attrsA[key].toLowerCase() !== attrsB[key].toLowerCase()) {
              conflictsFound.push(`${key}: ${attrsA[key]} vs ${attrsB[key]}`);
            }
          }

          if (conflictsFound.length > 0) {
            conflicts.push({
              conflictType: "entity",
              memoryIdA: midA,
              memoryIdB: midB,
              contentA: mems[i].content,
              contentB: mems[j].content,
              description: `Entity '${entity}' has conflicting attributes: ${conflictsFound.join(", ")}`,
              similarity: 0,
              resolved: false,
              resolution: null,
            });
          }
        }
      }
    }
    return conflicts;
  }

  /** Detect timeline inconsistencies (event order described differently). */
  private _detectTimelineConflicts(
    active: Array<Record<string, string>>,
  ): ConflictReport[] {
    const conflicts: ConflictReport[] = [];

    // Find memories with temporal expressions
    const timePattern = new RegExp(
      "(?:in|at|on|during|since|before|after|until|from|by)\\s+" +
        "(?:the\\s+)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|" +
        "Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)" +
        "\\s+\\d{2,4}|\\d{2,4}[-/]\\d{1,2}[-/]\\d{1,2}",
      "i",
    );

    const timedMemories = active.filter((m) => timePattern.test(m.content));
    if (timedMemories.length < 2) return conflicts;

    // Compare pairs with temporal references via LLM
    const seenPairs = new Set<string>();
    for (let i = 0; i < timedMemories.length; i++) {
      for (let j = i + 1; j < timedMemories.length; j++) {
        const midA = timedMemories[i].id;
        const midB = timedMemories[j].id;
        const pairKey = [midA, midB].sort().join("|");
        if (seenPairs.has(pairKey)) continue;
        seenPairs.add(pairKey);

        const prompt = CONFLICT_CHECK_PROMPT.replace(
          "{a}",
          timedMemories[i].content,
        ).replace("{b}", timedMemories[j].content);
        const response = this._llmProvider.generate(prompt, { maxTokens: 64 });
        if (response.toUpperCase().startsWith("YES")) {
          conflicts.push({
            conflictType: "timeline",
            memoryIdA: midA,
            memoryIdB: midB,
            contentA: timedMemories[i].content,
            contentB: timedMemories[j].content,
            description: response,
            similarity: 0,
            resolved: false,
            resolution: null,
          });
        }
      }
    }

    return conflicts;
  }

  /** Detect highly similar but contradictory memories via embeddings + LLM. */
  private _detectSemanticConflicts(
    active: Array<Record<string, string>>,
  ): ConflictReport[] {
    const conflicts: ConflictReport[] = [];
    if (active.length < 2) return conflicts;

    const texts = active.map((m) => m.content);
    let embeddings: number[][];
    try {
      embeddings = this.embeddingService.encode(texts);
    } catch {
      return conflicts;
    }

    const n = active.length;
    const seenPairs = new Set<string>();
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const midA = active[i].id;
        const midB = active[j].id;
        const pairKey = [midA, midB].sort().join("|");
        if (seenPairs.has(pairKey)) continue;
        seenPairs.add(pairKey);

        const sim = cosineSimilarity(embeddings[i], embeddings[j]);
        if (sim < this.simThreshold) continue;

        // High similarity -- check for contradiction via LLM
        const prompt = CONFLICT_CHECK_PROMPT.replace("{a}", active[i].content).replace(
          "{b}",
          active[j].content,
        );
        const response = this._llmProvider.generate(prompt, { maxTokens: 64 });
        if (response.toUpperCase().startsWith("YES")) {
          conflicts.push({
            conflictType: "semantic",
            memoryIdA: midA,
            memoryIdB: midB,
            contentA: active[i].content,
            contentB: active[j].content,
            description: response,
            similarity: sim,
            resolved: false,
            resolution: null,
          });
        }
      }
    }

    return conflicts;
  }

  // ── resolution ───────────────────────────────────────────────────────

  /** Resolve a single conflict via LLM arbitration. */
  resolveConflict(conflict: ConflictReport): ConflictResolution {
    const prompt = CONFLICT_RESOLVE_PROMPT.replace("{a}", conflict.contentA).replace(
      "{b}",
      conflict.contentB,
    );
    const answer = this._llmProvider.generate(prompt, { maxTokens: 128 });

    let resolution: ConflictResolution;
    if (answer.toUpperCase().startsWith("A")) {
      resolution = {
        action: "keep_a",
        winnerId: conflict.memoryIdA,
        mergedContent: "",
        reasoning: answer,
      };
    } else if (answer.toUpperCase().startsWith("B")) {
      resolution = {
        action: "keep_b",
        winnerId: conflict.memoryIdB,
        mergedContent: "",
        reasoning: answer,
      };
    } else {
      // Default to merge -- try to combine
      const merged = this._llmProvider.generate(
        `Combine these two statements into one accurate statement. ` +
          `Resolve any contradictions by keeping the more specific version.\n\n` +
          `A: ${conflict.contentA}\nB: ${conflict.contentB}\n\nCombined:`,
        { maxTokens: 256 },
      );
      resolution = {
        action: "merge",
        winnerId: "",
        mergedContent: merged || conflict.contentA,
        reasoning: answer,
      };
    }

    conflict.resolved = true;
    conflict.resolution = resolution;
    return resolution;
  }

  // ── full cycle ───────────────────────────────────────────────────────

  /** Run a full conflict detection and resolution cycle. Returns stats dict. */
  runCycle(): Record<string, unknown> {
    const t0 = Date.now();
    const conflicts = this.detectConflicts();

    let resolvedCount = 0;
    for (const conflict of conflicts) {
      try {
        this.resolveConflict(conflict);
        resolvedCount++;
      } catch {
        // skip failed resolutions
      }
    }

    const duration = Math.round(Date.now() - t0);

    return {
      conflictsDetected: conflicts.length,
      conflictsResolved: resolvedCount,
      byType: {
        entity: conflicts.filter((c) => c.conflictType === "entity").length,
        timeline: conflicts.filter((c) => c.conflictType === "timeline").length,
        semantic: conflicts.filter((c) => c.conflictType === "semantic").length,
      },
      durationMs: duration,
    };
  }

  /** Return the full conflict detection history. */
  getHistory(): ConflictReport[] {
    return [...this._conflictHistory];
  }

  /** Clear the conflict history. */
  clearHistory(): void {
    this._conflictHistory = [];
  }

  toString(): string {
    return `ConflictDetector(threshold=${this.simThreshold})`;
  }
}
