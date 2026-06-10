/**
 * MemoryBenchmarkRunner — unified benchmark execution.
 *
 * Runs MemoryArena and MemBench, collects results, and produces
 * aggregated reports for CI and development use.
 */

import { ArenaEvaluator, ARENA_TASKS } from "./memory_arena/index";
import type { ArenaResult } from "./memory_arena/index";
import {
  RetrievalEvaluator,
  TestTimeEvaluator,
  LongRangeEvaluator,
  ForgettingEvaluator,
} from "./membench/index";
import type {
  RetrievalMetrics,
  TestTimeMetrics,
  LongRangeMetrics,
  ForgettingMetrics,
} from "./membench/index";

export interface BenchmarkReport {
  timestamp: string;
  memoryArena: {
    results: ArenaResult[];
    summary: ReturnType<ArenaEvaluator["summarize"]>;
  } | null;
  memBench: {
    retrieval: RetrievalMetrics | null;
    testTime: TestTimeMetrics | null;
    longRange: LongRangeMetrics | null;
    forgetting: ForgettingMetrics | null;
  };
  overallScore: number;
}

export interface RunnerConfig {
  /** Enable MemoryArena suite */
  arena?: boolean;
  /** Enable MemBench suite */
  membench?: boolean;
}

export const DEFAULT_RUNNER_CONFIG: RunnerConfig = {
  arena: true,
  membench: true,
};

type SearchFn = (query: string, limit: number) => string[];
type StoreFn = (id: string, content: string) => void;
type DeleteFn = (id: string) => boolean;
type FewShotFn = (examples: Array<{ input: string; output: string }>, query: string) => string;
type GetKnowledgeFn = (sessionIndex: number) => string[];

export interface RunnerDeps {
  search: SearchFn;
  store: StoreFn;
  delete: DeleteFn;
  fewShotLearn: FewShotFn;
  getKnowledge: GetKnowledgeFn;
}

export class MemoryBenchmarkRunner {
  private config: RunnerConfig;

  constructor(config?: Partial<RunnerConfig>) {
    this.config = { ...DEFAULT_RUNNER_CONFIG, ...config };
  }

  /** Run all enabled benchmarks. */
  runAll(deps: RunnerDeps): BenchmarkReport {
    const report: BenchmarkReport = {
      timestamp: new Date().toISOString(),
      memoryArena: null,
      memBench: {
        retrieval: null,
        testTime: null,
        longRange: null,
        forgetting: null,
      },
      overallScore: 0,
    };

    let scoreSum = 0;
    let scoreCount = 0;

    // ── MemoryArena ──
    if (this.config.arena) {
      const evaluator = new ArenaEvaluator();
      const recalledPerTask = ARENA_TASKS.map(task =>
        task.sessions.map(session =>
          session.map(() => deps.search(task.description, 5)).flat()
        )
      );
      const results = evaluator.evaluateAll(ARENA_TASKS, recalledPerTask);
      const summary = evaluator.summarize(results);
      report.memoryArena = { results, summary };
      scoreSum += summary.avgKnowledgeRetention;
      scoreCount++;
    }

    // ── MemBench ──
    if (this.config.membench) {
      // Retrieval
      const retEval = new RetrievalEvaluator();
      report.memBench.retrieval = retEval.evaluate(deps.search);
      scoreSum += report.memBench.retrieval.mrr;
      scoreCount++;

      // Test-time learning
      const ttEval = new TestTimeEvaluator();
      report.memBench.testTime = ttEval.evaluate(deps.fewShotLearn);
      scoreSum += report.memBench.testTime.accuracy;
      scoreCount++;

      // Long-range
      const lrEval = new LongRangeEvaluator();
      report.memBench.longRange = lrEval.evaluate(deps.getKnowledge);
      scoreSum += report.memBench.longRange.crossSessionConsistency;
      scoreCount++;

      // Forgetting
      const fgEval = new ForgettingEvaluator();
      report.memBench.forgetting = fgEval.evaluate(
        deps.store, deps.delete, (q) => deps.search(q, 10)
      );
      scoreSum += report.memBench.forgetting.deletionSuccess ? 1 : 0;
      scoreCount++;
    }

    report.overallScore = scoreCount > 0
      ? Math.round((scoreSum / scoreCount) * 100) / 100
      : 0;

    return report;
  }
}
