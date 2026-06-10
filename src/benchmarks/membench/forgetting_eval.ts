/**
 * MemBench — Selective Forgetting Evaluation.
 *
 * Evaluates post-deletion residual checking: after deleting a memory,
 * is it truly removed from the system?
 */

export interface ForgettingMetrics {
  deletionSuccess: boolean;
  residualFound: boolean;
  preDeleteCount: number;
  postDeleteCount: number;
}

const TEST_ITEMS = [
  { id: "forget-1", content: "Temporary note: password reset scheduled for Friday" },
  { id: "forget-2", content: "Important: production API key is sk-abc123def456" },
  { id: "forget-3", content: "Temporary: meeting notes from June 2025 quarterly review" },
  { id: "forget-4", content: "Permanent: architecture decision record #42 — use PostgreSQL" },
];

export class ForgettingEvaluator {
  evaluate(
    store: (id: string, content: string) => void,
    deleteFn: (id: string) => boolean,
    search: (query: string) => string[],
  ): ForgettingMetrics {
    // Store all items
    for (const item of TEST_ITEMS) {
      store(item.id, item.content);
    }

    const targetId = "forget-3";
    const preDelete = search("meeting notes");
    const preDeleteCount = preDelete.length;

    // Delete target
    const deleted = deleteFn(targetId);

    // Check residuals
    const postDelete = search("meeting notes");
    const postDeleteCount = postDelete.length;
    const residualFound = postDelete.some((id: string) => id === targetId);

    return {
      deletionSuccess: deleted && !residualFound,
      residualFound,
      preDeleteCount,
      postDeleteCount,
    };
  }
}
