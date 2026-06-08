// claw-mem v5.0.0 — Keyword Retriever (TypeScript)
//
// Provides keyword search via n-gram intersection, BM25 re-ranking,
// and simple substring matching.
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

import { BM25 } from "./bm25.js";
import type { RetrievalResult, RetrievalDocument } from "./base.js";

/**
 * Tokenize text into words (supports English + CJK character extraction).
 */
export function tokenize(text: string): string[] {
  const lower = text.toLowerCase();
  const tokens: string[] = [];

  // English words
  const enTokens = lower.match(/\b\w+\b/g);
  if (enTokens) tokens.push(...enTokens);

  // CJK characters (extract individual chars)
  const cjkTokens = lower.match(/[\u4e00-\u9fff]/g);
  if (cjkTokens) tokens.push(...cjkTokens);

  return tokens;
}

const NGRAM_SIZE = 3;

/**
 * Extract n-grams from text for fuzzy matching.
 */
function extractNgrams(text: string, n: number = NGRAM_SIZE): Set<string> {
  const lower = text.toLowerCase();
  const grams = new Set<string>();
  for (let i = 0; i <= lower.length - n; i++) {
    grams.add(lower.slice(i, i + n));
  }
  return grams;
}

/**
 * Compute Jaccard similarity between two sets.
 */
function jaccardSimilarity(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 && b.size === 0) return 0;
  const intersection = new Set([...a].filter((x) => b.has(x)));
  const union = new Set([...a, ...b]);
  return intersection.size / union.size;
}

/**
 * Keyword retriever using n-gram matching and BM25 re-ranking.
 */
export class KeywordRetriever {
  private bm25: BM25;
  private documents: Map<string, RetrievalDocument> = new Map();

  constructor(k1: number = 1.5, b: number = 0.75) {
    this.bm25 = new BM25(k1, b);
  }

  /**
   * Index documents for retrieval.
   */
  index(documents: RetrievalDocument[]): void {
    for (const doc of documents) {
      this.documents.set(doc.id, doc);
      const tokens = tokenize(doc.text);
      this.bm25.addDocument(doc.id, tokens);
    }
  }

  /**
   * Add a single document to the index.
   */
  addDocument(id: string, text: string, metadata?: Record<string, unknown>): void {
    const doc: RetrievalDocument = { id, text, metadata };
    this.documents.set(id, doc);
    const tokens = tokenize(text);
    this.bm25.addDocument(id, tokens);
  }

  /**
   * Search indexed documents by keyword matching.
   *
   * Uses BM25 scoring with n-gram fallback for fuzzy matches.
   *
   * @param query - Search query.
   * @param limit - Maximum results.
   * @param minScore - Minimum BM25 score threshold.
   * @returns Ranked retrieval results.
   */
  search(query: string, limit: number = 10, minScore: number = 0.0): RetrievalResult[] {
    if (!query.trim()) return [];

    const queryTokens = tokenize(query);
    if (queryTokens.length === 0) return [];

    // Primary: BM25 scoring
    const bm25Scores = this.bm25.getScores(queryTokens);
    const scored: Array<{ id: string; score: number; ngramBoost: number }> = [];

    let idx = 0;
    for (const [docId] of this.documents) {
      const bm25Score = bm25Scores[idx] ?? 0;

      // Secondary: n-gram Jaccard similarity for fuzzy matching
      const doc = this.documents.get(docId);
      let ngramScore = 0;
      if (doc) {
        const queryGrams = extractNgrams(query);
        const docGrams = extractNgrams(doc.text);
        ngramScore = jaccardSimilarity(queryGrams, docGrams);
      }

      // Combined: BM25 primary, n-gram as boost
      const combinedScore = bm25Score + ngramScore * 0.3;

      if (combinedScore > minScore) {
        scored.push({ id: docId, score: combinedScore, ngramBoost: ngramScore });
      }
      idx++;
    }

    // Sort by combined score descending
    scored.sort((a, b) => b.score - a.score);

    // Build results
    return scored.slice(0, limit).map((s) => {
      const doc = this.documents.get(s.id);
      return {
        id: s.id,
        text: doc?.text ?? "",
        score: s.score,
        metadata: doc?.metadata ?? {},
        source: "keyword",
      };
    });
  }

  /**
   * Simple substring match search (no index required).
   *
   * @param query - Search query.
   * @param documents - Documents to search in.
   * @param limit - Maximum results.
   * @returns Matching retrieval results.
   */
  searchExact(query: string, documents: RetrievalDocument[], limit: number = 10): RetrievalResult[] {
    if (!query.trim()) return [];
    const queryLower = query.toLowerCase();
    const results: RetrievalResult[] = [];

    for (const doc of documents) {
      if (doc.text.toLowerCase().includes(queryLower)) {
        results.push({
          id: doc.id,
          text: doc.text,
          score: 1.0,
          metadata: doc.metadata ?? {},
          source: "keyword_exact",
        });
      }
      if (results.length >= limit) break;
    }

    return results;
  }

  /**
   * Clear all indexed documents.
   */
  clear(): void {
    this.bm25.clear();
    this.documents.clear();
  }

  /**
   * Get retriever statistics.
   */
  getStats(): Record<string, unknown> {
    return {
      documentCount: this.documents.size,
      bm25DocCount: this.bm25.documentCount,
      avgDocLen: this.bm25.averageDocumentLength,
    };
  }
}
