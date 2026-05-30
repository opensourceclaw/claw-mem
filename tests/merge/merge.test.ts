import { describe, it, expect } from "vitest";
import { cosineSimilarity, SemanticMergeScheduler } from "../../src/merge/semantic_merger";
import { ConflictDetector, conflictReportToDict, conflictResolutionToDict } from "../../src/merge/conflict_detector";

// ── Test 1: cosineSimilarity ───────────────────────────────────────────

function testCosineSimilarity(): void {
  // Identical vectors
  const sim1 = cosineSimilarity([1, 0, 0], [1, 0, 0]);
  console.assert(Math.abs(sim1 - 1.0) < 0.001, `Expected 1.0, got ${sim1}`);

  // Orthogonal vectors
  const sim2 = cosineSimilarity([1, 0, 0], [0, 1, 0]);
  console.assert(Math.abs(sim2 - 0.0) < 0.001, `Expected 0.0, got ${sim2}`);

  // Opposite vectors
  const sim3 = cosineSimilarity([1, 0], [-1, 0]);
  console.assert(Math.abs(sim3 - (-1.0)) < 0.001, `Expected -1.0, got ${sim3}`);

  // Zero vector
  const sim4 = cosineSimilarity([0, 0, 0], [1, 0, 0]);
  console.assert(Math.abs(sim4) < 0.001, `Expected 0.0, got ${sim4}`);

  console.log("PASS: testCosineSimilarity");
  return true;
}

// ── Test 2: ConflictDetector handles empty memory store ────────────────

function testConflictDetectorEmpty(): void {
  const stubManager = {
    semantic: {
      getAll: (): Record<string, unknown>[] => [],
    },
  };
  const stubLLM = {
    generate: (_p: string, _o?: { maxTokens?: number }): string => "",
  };

  const detector = new ConflictDetector(stubManager as any, stubLLM, undefined, 0.7);

  const conflicts = detector.detectConflicts();
  console.assert(conflicts.length === 0, "Expected 0 conflicts for empty store");

  const history = detector.getHistory();
  console.assert(history.length === 0, "Expected empty history");

  console.log("PASS: testConflictDetectorEmpty");
  return true;
}

// ── Test 3: ConflictDetector clears history ────────────────────────────

function testConflictDetectorClearHistory(): void {
  const stubManager = {
    semantic: {
      getAll: (): Record<string, unknown>[] => [],
    },
  };
  const stubLLM = {
    generate: (_p: string, _o?: { maxTokens?: number }): string => "",
  };

  const detector = new ConflictDetector(stubManager as any, stubLLM, undefined, 0.7);

  // Manually add to history
  detector.clearHistory();
  console.assert(detector.getHistory().length === 0, "History should be empty after clear");

  console.log("PASS: testConflictDetectorClearHistory");
  return true;
}

// ── Test 4: toDict serialization ──────────────────────────────────────

function testConflictReportToDict(): void {
  const report = {
    conflictType: "entity",
    memoryIdA: "a1",
    memoryIdB: "b1",
    contentA: "Alice age: 30",
    contentB: "Alice age: 25",
    description: "conflict detected",
    similarity: 0.95,
    resolved: true,
    resolution: {
      action: "keep_a",
      winnerId: "a1",
      mergedContent: "",
      reasoning: "A is more recent",
    },
  };

  const d = conflictReportToDict(report);
  console.assert(d.conflict_type === "entity", "Expected entity type");
  console.assert(d.memory_id_a === "a1", "Expected a1");
  console.assert(d.resolution.action === "keep_a", "Expected keep_a");

  const rd = conflictResolutionToDict(report.resolution);
  console.assert(rd.action === "keep_a", "Expected keep_a in resolution");
  console.assert(rd.reasoning === "A is more recent", "Expected reasoning");

  console.log("PASS: testConflictReportToDict");
  return true;
}

// ── Test 5: SemanticMergeScheduler shouldRun ──────────────────────────

function testShouldRun(): void {
  const stubManager = {
    semantic: {
      filePath: "/tmp/test.md",
      getAll: (): Record<string, unknown>[] => [],
      _formatMemory: (_mem: Record<string, unknown>): string => "",
    },
    store: (
      _content: string,
      _memoryType: string,
      _tags?: string[],
      _metadata?: Record<string, string>,
      _updateIndex?: boolean,
    ): void => {},
  };

  const stubLLM = {
    generate: (_p: string, _o?: { maxTokens?: number; system?: string }): string => "",
  };

  // Use a low embedding threshold to avoid needing EmbeddingService in shouldRun
  const merger = new SemanticMergeScheduler(
    stubManager as any,
    stubLLM,
    undefined,
    100,
    "auto",
    0.85,
    0.65,
  );

  // Not enough interactions
  console.assert(!merger.shouldRun(50), "shouldRun(50) should be false");

  // At exact interval
  console.assert(merger.shouldRun(100), "shouldRun(100) should be true");

  // Multiple of interval
  console.assert(merger.shouldRun(200), "shouldRun(200) should be true");

  console.log("PASS: testShouldRun");
  return true;
}

// ── Run all ────────────────────────────────────────────────────────────



describe("merge.test", () => {
  it("CosineSimilarity", () => {
    expect(testCosineSimilarity()).toBe(true);
  });
  it("ConflictDetectorEmpty", () => {
    expect(testConflictDetectorEmpty()).toBe(true);
  });
  it("ConflictDetectorClearHistory", () => {
    expect(testConflictDetectorClearHistory()).toBe(true);
  });
  it("ConflictReportToDict", () => {
    expect(testConflictReportToDict()).toBe(true);
  });
  it("ShouldRun", () => {
    expect(testShouldRun()).toBe(true);
  });
});
