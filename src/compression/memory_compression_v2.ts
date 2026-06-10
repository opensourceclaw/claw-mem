// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Memory Compression Module for claw-mem v2.12.0
 *
 * Active memory compression based on Focus and ProMem papers:
 * - Focus: Sawtooth pattern, autonomous triggering, Knowledge Block
 * - ProMem: Three-stage verification (extraction -> completion -> verification)
 *
 * Phase 1-3 implementation:
 * - Phase 1: Base architecture MemoryCompressorV2 + KnowledgeBlock
 * - Phase 2: Rule-triggered compression (count/interval thresholds)
 * - Phase 3: Semantic deduplication (BM25 similarity)
 */

import * as crypto from "crypto";
import * as fs from "fs";
import * as path from "path";

// ── CompressionLevel enum ─────────────────────────────────────────────────

export enum CompressionLevel {
  LIGHT = "light",
  MEDIUM = "medium",
  AGGRESSIVE = "aggressive",
}

// ── CompressionTrigger enum ───────────────────────────────────────────────

export enum CompressionTrigger {
  MANUAL = "manual",
  MEMORY_COUNT = "memory_count",
  TOKEN_ESTIMATE = "token_estimate",
  INTERVAL = "interval",
  SESSION_END = "session_end",
}

// ── CompressionConfig ────────────────────────────────────────────────────

export interface CompressionConfig {
  enabled: boolean;
  maxMemories: number;
  maxTokens: number;
  compressionInterval: number;
  similarityThreshold: number;
  useBm25Deduplication: boolean;
  knowledgeBlockEnabled: boolean;
  knowledgeBlockPath: string;
  maxKnowledgeEntries: number;
  level: CompressionLevel;
  enableSelfVerification: boolean;
}

export const DEFAULT_COMPRESSION_CONFIG: CompressionConfig = {
  enabled: true,
  maxMemories: 100,
  maxTokens: 10000,
  compressionInterval: 50,
  similarityThreshold: 0.8,
  useBm25Deduplication: true,
  knowledgeBlockEnabled: true,
  knowledgeBlockPath: ".claw-mem/knowledge",
  maxKnowledgeEntries: 50,
  level: CompressionLevel.MEDIUM,
  enableSelfVerification: false,
};

export function compressionConfigToDict(
  config: CompressionConfig,
): Record<string, unknown> {
  return {
    enabled: config.enabled,
    max_memories: config.maxMemories,
    max_tokens: config.maxTokens,
    compression_interval: config.compressionInterval,
    similarity_threshold: config.similarityThreshold,
    knowledge_block_enabled: config.knowledgeBlockEnabled,
    level: config.level,
  };
}

// ── CompressionResult ────────────────────────────────────────────────────

export interface CompressionResult {
  trigger: CompressionTrigger;
  originalCount: number;
  compressedCount: number;
  compressionRatio: number;
  tokenSavings: number;
  preservedMemoryIds: string[];
  removedMemoryIds: string[];
  extractedKnowledge: string[];
  timestamp: Date;
  durationMs: number;
}

export function createCompressionResult(
  overrides?: Partial<CompressionResult>,
): CompressionResult {
  return {
    trigger: CompressionTrigger.MANUAL,
    originalCount: 0,
    compressedCount: 0,
    compressionRatio: 0,
    tokenSavings: 0,
    preservedMemoryIds: [],
    removedMemoryIds: [],
    extractedKnowledge: [],
    timestamp: new Date(),
    durationMs: 0,
    ...overrides,
  };
}

export function compressionResultToDict(
  r: CompressionResult,
): Record<string, unknown> {
  return {
    trigger: r.trigger,
    original_count: r.originalCount,
    compressed_count: r.compressedCount,
    compression_ratio: r.compressionRatio,
    token_savings: r.tokenSavings,
    preserved_count: r.preservedMemoryIds.length,
    removed_count: r.removedMemoryIds.length,
    extracted_knowledge_count: r.extractedKnowledge.length,
    timestamp: r.timestamp.toISOString(),
    duration_ms: r.durationMs,
  };
}

// ── KnowledgeEntry ───────────────────────────────────────────────────────

export interface KnowledgeEntry {
  key: string;
  value: string;
  category: string;
  source: string;
  importance: number;
  memoryIds: string[];
  createdAt: Date;
  accessedAt: Date;
  accessCount: number;
}

export function createKnowledgeEntry(
  overrides?: Partial<KnowledgeEntry>,
): KnowledgeEntry {
  return {
    key: "",
    value: "",
    category: "general",
    source: "compression",
    importance: 0.5,
    memoryIds: [],
    createdAt: new Date(),
    accessedAt: new Date(),
    accessCount: 0,
    ...overrides,
  };
}

export function knowledgeEntryToDict(
  e: KnowledgeEntry,
): Record<string, unknown> {
  return {
    key: e.key,
    value: e.value,
    category: e.category,
    source: e.source,
    importance: e.importance,
    memory_ids: e.memoryIds,
    created_at: e.createdAt.toISOString(),
    accessed_at: e.accessedAt.toISOString(),
    access_count: e.accessCount,
  };
}

export function knowledgeEntryFromDict(
  data: Record<string, unknown>,
): KnowledgeEntry {
  return {
    key: data.key as string,
    value: data.value as string,
    category: data.category as string,
    source: data.source as string,
    importance: data.importance as number,
    memoryIds: (data.memory_ids as string[]) ?? [],
    createdAt: new Date(data.created_at as string),
    accessedAt: new Date(data.accessed_at as string),
    accessCount: (data.access_count as number) ?? 0,
  };
}

// ── KeyInformationExtractor ──────────────────────────────────────────────

export class KeyInformationExtractor {
  private readonly _decisionPatterns: RegExp[] = [
    /(决定|决策|选择|确定|批准|同意|拒绝|否认|确定 to )/i,
    /(decided|decided to|agreed|accepted|rejected|chose|selected|will|should|must)/i,
  ];

  private readonly _factPatterns: RegExp[] = [
    /(事实|实际上| its 实| already 经| already 知|确认|证明)/i,
    /(fact|actually|known|already|confirmed|proven|true|realized)/i,
  ];

  private readonly _taskPatterns: RegExp[] = [
    /(任务|目标|需 to |完成|做|执行|下一步|计划)/i,
    /(task|goal|need|complete|do|execute|action|next step|plan|intend)/i,
  ];

  private readonly _prefPatterns: RegExp[] = [
    /(喜欢|偏爱|prefer|like|better|instead of|rather|enjoy)/i,
    /( not 喜欢|讨厌|dislike|hate|avoid|not fond of)/i,
  ];

  extract(text: string): Record<string, string[]> {
    return {
      decisions: this._extractMatches(text, this._decisionPatterns),
      facts: this._extractMatches(text, this._factPatterns),
      tasks: this._extractMatches(text, this._taskPatterns),
      preferences: this._extractMatches(text, this._prefPatterns),
    };
  }

  extractCategories(text: string): string[] {
    const categories: string[] = [];
    if (this._hasMatch(text, this._decisionPatterns)) categories.push("decision");
    if (this._hasMatch(text, this._factPatterns)) categories.push("fact");
    if (this._hasMatch(text, this._taskPatterns)) categories.push("task");
    if (this._hasMatch(text, this._prefPatterns)) categories.push("preference");
    return categories.length > 0 ? categories : ["general"];
  }

  private _extractMatches(text: string, patterns: RegExp[]): string[] {
    const matches = new Set<string>();
    for (const pattern of patterns) {
      const found = text.match(pattern);
      if (found) {
        for (const m of found) {
          matches.add(m);
        }
      }
    }
    return Array.from(matches);
  }

  private _hasMatch(text: string, patterns: RegExp[]): boolean {
    return patterns.some((p) => p.test(text));
  }
}

// ── SemanticDeduplicator ─────────────────────────────────────────────────

export class SemanticDeduplicator {
  readonly threshold: number;
  private _extractor: KeyInformationExtractor;

  constructor(threshold = 0.8) {
    this.threshold = threshold;
    this._extractor = new KeyInformationExtractor();
  }

  /**
   * Deduplicate memories.
   *
   * @param memories - List of memories.
   * @returns Deduplicated list of memories.
   */
  deduplicate(memories: Record<string, unknown>[]): Record<string, unknown>[] {
    if (!memories.length) return [];

    // Sort by importance (retain high-importance ones)
    const sorted = [...memories].sort(
      (a, b) => ((b.importance as number) ?? 0.5) - ((a.importance as number) ?? 0.5),
    );

    const unique: Record<string, unknown>[] = [];
    for (const mem of sorted) {
      const content = (mem.content as string) ?? "";
      if (!content) continue;

      let isDuplicate = false;
      const contentLower = content.toLowerCase();

      for (let i = 0; i < unique.length; i++) {
        const existing = unique[i];
        const existingContent = ((existing.content as string) ?? "").toLowerCase();
        if (this._isSimilar(contentLower, existingContent)) {
          // Retain the one with higher importance
          if ((mem.importance as number) > (existing.importance as number)) {
            unique[i] = mem;
          }
          isDuplicate = true;
          break;
        }
      }

      if (!isDuplicate) {
        unique.push(mem);
      }
    }

    return unique;
  }

  private _isSimilar(text1: string, text2: string): boolean {
    // Extract key information
    const info1 = this._extractor.extract(text1);
    const info2 = this._extractor.extract(text2);

    const allInfo1 = new Set<string>();
    const allInfo2 = new Set<string>();

    for (const key of ["decisions", "facts", "tasks", "preferences"]) {
      for (const v of info1[key] ?? []) allInfo1.add(v);
      for (const v of info2[key] ?? []) allInfo2.add(v);
    }

    if (allInfo1.size === 0 || allInfo2.size === 0) {
      // If no key information extracted, use word overlap
      const words1 = new Set(text1.toLowerCase().split(/\s+/));
      const words2 = new Set(text2.toLowerCase().split(/\s+/));
      if (words1.size === 0 || words2.size === 0) return false;
      const intersection = new Set([...words1].filter((w) => words2.has(w)));
      const union = new Set([...words1, ...words2]);
      return intersection.size / union.size >= this.threshold;
    }

    // Key information overlap
    const intersection = new Set([...allInfo1].filter((w) => allInfo2.has(w)));
    const union = new Set([...allInfo1, ...allInfo2]);
    return intersection.size / union.size >= this.threshold;
  }
}

// ── KnowledgeBlock ───────────────────────────────────────────────────────

export class KnowledgeBlock {
  readonly storagePath: string;
  readonly maxEntries: number;
  private _knowledge: Map<string, KnowledgeEntry> = new Map();

  constructor(storagePath: string, maxEntries = 50) {
    this.storagePath = storagePath;
    this.maxEntries = maxEntries;
    this._load();
  }

  add(
    key: string,
    value: string,
    category = "general",
    importance = 0.5,
    memoryIds?: string[],
  ): void {
    const existing = this._knowledge.get(key);
    const now = new Date();

    if (existing) {
      existing.value = value;
      existing.importance = Math.max(existing.importance, importance);
      existing.accessedAt = now;
      existing.accessCount += 1;
      if (memoryIds) {
        existing.memoryIds = [
          ...new Set([...existing.memoryIds, ...memoryIds]),
        ];
      }
    } else {
      this._knowledge.set(
        key,
        createKnowledgeEntry({
          key,
          value,
          category,
          source: "compression",
          importance,
          memoryIds: memoryIds ?? [],
          createdAt: now,
          accessedAt: now,
          accessCount: 0,
        }),
      );
    }

    this._trim();
    this._persist();
  }

  get(key: string): string | undefined {
    const entry = this._knowledge.get(key);
    if (entry) {
      entry.accessedAt = new Date();
      entry.accessCount += 1;
      this._persist();
      return entry.value;
    }
    return undefined;
  }

  /** Get all knowledge (formatted, for context injection). */
  getAll(limit = 10): string {
    const sorted = this._sortedEntries(limit);
    if (sorted.length === 0) return "";

    const lines = ["[Knowledge Block]"];
    for (const entry of sorted) {
      lines.push(`- ${entry.key}: ${entry.value}`);
    }
    return lines.join("\n");
  }

  /** Get knowledge dictionary (for retrieval). */
  getDict(limit = 20): Record<string, unknown>[] {
    return this._sortedEntries(limit).map(knowledgeEntryToDict);
  }

  /** Search knowledge entries. */
  search(query: string): KnowledgeEntry[] {
    const queryLower = query.toLowerCase();
    const results: KnowledgeEntry[] = [];
    for (const entry of this._knowledge.values()) {
      if (
        entry.key.toLowerCase().includes(queryLower) ||
        entry.value.toLowerCase().includes(queryLower)
      ) {
        results.push(entry);
      }
    }
    return results
      .sort((a, b) => b.importance - a.importance)
      .slice(0, 5);
  }

  private _sortedEntries(limit: number): KnowledgeEntry[] {
    return [...this._knowledge.values()]
      .sort(
        (a, b) =>
          b.accessCount * 0.3 + b.importance * 0.7 - (a.accessCount * 0.3 + a.importance * 0.7),
      )
      .slice(0, limit);
  }

  private _trim(): void {
    if (this._knowledge.size <= this.maxEntries) return;

    const sorted = [...this._knowledge.values()].sort(
      (a, b) =>
        b.accessCount * 0.3 + b.importance * 0.7 - (a.accessCount * 0.3 + a.importance * 0.7),
    );

    this._knowledge = new Map(
      sorted.slice(0, this.maxEntries).map((e) => [e.key, e]),
    );
  }

  private _load(): void {
    if (!fs.existsSync(this.storagePath)) return;

    try {
      const raw = fs.readFileSync(this.storagePath, "utf-8");
      const data = JSON.parse(raw) as Record<string, unknown>[];
      for (const item of data) {
        const entry = knowledgeEntryFromDict(item);
        this._knowledge.set(entry.key, entry);
      }
    } catch {
      // silently skip on load error
    }
  }

  private _persist(): void {
    fs.mkdirSync(path.dirname(this.storagePath), { recursive: true });
    const data = [...this._knowledge.values()].map(knowledgeEntryToDict);
    try {
      fs.writeFileSync(this.storagePath, JSON.stringify(data, null, 2), "utf-8");
    } catch {
      // silently skip on persist error
    }
  }
}

// ── MemoryCompressorV2 ───────────────────────────────────────────────────

export class MemoryCompressorV2 {
  readonly config: CompressionConfig;
  readonly workspacePath: string;

  operationCount = 0;
  lastCompressionIdx = 0;
  compressionCount = 0;

  private _extractor: KeyInformationExtractor;
  private _deduplicator: SemanticDeduplicator;
  private _knowledgeBlock: KnowledgeBlock | undefined;

  constructor(config?: CompressionConfig, workspacePath?: string) {
    this.config = config ?? { ...DEFAULT_COMPRESSION_CONFIG };
    this.workspacePath = workspacePath ?? ".";

    this._extractor = new KeyInformationExtractor();
    this._deduplicator = new SemanticDeduplicator(
      this.config.similarityThreshold,
    );

    if (this.config.knowledgeBlockEnabled) {
      const kbPath = path.join(
        this.workspacePath,
        this.config.knowledgeBlockPath,
      );
      this._knowledgeBlock = new KnowledgeBlock(
        kbPath,
        this.config.maxKnowledgeEntries,
      );
    }
  }

  /**
   * Determine whether compression is needed (Phase 2).
   *
   * @returns [whether compression is needed, trigger reason].
   */
  shouldCompress(
    memoryCount: number,
    tokenEstimate = 0,
    force = false,
  ): [boolean, CompressionTrigger | undefined] {
    if (!this.config.enabled && !force) {
      return [false, undefined];
    }

    if (force) return [true, CompressionTrigger.MANUAL];

    if (memoryCount > this.config.maxMemories) {
      return [true, CompressionTrigger.MEMORY_COUNT];
    }

    if (tokenEstimate > this.config.maxTokens) {
      return [true, CompressionTrigger.TOKEN_ESTIMATE];
    }

    if (
      this.operationCount - this.lastCompressionIdx >=
      this.config.compressionInterval
    ) {
      return [true, CompressionTrigger.INTERVAL];
    }

    return [false, undefined];
  }

  /**
   * Execute compression (Phase 1-3).
   *
   * Workflow:
   * 1. Extract key information
   * 2. Semantic deduplication
   * 3. Update Knowledge Block
   * 4. Return compression result
   */
  compress(
    memories: Record<string, unknown>[],
    sessionEnd = false,
  ): CompressionResult {
    const t0 = Date.now();
    const originalCount = memories.length;

    if (originalCount === 0) {
      return createCompressionResult({
        trigger: CompressionTrigger.MANUAL,
        originalCount: 0,
        compressedCount: 0,
      });
    }

    // Phase 2: Determine trigger reason
    let [, trigger] = this.shouldCompress(originalCount);
    if (sessionEnd) trigger = CompressionTrigger.SESSION_END;
    trigger = trigger ?? CompressionTrigger.MANUAL;

    // Phase 1: Extract key information (categorize)
    const categorized = this._categorizeMemories(memories);

    // Phase 3: Semantic deduplication
    const deduplicated = this._deduplicator.deduplicate(categorized);

    // Update Knowledge Block
    let extractedKnowledge: string[] = [];
    if (this._knowledgeBlock) {
      extractedKnowledge = this._updateKnowledgeBlock(deduplicated);
    }

    // Calculate compression result
    const compressedCount = deduplicated.length;
    const compressionRatio =
      originalCount > 0 ? 1 - compressedCount / originalCount : 0;
    const tokenSavings = compressionRatio;

    // Update state
    this.lastCompressionIdx = this.operationCount;
    this.compressionCount += 1;

    const durationMs = Date.now() - t0;

    return createCompressionResult({
      trigger,
      originalCount,
      compressedCount,
      compressionRatio,
      tokenSavings,
      preservedMemoryIds: deduplicated.map(
        (m) => (m.id as string) ?? "",
      ),
      removedMemoryIds: memories
        .filter((m) => !deduplicated.includes(m))
        .map((m) => (m.id as string) ?? ""),
      extractedKnowledge,
      durationMs,
    });
  }

  private _categorizeMemories(
    memories: Record<string, unknown>[],
  ): Record<string, unknown>[] {
    return memories.map((mem) => {
      const content = (mem.content as string) ?? "";
      const categories = this._extractor.extractCategories(content);

      // Calculate importance
      let importance = 0.5;
      if (categories.includes("decision")) importance = 0.9;
      else if (categories.includes("preference")) importance = 0.8;
      else if (categories.includes("task")) importance = 0.7;
      else if (categories.includes("fact")) importance = 0.6;

      const existingImportance = (mem.importance as number) ?? 0.5;

      return {
        ...mem,
        importance: Math.max(existingImportance, importance),
        categories,
      };
    });
  }

  private _updateKnowledgeBlock(
    memories: Record<string, unknown>[],
  ): string[] {
    if (!this._knowledgeBlock) return [];

    const extracted: string[] = [];

    for (const mem of memories) {
      const content = (mem.content as string) ?? "";
      const memoryId = (mem.id as string) ?? "";
      const importance = (mem.importance as number) ?? 0.5;
      const categories = (mem.categories as string[]) ?? ["general"];

      // Generate key
      const contentHash = crypto
        .createHash("md5")
        .update(content)
        .digest("hex")
        .slice(0, 8);
      const key = `${categories[0]}_${contentHash}`;

      // Add to Knowledge Block
      this._knowledgeBlock.add(key, content.slice(0, 200), categories[0], importance, [
        memoryId,
      ]);

      extracted.push(key);
    }

    return extracted;
  }

  recordOperation(): void {
    this.operationCount += 1;
  }

  getKnowledgeBlock(): string | undefined {
    return this._knowledgeBlock?.getAll();
  }

  searchKnowledge(query: string): string[] {
    if (!this._knowledgeBlock) return [];
    return this._knowledgeBlock.search(query).map((e) => e.value);
  }
}

// ── Global instance ──────────────────────────────────────────────────────

let _compressor: MemoryCompressorV2 | undefined;

export function getCompressor(
  config?: CompressionConfig,
  workspacePath?: string,
): MemoryCompressorV2 {
  if (_compressor === undefined) {
    _compressor = new MemoryCompressorV2(config, workspacePath);
  }
  return _compressor;
}

export function resetCompressor(): void {
  _compressor = undefined;
}
