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
 * Dreaming Engine -- Pipeline (v4.12.0)
 *
 * Orchestrates the complete light->deep->REM->promote pipeline.
 * Supports dry_run mode (score-only, no persistence).
 */

import { DEFAULT_DREAMING_CONFIG, type DreamingConfig } from "./config";
import { SignalIngestor, type MemoryManagerLike, type Signal } from "./light";
import { CandidateScorer, type ScoredCandidate } from "./deep";
import { PatternExtractor, type REMResult } from "./rem";
import { Promoter, type MemoryManagerWithStorage, type PromotionResult } from "./promote";

// ── DreamingResult ───────────────────────────────────────────────────────

export interface DreamingResult {
  /** Number of signals staged in light phase. */
  staged: number;
  /** Number of candidates scored in deep phase. */
  scored: number;
  /** Number of candidates passing the filter. */
  passed: number;
  /** Total promotions (episodic + semantic + procedural). */
  promoted: number;
  /** Number of skills persisted. */
  skillsStored: number;
  /** Pipeline wall-clock duration in milliseconds. */
  durationMs: number;
  /** Whether this was a dry run. */
  dryRun: boolean;
  /** Error message if the pipeline failed (undefined on success). */
  error?: string;
  /** Detailed PromotionResult (undefined on dry_run). */
  promotionDetail?: Record<string, unknown>;
}

export function createDreamingResult(overrides?: Partial<DreamingResult>): DreamingResult {
  return {
    staged: 0,
    scored: 0,
    passed: 0,
    promoted: 0,
    skillsStored: 0,
    durationMs: 0,
    dryRun: false,
    ...overrides,
  };
}

export function dreamingResultToDict(r: DreamingResult): Record<string, unknown> {
  const d: Record<string, unknown> = {
    staged: r.staged,
    scored: r.scored,
    passed: r.passed,
    promoted: r.promoted,
    skills_stored: r.skillsStored,
    duration_ms: Math.round(r.durationMs * 100) / 100,
    dry_run: r.dryRun,
  };
  if (r.error) d.error = r.error;
  if (r.promotionDetail) d.promotion_detail = r.promotionDetail;
  return d;
}

// Combine both memory manager interfaces for pipeline usage
type FullMemoryManager = MemoryManagerLike & MemoryManagerWithStorage;

// ── DreamingPipeline ─────────────────────────────────────────────────────

export class DreamingPipeline {
  private _mm: FullMemoryManager;
  private _config: DreamingConfig;
  private _llm: unknown;
  private _lastResult: DreamingResult | undefined;

  constructor(
    memoryManager: FullMemoryManager,
    config?: DreamingConfig,
    llmProvider?: unknown,
  ) {
    this._mm = memoryManager;
    this._config = config ?? DEFAULT_DREAMING_CONFIG;
    this._llm = llmProvider;
  }

  /**
   * Execute the full dreaming pipeline.
   *
   * @returns DreamingResult with stage counts and timing.
   */
  run(): DreamingResult {
    const t0 = Date.now();
    const result = createDreamingResult({ dryRun: this._config.dryRun });

    try {
      // ── Phase 1: Light (ingest signals) ────
      const ingestor = new SignalIngestor(this._mm, this._config);
      const stagedCount = ingestor.ingest();
      result.staged = stagedCount;

      if (stagedCount === 0) {
        result.durationMs = Date.now() - t0;
        this._lastResult = result;
        return result;
      }

      const signals: Signal[] = ingestor["_internalStaged"];

      // ── Phase 2: Deep (score candidates) ────
      const scorer = new CandidateScorer(this._config);
      const allCandidates = scorer.scoreAll(signals);
      result.scored = allCandidates.length;

      const passed = scorer.filter(allCandidates);
      result.passed = passed.length;

      if (passed.length === 0) {
        result.durationMs = Date.now() - t0;
        this._lastResult = result;
        return result;
      }

      // ── Phase 3: REM (extract patterns) ────
      const extractor = new PatternExtractor(this._llm);
      const remResult: REMResult = extractor.extract(passed);

      // ── Phase 4: Promote (persist) ────
      const promoter = new Promoter(this._mm, this._config.dryRun);
      const promotion: PromotionResult = promoter.promote(passed, remResult);
      result.promoted =
        promotion.episodicPromoted +
        promotion.semanticReinforced +
        promotion.proceduralPromoted;
      result.skillsStored = promotion.skillStored;
      result.promotionDetail = {
        episodic_promoted: promotion.episodicPromoted,
        semantic_reinforced: promotion.semanticReinforced,
        procedural_promoted: promotion.proceduralPromoted,
        skill_stored: promotion.skillStored,
        total: result.promoted,
        dry_run: promotion.dryRun,
      };

      // Store skills from REM
      if (remResult.skills.length > 0 && !this._config.dryRun) {
        result.skillsStored = promotion.skillStored;
      }
    } catch (e) {
      result.error = e instanceof Error ? e.message : String(e);
    }

    result.durationMs = Date.now() - t0;
    this._lastResult = result;
    return result;
  }

  /** Get the result of the last pipeline run. */
  lastResult(): DreamingResult | undefined {
    return this._lastResult;
  }
}
