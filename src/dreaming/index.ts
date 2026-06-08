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
 * claw-mem dreaming module -- Dreaming Engine (v4.12.0)
 *
 * Orchestrates the light->deep->REM->promote pipeline for memory
 * consolidation, pattern extraction, and long-term storage promotion.
 */

export {
  DEFAULT_DREAMING_CONFIG,
  validateDreamingConfig,
  type DreamingConfig,
} from "./config.js";

export {
  SignalIngestor,
  createSignal,
  signalToDict,
  type Signal,
  type MemoryManagerLike,
} from "./light.js";

export {
  CandidateScorer,
  createScoredCandidate,
  scoredCandidateToDict,
  type ScoredCandidate,
} from "./deep.js";

export {
  PatternExtractor,
  createREMResult,
  remResultToDict,
  type REMResult,
  type Triplet,
} from "./rem.js";

export {
  DreamingPipeline,
  createDreamingResult,
  dreamingResultToDict,
  type DreamingResult,
} from "./pipeline.js";

export {
  Promoter,
  createPromotionResult,
  promotionTotal,
  promotionResultToDict,
  type PromotionResult,
  type MemoryManagerWithStorage,
} from "./promote.js";
