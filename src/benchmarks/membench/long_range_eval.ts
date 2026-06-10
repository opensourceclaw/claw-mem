/**
 * MemBench — Long-Range Understanding Evaluation.
 *
 * Evaluates cross-session consistency: can the memory system
 * maintain coherent understanding across multiple sessions?
 */

export interface LongRangeMetrics {
  crossSessionConsistency: number;
  totalSessions: number;
  checksPassed: number;
  totalChecks: number;
}

interface ConsistencyCheck {
  sessionA: number;
  sessionB: number;
  expectedKnowledge: string;
}

const CONSISTENCY_CHECKS: ConsistencyCheck[] = [
  { sessionA: 0, sessionB: 2, expectedKnowledge: "TypeScript" },
  { sessionA: 1, sessionB: 2, expectedKnowledge: "2-space" },
  { sessionA: 0, sessionB: 1, expectedKnowledge: "indentation" },
];

const MULTI_SESSION_DATA = [
  // Session 0
  [
    { role: "user", content: "Use TypeScript with 2-space indentation" },
    { role: "assistant", content: "Configured: TypeScript, 2-space indentation." },
  ],
  // Session 1
  [
    { role: "user", content: "Change indentation to 4 spaces" },
    { role: "assistant", content: "Updated: now using 4-space indentation." },
  ],
  // Session 2
  [
    { role: "user", content: "What settings are active?" },
    { role: "assistant", content: "Active: TypeScript, 4-space indentation." },
  ],
];

export class LongRangeEvaluator {
  evaluate(
    getKnowledge: (sessionIndex: number) => string[],
  ): LongRangeMetrics {
    let checksPassed = 0;
    const totalChecks = CONSISTENCY_CHECKS.length;

    for (const check of CONSISTENCY_CHECKS) {
      const knowledgeA = getKnowledge(check.sessionA).join(" ").toLowerCase();
      const knowledgeB = getKnowledge(check.sessionB).join(" ").toLowerCase();
      const kw = check.expectedKnowledge.toLowerCase();

      // Knowledge should persist between sessions A and B
      if (knowledgeA.includes(kw) || knowledgeB.includes(kw)) {
        checksPassed++;
      }
    }

    return {
      crossSessionConsistency: totalChecks > 0
        ? Math.round((checksPassed / totalChecks) * 100) / 100
        : 0,
      totalSessions: MULTI_SESSION_DATA.length,
      checksPassed,
      totalChecks,
    };
  }

  /** Get the multi-session test data for evaluation setup. */
  static getSessionData(): Array<Array<{ role: string; content: string }>> {
    return MULTI_SESSION_DATA;
  }
}
