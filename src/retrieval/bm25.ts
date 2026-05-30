// claw-mem v5.0.0 — Pure TypeScript BM25 (TypeScript)
//
// Hand-written BM25 algorithm with zero external dependencies.
// Implements the BM25Okapi scoring function.
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
 * Pure TypeScript BM25 (BM25Okapi variant).
 *
 * Usage:
 *   const bm25 = new BM25();
 *   bm25.addDocument("doc1", ["hello", "world"]);
 *   bm25.addDocument("doc2", ["hello", "foo", "bar"]);
 *   const scores = bm25.getScores(["hello"]);
 */
export class BM25 {
  private k1: number;
  private b: number;
  private docCount: number = 0;
  private avgDocLen: number = 0;
  private docFreqs: Map<string, number> = new Map(); // term -> doc frequency
  private docLengths: Map<string, number> = new Map(); // docId -> length
  private docTerms: Map<string, Map<string, number>> = new Map(); // docId -> term -> count
  private totalTermCount: number = 0;

  constructor(k1: number = 1.5, b: number = 0.75) {
    this.k1 = k1;
    this.b = b;
  }

  /** Number of indexed documents. */
  get documentCount(): number {
    return this.docCount;
  }

  /** Average document length across the corpus. */
  get averageDocumentLength(): number {
    return this.avgDocLen;
  }

  /** Term frequency in the document collection (number of docs containing term). */
  getDocumentFrequency(term: string): number {
    return this.docFreqs.get(term) ?? 0;
  }

  /**
   * Add a document to the index.
   *
   * @param id - Unique document identifier.
   * @param tokens - Tokenized document content.
   */
  addDocument(id: string, tokens: string[]): void {
    const termCounts = new Map<string, number>();
    for (const token of tokens) {
      termCounts.set(token, (termCounts.get(token) ?? 0) + 1);
    }

    this.docTerms.set(id, termCounts);
    this.docLengths.set(id, tokens.length);
    this.totalTermCount += tokens.length;
    this.docCount++;

    // Update document frequencies
    for (const term of termCounts.keys()) {
      this.docFreqs.set(term, (this.docFreqs.get(term) ?? 0) + 1);
    }

    this.avgDocLen = this.docCount > 0 ? this.totalTermCount / this.docCount : 0;
  }

  /**
   * Compute BM25 score for a single query against a single document.
   *
   * @param queryTokens - Tokenized query.
   * @param docId - Document identifier.
   * @returns BM25 score (0 if document not found).
   */
  score(queryTokens: string[], docId: string): number {
    const termCounts = this.docTerms.get(docId);
    if (!termCounts) return 0;

    const docLen = this.docLengths.get(docId) ?? 1;
    let totalScore = 0;

    for (const term of queryTokens) {
      const tf = termCounts.get(term) ?? 0;
      if (tf === 0) continue;

      const df = this.docFreqs.get(term) ?? 0;
      // BM25Okapi IDF: ln((N - n + 0.5) / (n + 0.5) + 1)
      const idf = Math.log((this.docCount - df + 0.5) / (df + 0.5) + 1);

      // BM25 scoring formula
      const numerator = idf * tf * (this.k1 + 1);
      const denominator = tf + this.k1 * (1 - this.b + this.b * (docLen / this.avgDocLen));
      totalScore += numerator / denominator;
    }

    return totalScore;
  }

  /**
   * Get BM25 scores for all indexed documents.
   *
   * @param queryTokens - Tokenized query.
   * @returns Array of scores in insertion order (same order as documents were added).
   */
  getScores(queryTokens: string[]): number[] {
    if (queryTokens.length === 0) return [];
    const scores: number[] = [];
    for (const docId of this.docTerms.keys()) {
      scores.push(this.score(queryTokens, docId));
    }
    return scores;
  }

  /**
   * Check if a document exists in the index.
   */
  hasDocument(docId: string): boolean {
    return this.docTerms.has(docId);
  }

  /**
   * Remove a document from the index.
   */
  removeDocument(docId: string): void {
    const termCounts = this.docTerms.get(docId);
    if (!termCounts) return;

    const docLen = this.docLengths.get(docId) ?? 0;

    // Decrement document frequencies
    for (const term of termCounts.keys()) {
      const currentDf = this.docFreqs.get(term) ?? 0;
      if (currentDf <= 1) {
        this.docFreqs.delete(term);
      } else {
        this.docFreqs.set(term, currentDf - 1);
      }
    }

    this.docTerms.delete(docId);
    this.docLengths.delete(docId);
    this.totalTermCount -= docLen;
    this.docCount--;

    this.avgDocLen = this.docCount > 0 ? this.totalTermCount / this.docCount : 0;
  }

  /**
   * Clear all indexed data.
   */
  clear(): void {
    this.docCount = 0;
    this.avgDocLen = 0;
    this.totalTermCount = 0;
    this.docFreqs.clear();
    this.docLengths.clear();
    this.docTerms.clear();
  }
}
