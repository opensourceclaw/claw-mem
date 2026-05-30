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
 * Dreaming Engine Configuration (v4.12.0)
 *
 * Weighted scoring parameters for the light->deep->REM->promote pipeline.
 * All weights sum to 1.0 for a normalized composite score.
 */

export interface DreamingConfig {
  /** Weight for how often a signal appears (0.0-1.0). */
  frequencyWeight: number;
  /** Weight for semantic relevance to existing knowledge. */
  relevanceWeight: number;
  /** Weight for number of distinct queries. */
  queryDiversityWeight: number;
  /** Weight for temporal freshness. */
  recencyWeight: number;
  /** Weight for how well-integrated the signal is. */
  consolidationWeight: number;
  /** Weight for information density. */
  conceptualRichnessWeight: number;
  /** Minimum composite score to pass the deep filter (0.0-1.0). */
  scoreThreshold: number;
  /** Maximum signals to stage in light phase. */
  maxStaged: number;
  /** Max candidates after deep scoring. */
  topKCandidates: number;
  /** If true, the pipeline scores but does not persist. */
  dryRun: boolean;
}

/** Default dreaming configuration. */
export const DEFAULT_DREAMING_CONFIG: DreamingConfig = {
  frequencyWeight: 0.20,
  relevanceWeight: 0.20,
  queryDiversityWeight: 0.15,
  recencyWeight: 0.15,
  consolidationWeight: 0.15,
  conceptualRichnessWeight: 0.15,
  scoreThreshold: 0.35,
  maxStaged: 50,
  topKCandidates: 20,
  dryRun: false,
};

/**
 * Validate that all weights sum approximately to 1.0.
 *
 * @param config - The dreaming config to validate.
 * @returns true if weights sum to 1.0 within a 0.01 tolerance.
 */
export function validateDreamingConfig(config: DreamingConfig): boolean {
  const total =
    config.frequencyWeight +
    config.relevanceWeight +
    config.queryDiversityWeight +
    config.recencyWeight +
    config.consolidationWeight +
    config.conceptualRichnessWeight;
  return Math.abs(total - 1.0) < 0.01;
}
