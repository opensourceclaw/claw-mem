/**
 * MemBench — Retrieval Accuracy Evaluation.
 *
 * Metrics: Recall@K, MRR (Mean Reciprocal Rank), Precision@K.
 */

export interface RetrievalTestCase {
  query: string;
  relevantIds: string[];
  corpus: Array<{ id: string; content: string }>;
}

export interface RetrievalMetrics {
  recallAtK: Record<number, number>;
  mrr: number;
  precisionAtK: Record<number, number>;
  totalQueries: number;
}

const RETRIEVAL_TEST_CASES: RetrievalTestCase[] = [
  {
    query: "authentication configuration",
    relevantIds: ["doc-1", "doc-3"],
    corpus: [
      { id: "doc-1", content: "Authentication: configure OAuth2 with JWT tokens for API security" },
      { id: "doc-2", content: "Database setup: PostgreSQL connection pooling with pgBouncer" },
      { id: "doc-3", content: "Auth module: session management and token refresh strategies" },
      { id: "doc-4", content: "Deployment: Docker container orchestration with Kubernetes" },
    ],
  },
  {
    query: "deployment pipeline CI/CD",
    relevantIds: ["doc-2", "doc-4"],
    corpus: [
      { id: "doc-1", content: "TypeScript configuration for strict mode compilation" },
      { id: "doc-2", content: "CI/CD pipeline: GitHub Actions workflow for automated deployment" },
      { id: "doc-3", content: "Testing: unit tests with vitest and integration tests" },
      { id: "doc-4", content: "Deployment pipeline: build, test, deploy stages with rollback support" },
    ],
  },
  {
    query: "memory optimization caching",
    relevantIds: ["doc-1"],
    corpus: [
      { id: "doc-1", content: "Memory optimization: LRU caching with TTL-based eviction for search results" },
      { id: "doc-2", content: "API design: RESTful endpoints with pagination and filtering" },
    ],
  },
];

export class RetrievalEvaluator {
  /**
   * Evaluate retrieval accuracy using a search function.
   *
   * @param search - Search function (query, limit) => result IDs
   * @param kValues - K values for Recall@K (default: [1, 3, 5])
   */
  evaluate(
    search: (query: string, limit: number) => string[],
    kValues: number[] = [1, 3, 5],
  ): RetrievalMetrics {
    const tests = RETRIEVAL_TEST_CASES;
    const recallSum: Record<number, number> = {};
    const precisionSum: Record<number, number> = {};
    let mrrSum = 0;

    for (const kv of kValues) {
      recallSum[kv] = 0;
      precisionSum[kv] = 0;
    }

    for (const test of tests) {
      const results = search(test.query, Math.max(...kValues));
      const relevantSet = new Set(test.relevantIds);

      for (const kv of kValues) {
        const topK = results.slice(0, kv);
        const hits = topK.filter(id => relevantSet.has(id)).length;
        recallSum[kv] += hits / Math.max(1, test.relevantIds.length);
        precisionSum[kv] += hits / Math.max(1, kv);
      }

      // MRR: reciprocal of first relevant result rank
      let rr = 0;
      for (let i = 0; i < results.length; i++) {
        if (relevantSet.has(results[i])) {
          rr = 1 / (i + 1);
          break;
        }
      }
      mrrSum += rr;
    }

    const n = tests.length;
    const recallAtK: Record<number, number> = {};
    const precisionAtK: Record<number, number> = {};
    for (const kv of kValues) {
      recallAtK[kv] = Math.round((recallSum[kv] / n) * 1000) / 1000;
      precisionAtK[kv] = Math.round((precisionSum[kv] / n) * 1000) / 1000;
    }

    return {
      recallAtK,
      mrr: Math.round((mrrSum / n) * 1000) / 1000,
      precisionAtK,
      totalQueries: n,
    };
  }
}
