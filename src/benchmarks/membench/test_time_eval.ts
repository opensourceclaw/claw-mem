/**
 * MemBench — Test-Time Learning Evaluation.
 *
 * Evaluates few-shot learning accuracy: can the memory system
 * learn from a small number of examples and generalize?
 */

export interface TestTimeCase {
  name: string;
  examples: Array<{ input: string; output: string }>;
  testInput: string;
  expectedOutput: string;
}

export interface TestTimeMetrics {
  accuracy: number;
  totalCases: number;
  passed: number;
  details: Array<{ name: string; passed: boolean; similarity: number }>;
}

const TEST_TIME_CASES: TestTimeCase[] = [
  {
    name: "code-style-preference",
    examples: [
      { input: "Write a function", output: "function fn(): void {}" },
      { input: "Create a class", output: "class MyClass {}" },
    ],
    testInput: "Write a method",
    expectedOutput: "method(): void {}",
  },
  {
    name: "error-pattern-recognition",
    examples: [
      { input: "Fix TypeError in auth.ts", output: "Check null checks in auth.ts:23" },
      { input: "Fix TypeError in db.ts", output: "Check null checks in db.ts:45" },
    ],
    testInput: "Fix TypeError in api.ts",
    expectedOutput: "Check null checks in api.ts",
  },
  {
    name: "config-pattern",
    examples: [
      { input: "Set port", output: "PORT=3000" },
      { input: "Set host", output: "HOST=localhost" },
    ],
    testInput: "Set database",
    expectedOutput: "DATABASE=postgres",
  },
];

export class TestTimeEvaluator {
  /** Simple Jaccard word similarity between two strings. */
  private similarity(a: string, b: string): number {
    const aWords = new Set(a.toLowerCase().split(/\s+/));
    const bWords = new Set(b.toLowerCase().split(/\s+/));
    if (aWords.size === 0 || bWords.size === 0) return 0;
    let intersection = 0;
    for (const w of aWords) {
      if (bWords.has(w)) intersection++;
    }
    return intersection / new Set([...aWords, ...bWords]).size;
  }

  evaluate(
    fewShotLearn: (examples: Array<{ input: string; output: string }>, query: string) => string,
  ): TestTimeMetrics {
    const details: Array<{ name: string; passed: boolean; similarity: number }> = [];
    let passed = 0;

    for (const tc of TEST_TIME_CASES) {
      const output = fewShotLearn(tc.examples, tc.testInput);
      const sim = this.similarity(output, tc.expectedOutput);
      const ok = sim >= 0.2;
      if (ok) passed++;
      details.push({ name: tc.name, passed: ok, similarity: Math.round(sim * 100) / 100 });
    }

    return {
      accuracy: Math.round((passed / TEST_TIME_CASES.length) * 100) / 100,
      totalCases: TEST_TIME_CASES.length,
      passed,
      details,
    };
  }
}
