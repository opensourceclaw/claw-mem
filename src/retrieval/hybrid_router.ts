// claw-mem v5.0.0 — Hybrid Query Router (TypeScript)
//
// Classifies incoming queries into FACT / SEMANTIC / RELATION types and
// routes them through the optimal retrieval pipeline for each category.
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

/** Query classification types. */
export enum QueryType {
  FACT = "fact",
  SEMANTIC = "semantic",
  RELATION = "relation",
}

// ── Rule-based classification patterns ───────────────────────────────────────

const FACT_PATTERNS_ZH = new Set([
  "密码", "设置", "配置", "是谁", "在哪里", "什么时候", "多少个", "哪个",
  "什么", "谁", "哪里", "何时", "日期", "时间", "地址", "位置", "电话",
]);
const FACT_PATTERNS_EN = new Set([
  "password", "setting", "config", "who", "where", "when", "how many",
  "what is", "is the", "are the", "which",
]);
const SEMANTIC_PATTERNS_ZH = new Set([
  "怎么", "为什么", "解释", "讨论", "方案", "分析", "总结", "评估",
  "如何", "怎么样", "探讨", "建议", "规划", "设计", "实现", "优化",
  "改进", "修复", "解决", "指南", "教程", "原理", "流程",
]);
const SEMANTIC_PATTERNS_EN = new Set([
  "how", "why", "explain", "discuss", "analyze", "describe", "evaluate",
  "summarize", "suggest", "recommend", "design", "implement", "optimize",
  "improve", "fix", "solve", "guide", "tutorial", "principle", "approach",
  "strategy",
]);
const RELATION_PATTERNS_ZH = new Set([
  "关系", "关联", "区别", "比较", "vs", "联系", "和", "与",
  "连接", "依赖", "影响", "对比",
]);
const RELATION_PATTERNS_EN = new Set([
  "relation", "relationship", "link", "connection", "vs", "versus",
  "compare", "difference", "between", "depend", "affect", "contrast",
  "correlation",
]);

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Check if text contains CJK characters. */
function hasCJK(text: string): boolean {
  return /[\u4e00-\u9fff\u3040-\u309f\uac00-\ud7af]/.test(text);
}

/**
 * Simple Chinese tokenization (character-level fallback without jieba).
 */
function tokenizeZH(text: string): string[] {
  const tokens: string[] = [];
  let buf = "";
  for (const ch of text) {
    if (hasCJK(ch)) {
      if (buf) {
        tokens.push(buf);
        buf = "";
      }
      tokens.push(ch);
    } else if (/\s/.test(ch)) {
      if (buf) {
        tokens.push(buf);
        buf = "";
      }
    } else {
      buf += ch;
    }
  }
  if (buf) tokens.push(buf);
  return tokens;
}

/**
 * Match query tokens against a pattern set.
 * For CJK, uses token-list membership to avoid substring false matches.
 */
function matchPatterns(query: string, patternsZH: Set<string>, patternsEN: Set<string>): boolean {
  const queryLower = query.toLowerCase();
  const isCJK = hasCJK(query);

  if (isCJK) {
    const tokens = tokenizeZH(query);
    // Check exact token membership (for single CJK chars)
    for (const pat of patternsZH) {
      if (tokens.includes(pat)) return true;
    }
    // Fallback: check multi-character patterns as substrings
    // This handles cases where jieba-like tokenization is unavailable
    // and multi-char patterns (e.g. "什么时候") would not match individual chars.
    for (const pat of patternsZH) {
      if (pat.length > 1 && query.includes(pat)) return true;
    }
  }

  for (const pat of patternsEN) {
    if (queryLower.includes(pat)) return true;
  }

  return false;
}

/**
 * HybridRouter — routes queries through optimal retrieval pipelines.
 *
 * Usage:
 *   const router = new HybridRouter();
 *   const qtype = router.classify("how to fix memory leak");
 *   // -> QueryType.SEMANTIC
 */
export class HybridRouter {
  /**
   * Classify query into FACT, SEMANTIC, or RELATION.
   *
   * Priority: FACT > RELATION > SEMANTIC (default).
   */
  classify(query: string): QueryType {
    const stripped = query.trim();
    if (!stripped) return QueryType.SEMANTIC;

    // Check FACT patterns first (highest priority)
    if (matchPatterns(stripped, FACT_PATTERNS_ZH, FACT_PATTERNS_EN)) {
      return QueryType.FACT;
    }

    // Check RELATION patterns
    if (matchPatterns(stripped, RELATION_PATTERNS_ZH, RELATION_PATTERNS_EN)) {
      return QueryType.RELATION;
    }

    // Check SEMANTIC patterns
    if (matchPatterns(stripped, SEMANTIC_PATTERNS_ZH, SEMANTIC_PATTERNS_EN)) {
      return QueryType.SEMANTIC;
    }

    // Default
    return QueryType.SEMANTIC;
  }

  /**
   * Route a query through the optimal pipeline.
   *
   * @param query - Search query.
   * @param factSearch - Callback for fact-style search.
   * @param semanticSearch - Callback for semantic-style search.
   * @param relationSearch - Callback for relation-style search.
   * @param limit - Maximum results.
   * @returns Results from the chosen pipeline.
   */
  route<T>(
    query: string,
    factSearch: (query: string, limit: number) => T[],
    semanticSearch: (query: string, limit: number) => T[],
    relationSearch: (query: string, limit: number) => T[],
    limit: number = 10,
  ): T[] {
    const qtype = this.classify(query);

    switch (qtype) {
      case QueryType.FACT:
        return factSearch(query, limit);
      case QueryType.SEMANTIC:
        return semanticSearch(query, limit);
      case QueryType.RELATION:
        return relationSearch(query, limit);
    }
  }
}
