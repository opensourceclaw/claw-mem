/**
 * claw-mem v6.43.0 — MemoryContextBridge
 * Bridges TranscriptStorage with claw-ctx for context-aware memory management.
 */

import * as fs from "fs";
import type {
  MemoryContextReport,
  CompressionRecommendation,
  CompressionResult,
  ContextTaskType,
} from "./types.js";
import { TruncateStrategy, SummarizeStrategy } from "../compression/CompressionStrategy.js";
import type { CompressionStrategy } from "../compression/CompressionStrategy.js";

export class MemoryContextBridge {
  private ctxEngine: any = null;
  private detector: any = null;
  private budgetManager: any = null;
  private timers: Map<string, ReturnType<typeof setInterval>> = new Map();
  private listeners: Map<string, Function[]> = new Map();
  private strategies: Map<string, CompressionStrategy> = new Map();

  constructor() {
    // Try to load claw-ctx; graceful degradation if unavailable
    try {
      // Dynamic import attempt — if claw-ctx is available, use it
      this.initClawCtx();
    } catch {
      // claw-ctx not available, use fallback defaults
    }
    this.strategies.set("truncate", new TruncateStrategy());
    this.strategies.set("summarize", new SummarizeStrategy());
  }

  setContextEngine(ctxEngine: any): void {
    this.ctxEngine = ctxEngine;
  }

  /**
   * Report memory size and check budget.
   */
  reportMemorySize(sessionId: string, filePath: string): MemoryContextReport {
    const stats = fs.statSync(filePath);
    const content = fs.readFileSync(filePath, "utf-8");
    const entryCount = (content.match(/\*\*User\*\*|\*\*Assistant\*\*/g) || []).length;

    const report: MemoryContextReport = {
      sessionId,
      filePath,
      totalBytes: stats.size,
      tokenEstimate: this.estimateTokens(content),
      entryCount,
      oldestEntry: undefined,
      newestEntry: new Date(stats.mtime),
    };

    // Check budget if claw-ctx available
    try {
      const taskType = this.detectTaskType(content);
      const budget = this.budgetManager?.getBudget(taskType);
      const maxTokens = budget?.maxTokens ?? 10000;
      if (report.tokenEstimate >= maxTokens * 0.8) {
        report.compressionRecommendation = {
          shouldCompact: true,
          reason: `Memory approaching limit (${report.tokenEstimate}/${maxTokens} tokens)`,
          targetTokens: Math.floor(maxTokens * 0.5),
          taskType,
          strategy: this.selectStrategy(taskType),
        };
      }
    } catch {
      // Budget check failed — skip recommendation
    }

    return report;
  }

  /**
   * Start periodic memory reporting.
   */
  startPeriodicReporting(sessionId: string, intervalMs: number = 30000): void {
    this.stopPeriodicReporting(sessionId);
    const timer = setInterval(() => {
      try {
        const filePath = this.getMemoryFilePath(sessionId);
        const report = this.reportMemorySize(sessionId, filePath);
        this.emit("memory-report", report);
      } catch {
        // Non-blocking
      }
    }, intervalMs);
    this.timers.set(sessionId, timer);
  }

  /**
   * Stop periodic reporting for a session.
   */
  stopPeriodicReporting(sessionId: string): void {
    const timer = this.timers.get(sessionId);
    if (timer) { clearInterval(timer); this.timers.delete(sessionId); }
  }

  /**
   * Execute compression using the specified strategy.
   */
  async executeCompression(
    sessionId: string,
    strategy: string,
    targetTokens: number,
    filePath?: string
  ): Promise<CompressionResult> {
    try {
      const fp = filePath || this.getMemoryFilePath(sessionId);
      const original = fs.readFileSync(fp, "utf-8");
      const originalTokens = this.estimateTokens(original);

      const strat = this.strategies.get(strategy);
      if (!strat) return { strategy: "truncate", originalTokens, newTokens: originalTokens, savedTokens: 0, error: `Unknown strategy: ${strategy}` };

      const compressed = await strat.compress(original, targetTokens);
      const newTokens = this.estimateTokens(compressed);

      return { strategy: strategy as any, originalTokens, newTokens, savedTokens: originalTokens - newTokens };
    } catch (err) {
      return { strategy: "truncate", originalTokens: 0, newTokens: 0, savedTokens: 0, error: err instanceof Error ? err.message : "unknown" };
    }
  }

  // ── Events ──────────────────────────────────────────────────────

  on(event: string, listener: Function): void {
    const list = this.listeners.get(event) || [];
    list.push(listener);
    this.listeners.set(event, list);
  }

  emit(event: string, data: any): void {
    const list = this.listeners.get(event) || [];
    for (const fn of list) {
      try { fn(data); } catch { /* listener error non-blocking */ }
    }
  }

  // ── Private ─────────────────────────────────────────────────────

  /**
   * Estimate token count from content using ~4 chars per token heuristic.
   * This is an approximation. For accurate counts use tiktoken or claw-ctx token counter.
   * Limitations: non-English text (CJK), code symbols, mixed content.
   */
  private estimateTokens(content: string): number {
    return Math.ceil(content.length / 4);
  }

  private detectTaskType(_content: string): ContextTaskType {
    if (this.detector?.detectTaskType) {
      try { return this.detector.detectTaskType(_content); } catch { /* fallthrough */ }
    }
    return "simple_lookup";
  }

  private selectStrategy(taskType: ContextTaskType): "truncate" | "summarize" | "compress" {
    switch (taskType) {
      case "simple_lookup":
      case "multi_lookup":
        return "truncate";
      case "summarization":
        return "summarize";
      case "complex_reasoning":
        return "compress";
      default:
        return "truncate";
    }
  }

  private getMemoryFilePath(sessionId: string): string {
    return `transcripts/session-${sessionId}.md`;
  }

  private initClawCtx(): void {
    // Placeholder for dynamic claw-ctx import
    // In production: const { ContextTaskDetector, ContextBudgetManager } = await import('@opensourceclaw/claw-ctx');
  }
}
