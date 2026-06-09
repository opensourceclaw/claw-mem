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
 * Dreaming Engine -- Light Phase (Signal Ingestor | v4.12.0)
 *
 * Reads recent episodic memories, computes basic signal metrics,
 * deduplicates against existing semantic memories, and stages
 * candidates for deep scoring.
 */

import { DEFAULT_DREAMING_CONFIG, type DreamingConfig } from "./config";

// ── Signal dataclass ─────────────────────────────────────────────────────

export interface Signal {
  /** Source memory ID. */
  memoryId: string;
  /** Memory content text. */
  content: string;
  /** Type (episodic, semantic, etc.). */
  memoryType: string;
  /** How many times this signal has been recalled. */
  recallCount: number;
  /** Number of distinct queries that matched this content. */
  uniqueQueries: number;
  /** List of relevance scores from prior retrievals. */
  relevanceScores: number[];
  /** Associated tags. */
  tags: string[];
  /** ISO timestamp string. */
  timestamp: string;
}

export function createSignal(overrides?: Partial<Signal>): Signal {
  return {
    memoryId: "",
    content: "",
    memoryType: "episodic",
    recallCount: 1,
    uniqueQueries: 0,
    relevanceScores: [0.5],
    tags: [],
    timestamp: "",
    ...overrides,
  };
}

export function signalToDict(signal: Signal): Record<string, unknown> {
  return {
    memory_id: signal.memoryId,
    content: signal.content,
    memory_type: signal.memoryType,
    recall_count: signal.recallCount,
    unique_queries: signal.uniqueQueries,
    relevance_scores: signal.relevanceScores,
    tags: signal.tags,
    timestamp: signal.timestamp,
  };
}

// ── SignalIngestor ───────────────────────────────────────────────────────

export interface MemoryManagerLike {
  episodic: {
    getRecent(count: number): Array<Record<string, unknown>>;
  };
  semantic: {
    getAll(): Array<Record<string, unknown>>;
  };
}

export class SignalIngestor {
  private _mm: MemoryManagerLike;
  private _config: DreamingConfig;
  private _staged: Signal[] = [];

  constructor(memoryManager: MemoryManagerLike, config?: DreamingConfig) {
    this._mm = memoryManager;
    this._config = config ?? DEFAULT_DREAMING_CONFIG;
  }

  /**
   * Read recent episodic memories, deduplicate, and stage signals.
   *
   * @returns Number of signals staged.
   */
  ingest(): number {
    const episodic = this._mm.episodic.getRecent(this._config.maxStaged);
    const existingSemantic = this._mm.semantic.getAll();

    // Collect existing semantic content for substring dedup
    const semanticTexts: string[] = existingSemantic.map(
      (m) => (m.content as string) ?? "",
    );

    // Count query occurrences per content
    const contentCounts = new Map<string, number>();
    const contentQueries = new Map<string, Set<string>>();

    for (const mem of episodic) {
      const content = (mem.content as string) ?? "";
      if (!content) continue;
      contentCounts.set(content, (contentCounts.get(content) ?? 0) + 1);
      if (!contentQueries.has(content)) {
        contentQueries.set(content, new Set());
      }
      const queries = (mem.tags as string[]) ?? [];
      const qset = contentQueries.get(content)!;
      for (const q of queries) {
        qset.add(q);
      }
    }

    this._staged = [];
    const seenContent = new Set<string>();

    for (const mem of episodic) {
      const content = (mem.content as string) ?? "";
      if (!content) continue;

      // Deduplicate by content (same content → one signal with recallCount)
      if (seenContent.has(content)) continue;
      seenContent.add(content);

      // Deduplicate: skip if substring match against any semantic memory
      if (semanticTexts.some((st) => content.includes(st) || st.includes(content))) {
        continue;
      }

      const signal: Signal = {
        memoryId: (mem.id as string) ?? "",
        content,
        memoryType: (mem.type as string) ?? "episodic",
        recallCount: contentCounts.get(content) ?? 1,
        uniqueQueries: contentQueries.get(content)?.size ?? 0,
        relevanceScores: [0.5],
        tags: (mem.tags as string[]) ?? [],
        timestamp: (mem.timestamp as string) ?? "",
      };
      this._staged.push(signal);
    }

    return this._staged.length;
  }

  /** Get all staged signals as dicts. */
  getStaged(): Record<string, unknown>[] {
    return this._staged.map(signalToDict);
  }

  /** Clear all staged signals. */
  clearStaged(): void {
    this._staged = [];
  }

  /** Access staged signals directly (for pipeline orchestration). */
  get _internalStaged(): Signal[] {
    return this._staged;
  }
}
