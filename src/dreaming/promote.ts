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
 * Dreaming Engine -- Promote Phase (Promoter | v4.12.0)
 *
 * Persists scored candidates and extracted patterns into long-term storage:
 *   - episodic memories -> SemanticStorage
 *   - semantic -> SemanticStorage.update() reinforcement
 *   - procedural -> ProceduralStorage
 *   - skills -> SkillStore
 */

import type { ScoredCandidate } from "./deep";
import type { REMResult } from "./rem";

// ── PromotionResult ──────────────────────────────────────────────────────

export interface PromotionResult {
  /** Count of episodic -> semantic promotions. */
  episodicPromoted: number;
  /** Count of semantic memory reinforcements. */
  semanticReinforced: number;
  /** Count of procedural entries written. */
  proceduralPromoted: number;
  /** Count of skills stored via SkillStore. */
  skillStored: number;
  /** If true, no actual writes occurred. */
  dryRun: boolean;
}

export function createPromotionResult(overrides?: Partial<PromotionResult>): PromotionResult {
  return {
    episodicPromoted: 0,
    semanticReinforced: 0,
    proceduralPromoted: 0,
    skillStored: 0,
    dryRun: false,
    ...overrides,
  };
}

export function promotionTotal(result: PromotionResult): number {
  return result.episodicPromoted + result.semanticReinforced + result.proceduralPromoted;
}

export function promotionResultToDict(r: PromotionResult): Record<string, unknown> {
  return {
    episodic_promoted: r.episodicPromoted,
    semantic_reinforced: r.semanticReinforced,
    procedural_promoted: r.proceduralPromoted,
    skill_stored: r.skillStored,
    total: promotionTotal(r),
    dry_run: r.dryRun,
  };
}

// ── MemoryManager abstraction ────────────────────────────────────────────

export interface MemoryManagerWithStorage {
  semantic: {
    store(data: Record<string, unknown>): void;
    getAll(): Array<Record<string, unknown>>;
    update(id: string, content: string): void;
  };
  procedural: {
    store(data: Record<string, unknown>): void;
  };
  skill_store?: {
    store(skill: unknown): void;
  };
}

// ── Promoter ─────────────────────────────────────────────────────────────

export class Promoter {
  private _mm: MemoryManagerWithStorage;
  private _dryRun: boolean;

  constructor(memoryManager: MemoryManagerWithStorage, dryRun = false) {
    this._mm = memoryManager;
    this._dryRun = dryRun;
  }

  /**
   * Promote candidates and REM results to long-term storage.
   *
   * @param candidates - Filtered ScoredCandidate list.
   * @param remResult - Pattern extraction results.
   * @returns PromotionResult with counts per storage type.
   */
  promote(candidates: ScoredCandidate[], remResult: REMResult): PromotionResult {
    const result = createPromotionResult({ dryRun: this._dryRun });

    // 1. Promote candidates based on memory type
    for (const c of candidates) {
      const mtype = c.signal.memoryType;

      if (mtype === "episodic" || mtype === "") {
        this._promoteToSemantic(c, result);
      } else if (mtype === "semantic") {
        this._reinforceSemantic(c, result);
      } else if (mtype === "procedural") {
        this._promoteToProcedural(c, result);
      }
    }

    // 2. Store extracted skills
    if (remResult.skills.length > 0) {
      result.skillStored = this._storeSkills(remResult.skills);
    }

    return result;
  }

  // ── internal promotion methods ─────────────────────────────────────────

  private _promoteToSemantic(
    c: ScoredCandidate,
    result: PromotionResult,
  ): void {
    if (this._dryRun) {
      result.episodicPromoted += 1;
      return;
    }

    try {
      this._mm.semantic.store({
        content: `[dreaming] ${c.signal.content}`,
        tags: [...(c.signal.tags ?? []), "dreaming", `score_${c.composite.toFixed(2)}`],
        metadata: {
          source: "dreaming_engine",
          composite_score: c.composite,
          frequency_score: c.frequencyScore,
          conceptual_richness: c.conceptualRichnessScore,
        },
        timestamp: new Date().toISOString(),
      });
      result.episodicPromoted += 1;
    } catch {
      // silently skip
    }
  }

  private _reinforceSemantic(
    c: ScoredCandidate,
    result: PromotionResult,
  ): void {
    if (this._dryRun) {
      result.semanticReinforced += 1;
      return;
    }

    try {
      const existing = this._mm.semantic.getAll();
      for (const mem of existing) {
        const memContent = (mem.content as string) ?? "";
        if (c.signal.content.includes(memContent) || memContent.includes(c.signal.content)) {
          const mid = mem.id as string | undefined;
          if (mid) {
            const reinforced = `[reinforced:${c.composite.toFixed(2)}] ${memContent}`;
            this._mm.semantic.update(mid, reinforced);
            result.semanticReinforced += 1;
            break;
          }
        }
      }
    } catch {
      // silently skip
    }
  }

  private _promoteToProcedural(
    c: ScoredCandidate,
    result: PromotionResult,
  ): void {
    if (this._dryRun) {
      result.proceduralPromoted += 1;
      return;
    }

    try {
      this._mm.procedural.store({
        content: c.signal.content,
        tags: [...(c.signal.tags ?? []), "dreaming_procedural"],
        metadata: { source: "dreaming_engine", composite_score: c.composite },
        timestamp: new Date().toISOString(),
      });
      result.proceduralPromoted += 1;
    } catch {
      // silently skip
    }
  }

  private _storeSkills(skills: unknown[]): number {
    if (this._dryRun || !skills.length) return 0;

    let count = 0;
    try {
      const store = this._mm.skill_store;
      if (!store) return 0;
      for (const skill of skills) {
        store.store(skill);
        count += 1;
      }
    } catch {
      // silently skip
    }
    return count;
  }
}
