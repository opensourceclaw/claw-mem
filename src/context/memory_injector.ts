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
 * F1: MemoryInjector + InjectorResult
 *
 * Five-stage injection pipeline between retrieval and context formatting:
 *   1. Confidence gate
 *   2. Relevance threshold
 *   3. Diversity dedup (Jaccard similarity)
 *   4. Sort (recency + relevance)
 *   5. Token budget
 */

// ── Word-level Jaccard similarity ─────────────────────────────────────

function _jaccard_similarity(text_a: string, text_b: string): number {
  function _tokenize(text: string): Set<string> {
    const tokens = new Set<string>();
    let i = 0;
    const n = text.length;
    while (i < n) {
      const ch = text[i];
      // CJK characters (U+4E00-U+9FFF) treated as individual tokens
      if (ch >= "\u4e00" && ch <= "\u9fff") {
        tokens.add(ch);
        i++;
      } else if (/[a-zA-Z0-9]/.test(ch)) {
        let j = i;
        while (
          j < n &&
          /[a-zA-Z0-9]/.test(text[j]) &&
          !(text[j] >= "\u4e00" && text[j] <= "\u9fff")
        ) {
          j++;
        }
        tokens.add(text.slice(i, j).toLowerCase());
        i = j;
      } else {
        i++;
      }
    }
    return tokens;
  }

  const setA = _tokenize(text_a);
  const setB = _tokenize(text_b);

  if (setA.size === 0 || setB.size === 0) return 0.0;

  let intersection = 0;
  for (const tok of setA) {
    if (setB.has(tok)) intersection++;
  }
  const union = new Set([...setA, ...setB]);
  return union.size > 0 ? intersection / union.size : 0.0;
}

// ── Token estimation ──────────────────────────────────────────────────

/**
 * Rough token estimator: 1 token ≈ 4 characters of English, 1.5 for CJK.
 */
function estimate_tokens(text: string): number {
  if (!text) return 0;
  let cjkCount = 0;
  let asciiCount = 0;
  for (const ch of text) {
    if (ch >= "\u4e00" && ch <= "\u9fff") {
      cjkCount++;
    } else {
      asciiCount++;
    }
  }
  return Math.ceil(cjkCount * 1.5 + asciiCount / 4);
}

// ── Data classes ──────────────────────────────────────────────────────

export interface InjectorResult {
  refined_memories: Record<string, unknown>[];
  total_candidates: number;
  total_removed: number;
  total_tokens: number;
  max_allowed: number;
  diversity_removed: number;
  threshold_removed: number;
  budget_exceeded: boolean;
  metadata: Record<string, unknown>;

  /** Number of memories that passed all stages. */
  readonly passed: number;
}

// ── MemoryInjector ────────────────────────────────────────────────────

export class MemoryInjector {
  confidence_gate: any;
  max_tokens: number;
  diversity_threshold: number;
  relevance_threshold: number;
  recency_weight: number;
  relevance_weight: number;
  enable_confidence_gate: boolean;

  constructor(
    confidence_gate?: any,
    max_tokens: number = 2000,
    diversity_threshold: number = 0.8,
    relevance_threshold: number = 0.3,
    recency_weight: number = 0.4,
    relevance_weight: number = 0.6,
    enable_confidence_gate: boolean = true,
  ) {
    this.confidence_gate = confidence_gate;
    this.max_tokens = max_tokens;
    this.diversity_threshold = diversity_threshold;
    this.relevance_threshold = relevance_threshold;
    this.recency_weight = recency_weight;
    this.relevance_weight = relevance_weight;
    this.enable_confidence_gate = enable_confidence_gate;
  }

  // ── Public API ─────────────────────────────────────────────────────

  refine(memories: Record<string, unknown>[]): InjectorResult {
    const total = memories.length;
    const stages: Record<string, unknown>[] = [];
    let current = [...memories];

    // Stage 1: Confidence gate
    let removedConf = 0;
    if (this.enable_confidence_gate && this.confidence_gate) {
      const before = current.length;
      current = this.confidence_gate.filter(current);
      removedConf = before - current.length;
      stages.push({
        name: "confidence_gate",
        input_count: before,
        output_count: current.length,
        removed: removedConf,
      });
    } else {
      stages.push({
        name: "confidence_gate",
        input_count: current.length,
        output_count: current.length,
        removed: 0,
        skipped: true,
      });
    }

    // Stage 2: Relevance threshold
    let before = current.length;
    const [afterThreshold, removedThr] = this._apply_relevance_threshold(current);
    current = afterThreshold;
    stages.push({
      name: "relevance_threshold",
      input_count: before,
      output_count: current.length,
      removed: removedThr,
    });

    // Stage 3: Diversity dedup
    before = current.length;
    const [afterDedup, removedDiv] = this._deduplicate_by_diversity(current);
    current = afterDedup;
    stages.push({
      name: "diversity_dedup",
      input_count: before,
      output_count: current.length,
      removed: removedDiv,
    });

    // Stage 4: Sort
    before = current.length;
    current = this._sort_by_recency_and_relevance(current);
    stages.push({
      name: "sort",
      input_count: before,
      output_count: current.length,
      removed: 0,
    });

    // Stage 5: Token budget
    before = current.length;
    const [afterBudget, tokenCount, exceeded] = this._apply_token_budget(current);
    current = afterBudget;
    stages.push({
      name: "token_budget",
      input_count: before,
      output_count: current.length,
      removed: before - current.length,
      tokens: tokenCount,
      max_allowed: this.max_tokens,
      budget_exceeded: exceeded,
    });

    const totalTokens = tokenCount;
    const totalRemoved = total - current.length;

    return {
      refined_memories: current,
      total_candidates: total,
      total_removed: totalRemoved,
      total_tokens: totalTokens,
      max_allowed: this.max_tokens,
      diversity_removed: removedDiv,
      threshold_removed: removedThr,
      budget_exceeded: exceeded,
      metadata: { stages },
      get passed(): number {
        return this.refined_memories.length;
      },
    };
  }

  // ── Stage implementations ──────────────────────────────────────────

  private _apply_relevance_threshold(
    memories: Record<string, unknown>[],
  ): [Record<string, unknown>[], number] {
    const kept: Record<string, unknown>[] = [];
    let removed = 0;
    for (const m of memories) {
      const score = m.score;
      if (score == null) {
        kept.push(m);
      } else if (typeof score === "number" && score >= this.relevance_threshold) {
        kept.push(m);
      } else {
        removed++;
      }
    }
    return [kept, removed];
  }

  private _deduplicate_by_diversity(
    memories: Record<string, unknown>[],
  ): [Record<string, unknown>[], number] {
    if (memories.length <= 1) return [[...memories], 0];

    const sorted = [...memories].sort(
      (a, b) => ((b.score as number) ?? 0.0) - ((a.score as number) ?? 0.0),
    );

    const kept: Record<string, unknown>[] = [];
    let removed = 0;

    for (const m of sorted) {
      const content = (m.content as string) ?? "";
      let isDup = false;
      for (const keptM of kept) {
        const keptContent = (keptM.content as string) ?? "";
        const keptLen = keptContent.length;
        // Fast length-based pre-filter for dedup performance
        if (content.length > 0 && keptLen > 0 && Math.abs(content.length - keptLen) / Math.max(content.length, keptLen) > 0.5) continue;
        const sim = _jaccard_similarity(content, keptContent);
        if (sim >= this.diversity_threshold) {
          isDup = true;
          break;
        }
      }
      if (isDup) {
        removed++;
      } else {
        kept.push(m);
      }
    }
    return [kept, removed];
  }

  private _sort_by_recency_and_relevance(
    memories: Record<string, unknown>[],
  ): Record<string, unknown>[] {
    const now = Date.now() / 1000;

    return [...memories].sort((a, b) => {
      const scoreA = this._composite_score(a, now);
      const scoreB = this._composite_score(b, now);
      return scoreB - scoreA;
    });
  }

  private _composite_score(m: Record<string, unknown>, now: number): number {
    let recency = 0.0;
    const createdAt =
      (m.created_at as string) ?? (m.timestamp as string);
    if (createdAt) {
      try {
        const tsStr = String(createdAt).replace(/[Zz+].*$/, "");
        const dt = new Date(tsStr);
        const ageHours = Math.max(0.0, (now - dt.getTime() / 1000) / 3600.0);
        recency = 1.0 / (1.0 + ageHours / 168.0);
      } catch {
        recency = 0.0;
      }
    }

    let relevance = (m.score as number) ?? 0.0;
    if (typeof relevance !== "number" || isNaN(relevance)) relevance = 0.0;

    return recency * this.recency_weight + relevance * this.relevance_weight;
  }

  private _apply_token_budget(
    memories: Record<string, unknown>[],
  ): [Record<string, unknown>[], number, boolean] {
    const kept: Record<string, unknown>[] = [];
    let total = 0;
    let exceeded = false;

    for (const m of memories) {
      const content = (m.content as string) ?? "";
      const memTokens = estimate_tokens(content);
      if (total + memTokens > this.max_tokens) {
        exceeded = true;
        if (kept.length === 0) {
          kept.push(m);
          total = memTokens;
        }
        break;
      }
      kept.push(m);
      total += memTokens;
    }
    return [kept, total, exceeded];
  }
}
