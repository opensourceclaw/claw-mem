// ResultReporter - JSON and Markdown report generation (v6.32.0)

import * as fs from "fs";
import * as path from "path";
import { BenchmarkResult } from "./core.js";

export interface ReportOptions {
  /** Output directory */
  outputDir: string;
  /** Format: json, markdown, both */
  format: "json" | "markdown" | "both";
  /** Baseline file for comparison */
  baseline?: string;
  /** Thresholds for pass/fail */
  thresholds?: Record<string, Record<string, { min?: number; max?: number }>>;
}

export interface ComparisonReport {
  benchmark: string;
  metric: string;
  current: number;
  baseline: number;
  change: number;
  changePercent: number;
  improved: boolean;
}

export class ResultReporter {
  /**
   * Generate reports for all benchmark results.
   */
  static generate(results: BenchmarkResult[], options: ReportOptions): void {
    fs.mkdirSync(options.outputDir, { recursive: true });

    if (options.format === "json" || options.format === "both") {
      const jsonPath = path.join(options.outputDir, "latest.json");
      fs.writeFileSync(jsonPath, this.toJSON(results), "utf-8");
    }

    if (options.format === "markdown" || options.format === "both") {
      const mdPath = path.join(options.outputDir, "report.md");
      fs.writeFileSync(mdPath, this.toMarkdown(results, options), "utf-8");
    }
  }

  /**
   * Compare current results against baseline.
   */
  static compare(current: BenchmarkResult[], baseline: BenchmarkResult[]): ComparisonReport[] {
    const reports: ComparisonReport[] = [];

    for (const curr of current) {
      const base = baseline.find(b => b.name === curr.name);
      if (!base) continue;

      for (const [metric, value] of Object.entries(curr.metrics)) {
        const baseValue = base.metrics[metric];
        if (baseValue === undefined) continue;

        const change = value - baseValue;
        const changePercent = baseValue !== 0 ? (change / Math.abs(baseValue)) * 100 : 0;

        // Determine if improvement (lower is better for latency, higher is better for accuracy)
        const lowerIsBetter = metric.includes("latency") || metric.includes("rate") || metric.includes("cost");
        const improved = lowerIsBetter ? change < 0 : change > 0;

        reports.push({
          benchmark: curr.name,
          metric,
          current: value,
          baseline: baseValue,
          change,
          changePercent,
          improved,
        });
      }
    }

    return reports;
  }

  /**
   * Get version from package.json.
   */
  private static getVersion(): string {
    try {
      // Try two levels up first (compiled: dist/benchmarks/ -> project root)
      let pkgPath = path.resolve(__dirname, "..", "..", "package.json");
      if (!fs.existsSync(pkgPath)) {
        // Fallback to one level up (source: benchmarks/ -> project root)
        pkgPath = path.resolve(__dirname, "..", "package.json");
      }
      return JSON.parse(fs.readFileSync(pkgPath, "utf-8")).version || "unknown";
    } catch {
      return "unknown";
    }
  }

  /**
   * Format as JSON.
   */
  private static toJSON(results: BenchmarkResult[]): string {
    return JSON.stringify({
      version: this.getVersion(),
      timestamp: new Date().toISOString(),
      results,
    }, null, 2);
  }

  /**
   * Format as Markdown.
   */
  private static toMarkdown(results: BenchmarkResult[], options: ReportOptions): string {
    const version = this.getVersion();
    const lines: string[] = [
      `# claw-mem v${version} Benchmark Report`,
      `**Date**: ${new Date().toISOString()}`,
      `**Version**: ${version}`,
      "",
    ];

    for (const result of results) {
      lines.push(`## ${result.name}`);
      lines.push("");
      lines.push("| Metric | Value | Status |");
      lines.push("|--------|-------|:------:|");

      for (const [metric, value] of Object.entries(result.metrics)) {
        // Skip nested objects (strategy breakdown)
        if (typeof value === "object") continue;

        const formatted = typeof value === "number" && value < 10
          ? value.toFixed(4)
          : typeof value === "number"
            ? value.toFixed(2)
            : String(value);

        const status = this.checkThreshold(result.name, metric, value as number, options.thresholds);
        const statusIcon = status === "pass" ? "✅" : status === "fail" ? "❌" : "➖";

        lines.push(`| ${metric} | ${formatted} | ${statusIcon} |`);
      }

      lines.push("");
      lines.push(`**Duration**: ${result.durationMs}ms`);
      lines.push(`**Passed**: ${result.passed ? "✅" : "❌"}`);
      lines.push("");
    }

    return lines.join("\n");
  }

  /**
   * Check if metric passes threshold.
   */
  private static checkThreshold(
    benchmark: string,
    metric: string,
    value: number,
    thresholds?: Record<string, Record<string, { min?: number; max?: number }>>
  ): "pass" | "fail" | "unknown" {
    if (!thresholds) return "unknown";

    const benchmarkThresholds = thresholds[benchmark];
    if (!benchmarkThresholds) return "unknown";

    const threshold = benchmarkThresholds[metric];
    if (!threshold) return "unknown";

    if (threshold.min !== undefined && value < threshold.min) return "fail";
    if (threshold.max !== undefined && value > threshold.max) return "fail";

    return "pass";
  }
}
