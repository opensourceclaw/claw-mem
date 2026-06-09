// claw-mem v5.0.0 — Three-Tier Memory Retriever (TypeScript)
//
// Implements cross-layer retrieval across:
//   L1: Working Memory (current session context)
//   L2: Short-term Memory (daily memory records)
//   L3: Long-term Memory (consolidated knowledge)
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

import type { RetrievalResult } from "./base.js";
import { tokenize } from "./keyword.js";

/**
 * Memory layer identifiers.
 */
export enum MemoryLayer {
  L1 = "l1", // Working Memory (current session)
  L2 = "l2", // Short-term Memory (daily files)
  L3 = "l3", // Long-term Memory (consolidated)
}

/**
 * Memory result from a specific layer.
 */
export interface MemoryResult {
  memoryId: string;
  content: string;
  layer: MemoryLayer;
  score: number;
  source: string;
  timestamp?: string;
  tags: string[];
  memoryType: string;
}

/**
 * Topic keywords for intent classification.
 */
const TOPIC_KEYWORDS: Record<string, string[]> = {
  harness_engineering: ["harness", "engineering", "pillar", "agent", "architecture"],
  project_neo: ["neo", "project neo", "multi-agent", "agent system"],
  memory_system: ["memory", "recall", "retrieve", "search", "index"],
  openclaw: ["openclaw", "claude", "assistant", "agent"],
  technical: ["code", "api", "function", "class", "module", "implementation"],
  personal: ["preference", "like", "dislike", "hobby", "interest"],
};

/**
 * Detect topic/intent from a query based on keyword matching.
 *
 * @param query - User query string.
 * @returns Detected topic or undefined.
 */
export function detectIntent(query: string): string | undefined {
  const tokens = tokenize(query);
  const keywordSet = new Set(tokens.map((t) => t.toLowerCase()));

  let bestMatch: string | undefined;
  let bestScore = 0;

  for (const [topic, keywords] of Object.entries(TOPIC_KEYWORDS)) {
    const matches = keywords.filter((kw) => keywordSet.has(kw.toLowerCase())).length;
    const score = matches / keywords.length;
    if (score > bestScore && score >= 0.3) {
      bestScore = score;
      bestMatch = topic;
    }
  }

  return bestMatch;
}

/**
 * Compute relevance score between query and content.
 * Normalized to 0.0 - 1.0.
 */
function computeRelevance(query: string, content: string, _intent?: string): number {
  if (!content) return 0.0;

  const queryLower = query.toLowerCase();
  const contentLower = content.toLowerCase();

  // Exact match score
  const exactMatch = queryLower.length > 0 && contentLower.includes(queryLower) ? 1.0 : 0.0;

  // Keyword match score
  const queryWords = new Set(queryLower.split(/\s+/).filter(Boolean));
  const contentWords = new Set(contentLower.match(/\w+/g) ?? []);
  const keywordMatches = [...queryWords].filter((w) => contentWords.has(w)).length;
  const keywordScore = queryWords.size > 0 ? keywordMatches / queryWords.size : 0;

  // Combined score
  const score = 0.5 * exactMatch + 0.4 * keywordScore;
  return Math.min(score, 1.0);
}

/**
 * Callback types for layer-specific retrieval.
 */
export interface LayerRetrievalContext {
  /** Callback to retrieve L1 (working) memories. */
  getL1Memories?: () => Array<{ id?: string; content: string; timestamp?: string; tags?: string[]; type?: string }>;
  /** Callback to retrieve L2 (short-term) memories. */
  getL2Memories?: () => Array<{ id?: string; content: string; timestamp?: string; tags?: string[]; type?: string }>;
  /** Callback to retrieve L3 (long-term) memories. */
  getL3Memories?: () => Array<{ id?: string; content: string; timestamp?: string; tags?: string[]; type?: string }>;
}

/**
 * Three-Tier Memory Retriever.
 *
 * Provides unified search across L1 (Working), L2 (Short-term), and L3 (Long-term) memory layers.
 */
export class ThreeTierRetriever {
  private searchCount: number = 0;
  private totalLatencyMs: number = 0;
  private lastSearchTime: number = 0;

  /**
   * Cross-layer memory search.
   *
   * @param query - Search query.
   * @param context - Layer retrieval callbacks providing memories per layer.
   * @param layers - Layers to search (default: all three).
   * @param limit - Maximum results.
   * @param memoryType - Optional memory type filter.
   * @param minScore - Minimum relevance score threshold.
   * @returns Ranked, deduplicated memory results.
   */
  search(
    query: string,
    context: LayerRetrievalContext,
    layers: MemoryLayer[] = [MemoryLayer.L1, MemoryLayer.L2, MemoryLayer.L3],
    limit: number = 10,
    memoryType?: string,
    minScore: number = 0.1,
  ): MemoryResult[] {
    const startTime = Date.now();
    const intent = detectIntent(query);

    const allResults: MemoryResult[] = [];

    for (const layer of layers) {
      const layerResults = this.searchLayer(query, layer, context, intent, memoryType, minScore);
      allResults.push(...layerResults);
    }

    // Deduplicate by content
    const seenContent = new Set<string>();
    const unique: MemoryResult[] = [];
    for (const r of allResults) {
      const key = r.content.toLowerCase().trim().slice(0, 100);
      if (!seenContent.has(key)) {
        seenContent.add(key);
        unique.push(r);
      }
    }

    // Sort by score descending
    unique.sort((a, b) => b.score - a.score);

    // Performance tracking
    const latencyMs = Date.now() - startTime;
    this.searchCount++;
    this.totalLatencyMs += latencyMs;
    this.lastSearchTime = Date.now();

    // Log slow searches
    if (latencyMs > 500) {
      console.warn(`Warning: Slow search detected: ${latencyMs}ms for query: ${query.slice(0, 50)}`);
    }

    return unique.slice(0, limit);
  }

  /**
   * Search a specific memory layer.
   */
  private searchLayer(
    query: string,
    layer: MemoryLayer,
    context: LayerRetrievalContext,
    intent?: string,
    memoryType?: string,
    minScore: number = 0.1,
  ): MemoryResult[] {
    let memories: Array<{ id?: string; content: string; timestamp?: string; tags?: string[]; type?: string }> = [];

    if (layer === MemoryLayer.L1 && context.getL1Memories) {
      memories = context.getL1Memories();
    } else if (layer === MemoryLayer.L2 && context.getL2Memories) {
      memories = context.getL2Memories();
    } else if (layer === MemoryLayer.L3 && context.getL3Memories) {
      memories = context.getL3Memories();
    }

    const results: MemoryResult[] = [];

    for (const mem of memories) {
      // Filter by memory type
      if (memoryType && mem.type !== memoryType) continue;

      const score = computeRelevance(query, mem.content ?? "", intent);
      if (score < minScore) continue;

      results.push({
        memoryId: mem.id ?? `${layer}_${results.length}`,
        content: mem.content ?? "",
        layer,
        score,
        source: layer === MemoryLayer.L1 ? "working_memory" : `memory_${layer}`,
        timestamp: mem.timestamp,
        tags: mem.tags ?? [],
        memoryType: mem.type ?? "episodic",
      });
    }

    results.sort((a, b) => b.score - a.score);
    return results;
  }

  /**
   * Get performance statistics.
   */
  getPerformanceStats(): Record<string, unknown> {
    const avgLatency = this.searchCount > 0 ? this.totalLatencyMs / this.searchCount : 0;
    return {
      totalSearches: this.searchCount,
      averageLatencyMs: Math.round(avgLatency * 100) / 100,
      lastSearchTime: this.lastSearchTime > 0 ? new Date(this.lastSearchTime).toISOString() : null,
      performanceTargetMet: avgLatency < 500,
    };
  }
}
