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
 * Reflection Orchestrator
 *
 * Coordinates the full reflection pipeline:
 *   1. Collect recent observations from memory
 *   2. Synthesize into beliefs
 *   3. Track belief changes
 *   4. Store results back to memory
 */

import { BeliefTracker } from "./belief_tracker";
import {
  BeliefSynthesizer,
  Belief,
  Observation,
  SynthesizerConfig,
} from "./synthesizer";

// ── ReflectionResult ──────────────────────────────────────────────────

export interface ReflectionResult {
  observations: Observation[];
  beliefs: Belief[];
  new_beliefs: Belief[];
  updated_beliefs: Belief[];
  timestamp: string;
  summary: string;
}

// ── ReflectionOrchestrator ────────────────────────────────────────────

export class ReflectionOrchestrator {
  synthesizer: BeliefSynthesizer;
  tracker: BeliefTracker;
  private _lastReflectionAt: string | null = null;
  private _reflectionCount = 0;

  constructor(config?: Partial<SynthesizerConfig>) {
    this.synthesizer = new BeliefSynthesizer(config);
    this.tracker = new BeliefTracker();
  }

  /**
   * Execute a full reflection cycle.
   *
   * @param memories - Recent memory records to reflect on
   * @param userId - User identifier
   * @param force - Force reflection even if not enough data
   * @returns ReflectionResult with observations and beliefs
   */
  reflect(
    memories: Record<string, unknown>[],
    userId: string = "",
    force: boolean = false,
  ): ReflectionResult {
    const now = new Date().toISOString();
    this._reflectionCount++;
    this._lastReflectionAt = now;

    // Step 1: Extract observations
    const observations = this.synthesizer.extract_observations(memories);

    // Step 2: Synthesize beliefs
    const beliefs = this.synthesizer.synthesize(observations, userId);

    // Step 3: Track changes (new vs updated)
    const newBeliefs: Belief[] = [];
    const updatedBeliefs: Belief[] = [];

    for (const belief of beliefs) {
      const existing = this.tracker.get_current(belief.id);
      if (existing) {
        if (existing.statement !== belief.statement) {
          this.tracker.update(belief.id, belief.statement, belief.confidence);
          updatedBeliefs.push(belief);
        }
      } else {
        this.tracker.record(belief.id, belief.statement, belief.confidence);
        newBeliefs.push(belief);
      }
    }

    // Step 4: Build summary
    const summary =
      `Reflection #${this._reflectionCount}: ` +
      `${observations.length} observations \u2192 ` +
      `${beliefs.length} beliefs ` +
      `(${newBeliefs.length} new, ${updatedBeliefs.length} updated)`;

    return {
      observations,
      beliefs,
      new_beliefs: newBeliefs,
      updated_beliefs: updatedBeliefs,
      timestamp: now,
      summary,
    };
  }

  /**
   * Get all current beliefs.
   *
   * @param includeHistory - Include version history
   * @returns List of belief dicts
   */
  get_beliefs(includeHistory: boolean = false): Record<string, unknown>[] {
    const beliefs: Record<string, unknown>[] = [];
    for (const beliefId of this.tracker.get_all_ids()) {
      const version = this.tracker.get_current(beliefId);
      if (version) {
        const b: Record<string, unknown> = {
          belief_id: version.belief_id,
          statement: version.statement,
          confidence: version.confidence,
          version: version.version,
          created_at: version.created_at,
        };
        if (includeHistory) {
          b.history = this.tracker
            .get_history(beliefId)
            .map((v) => ({
              belief_id: v.belief_id,
              statement: v.statement,
              confidence: v.confidence,
              version: v.version,
              created_at: v.created_at,
              previous_statement: v.previous_statement,
            }));
        }
        beliefs.push(b);
      }
    }
    return beliefs;
  }

  /**
   * Get reflection statistics.
   *
   * @returns Dict with reflection stats
   */
  get_reflection_stats(): Record<string, unknown> {
    return {
      reflection_count: this._reflectionCount,
      last_reflection_at: this._lastReflectionAt,
      total_beliefs: this.tracker.count_beliefs(),
      total_versions: this.tracker.count_versions(),
    };
  }
}
