/**
 * MemoryArena evaluator — scores multi-session cross-domain task performance.
 */

import type { ArenaTask } from "./tasks";

export interface ArenaResult {
  taskId: string;
  taskType: string;
  completionRate: number;
  knowledgeRetention: number;
  memoryUtilization: number;
  passed: boolean;
  details: {
    totalSessions: number;
    knowledgeFound: string[];
    knowledgeMissed: string[];
  };
}

export class ArenaEvaluator {
  /**
   * Evaluate a single task against the memory manager results.
   *
   * @param task - The task definition
   * @param recalledMemories - Memories recalled from claw-mem across sessions
   * @returns Evaluation result
   */
  evaluate(task: ArenaTask, recalledMemories: string[][]): ArenaResult {
    const totalSessions = task.sessions.length;
    let knowledgeFound: string[] = [];
    const knowledgeMissed: string[] = [];

    // Aggregate all recalled content across sessions
    const allRecalled = recalledMemories.flat().join(" ").toLowerCase();

    // Check knowledge retention
    for (const kw of task.expectedKnowledge) {
      if (allRecalled.includes(kw.toLowerCase())) {
        knowledgeFound.push(kw);
      } else {
        knowledgeMissed.push(kw);
      }
    }

    const knowledgeRetention = task.expectedKnowledge.length > 0
      ? knowledgeFound.length / task.expectedKnowledge.length
      : 0;

    // Completion: how many sessions had at least one recall
    const sessionsWithRecall = recalledMemories.filter(r => r.length > 0).length;
    const completionRate = totalSessions > 0
      ? sessionsWithRecall / totalSessions
      : 0;

    // Memory utilization: average recalls per session
    const totalRecalls = recalledMemories.reduce((s, r) => s + r.length, 0);
    const memoryUtilization = totalSessions > 0
      ? Math.min(1, totalRecalls / (totalSessions * 3))
      : 0;

    const overallScore = (completionRate * 0.3 + knowledgeRetention * 0.5 + memoryUtilization * 0.2);
    const passed = overallScore >= task.threshold;

    return {
      taskId: task.id,
      taskType: task.type,
      completionRate: Math.round(completionRate * 100) / 100,
      knowledgeRetention: Math.round(knowledgeRetention * 100) / 100,
      memoryUtilization: Math.round(memoryUtilization * 100) / 100,
      passed,
      details: {
        totalSessions,
        knowledgeFound,
        knowledgeMissed,
      },
    };
  }

  /** Evaluate all tasks. */
  evaluateAll(tasks: ArenaTask[], recalledPerTask: string[][][]): ArenaResult[] {
    return tasks.map((task, i) =>
      this.evaluate(task, recalledPerTask[i] || [])
    );
  }

  /** Aggregate results into summary. */
  summarize(results: ArenaResult[]): {
    totalTasks: number;
    passed: number;
    failed: number;
    avgKnowledgeRetention: number;
    avgCompletionRate: number;
  } {
    const total = results.length;
    const passed = results.filter(r => r.passed).length;
    return {
      totalTasks: total,
      passed,
      failed: total - passed,
      avgKnowledgeRetention: total > 0
        ? results.reduce((s, r) => s + r.knowledgeRetention, 0) / total
        : 0,
      avgCompletionRate: total > 0
        ? results.reduce((s, r) => s + r.completionRate, 0) / total
        : 0,
    };
  }
}
