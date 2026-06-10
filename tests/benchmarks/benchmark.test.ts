import { describe, it, expect } from "vitest";
import {
  MemoryBenchmarkRunner,
  ArenaEvaluator, ARENA_TASKS,
  RetrievalEvaluator,
  TestTimeEvaluator,
  LongRangeEvaluator,
  ForgettingEvaluator,
} from "../../src/benchmarks/index";

// ── MemoryArena ───────────────────────────────────────────────────────

describe("ArenaEvaluator", () => {
  it("evaluates a single task", () => {
    const evaluator = new ArenaEvaluator();
    const task = ARENA_TASKS[0];
    const recalled = [
      ["max_tokens parameter controls response length default 4096"],
      ["max_tokens is the response length parameter"],
    ];
    const result = evaluator.evaluate(task, recalled);
    expect(result.taskId).toBe(task.id);
    expect(result.knowledgeRetention).toBeGreaterThanOrEqual(0);
    expect(result.completionRate).toBeGreaterThanOrEqual(0);
  });

  it("evaluates all tasks", () => {
    const evaluator = new ArenaEvaluator();
    const recalled = ARENA_TASKS.map(t =>
      t.sessions.map(() => t.expectedKnowledge.map(k => `Found: ${k}`))
    );
    const results = evaluator.evaluateAll(ARENA_TASKS, recalled);
    expect(results).toHaveLength(ARENA_TASKS.length);
  });

  it("summarizes results", () => {
    const evaluator = new ArenaEvaluator();
    const results = ARENA_TASKS.map(t => ({
      taskId: t.id, taskType: t.type,
      completionRate: 1, knowledgeRetention: 1,
      memoryUtilization: 0.8, passed: true,
      details: { totalSessions: 2, knowledgeFound: t.expectedKnowledge, knowledgeMissed: [] },
    }));
    const summary = evaluator.summarize(results);
    expect(summary.totalTasks).toBe(ARENA_TASKS.length);
    expect(summary.passed).toBe(ARENA_TASKS.length);
  });
});

// ── MemBench: Retrieval ───────────────────────────────────────────────

describe("RetrievalEvaluator", () => {
  it("evaluates with mock search", () => {
    const evaluator = new RetrievalEvaluator();
    const result = evaluator.evaluate((query: string, limit: number) => {
      if (query.includes("authentication")) return ["doc-1", "doc-3"];
      if (query.includes("deployment")) return ["doc-2", "doc-4"];
      if (query.includes("memory")) return ["doc-1"];
      return [];
    });
    expect(result.totalQueries).toBe(3);
    expect(result.recallAtK[3]).toBeGreaterThanOrEqual(0);
    expect(result.mrr).toBeGreaterThan(0);
  });
});

// ── MemBench: Test-Time Learning ──────────────────────────────────────

describe("TestTimeEvaluator", () => {
  it("evaluates few-shot learning", () => {
    const evaluator = new TestTimeEvaluator();
    const result = evaluator.evaluate((examples, query) => {
      if (query.includes("method")) return "method(): void {}";
      if (query.includes("TypeError")) return "Check null checks in api.ts";
      if (query.includes("database")) return "DATABASE=postgres";
      return "";
    });
    expect(result.totalCases).toBe(3);
    expect(result.accuracy).toBeGreaterThan(0);
  });
});

// ── MemBench: Long-Range ──────────────────────────────────────────────

describe("LongRangeEvaluator", () => {
  it("evaluates cross-session consistency", () => {
    const evaluator = new LongRangeEvaluator();
    const knowledge = [
      ["TypeScript", "2-space"],
      ["TypeScript", "4-space"],
      ["TypeScript", "4-space"],
    ];
    const result = evaluator.evaluate((i: number) => knowledge[i] || []);
    expect(result.totalSessions).toBe(3);
    expect(result.crossSessionConsistency).toBeGreaterThanOrEqual(0);
  });
});

// ── MemBench: Forgetting ──────────────────────────────────────────────

describe("ForgettingEvaluator", () => {
  it("evaluates selective forgetting", () => {
    const stored: Record<string, string> = {};
    const evaluator = new ForgettingEvaluator();
    const result = evaluator.evaluate(
      (id, content) => { stored[id] = content; },
      (id) => { delete stored[id]; return true; },
      (query) => Object.entries(stored)
        .filter(([, c]) => c.toLowerCase().includes(query.toLowerCase()))
        .map(([id]) => id),
    );
    expect(result.deletionSuccess).toBe(true);
    expect(result.residualFound).toBe(false);
  });
});

// ── Unified Runner ────────────────────────────────────────────────────

describe("MemoryBenchmarkRunner", () => {
  const mockDeps = {
    search: (_q: string, _l: number) => ["result-1"],
    store: (_id: string, _c: string) => {},
    delete: (_id: string) => true,
    fewShotLearn: (_ex: Array<{ input: string; output: string }>, _q: string) => "output",
    getKnowledge: (_i: number) => ["knowledge-1"],
  };

  it("runs all benchmarks", () => {
    const runner = new MemoryBenchmarkRunner();
    const report = runner.runAll(mockDeps);
    expect(report.timestamp).toBeTruthy();
    expect(report.memoryArena).not.toBeNull();
    expect(report.memBench.retrieval).not.toBeNull();
    expect(report.overallScore).toBeGreaterThanOrEqual(0);
  });

  it("runs only arena when configured", () => {
    const runner = new MemoryBenchmarkRunner({ arena: true, membench: false });
    const report = runner.runAll(mockDeps);
    expect(report.memoryArena).not.toBeNull();
    expect(report.memBench.retrieval).toBeNull();
  });
});
