// claw-mem v5.0.0 — Retrieval Module (TypeScript)
//
// Package-level re-exports for all retrieval components.
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

export type { RetrievalResult, RetrievalDocument } from "./base";
export { BaseRetriever } from "./base";

export { BM25 } from "./bm25";

export { KeywordRetriever, tokenize } from "./keyword";

export { ThreeTierRetriever, MemoryLayer, detectIntent } from "./three_tier";
export type { MemoryResult, LayerRetrievalContext } from "./three_tier";

export { HybridRouter, QueryType } from "./hybrid_router";

export { QueryCache, getQueryCache, resetQueryCache } from "./query_cache";

export { SynonymExpander, BUILTIN_SYNONYMS } from "./synonym";

// Drift-aware retriever (v6.3.0)
export {
  DriftAwareRetriever,
  DEFAULT_WEIGHT_CONFIG,
  DEFAULT_DRIFT_AWARE_CONFIG,
  type WeightConfig,
  type DriftAwareResult,
  type DriftMode,
  type DriftDetectorLike,
  type DriftAwareConfig,
} from "./drift-aware-retriever";
