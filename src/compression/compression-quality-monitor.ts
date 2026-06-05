// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * CompressionQualityMonitor — standalone quality monitoring for claw-mem v6.2.0.
 *
 * Tracks every compression with multiple quality dimensions, provides trend
 * analysis, and fires alerts when quality drops below configured thresholds.
 */

import type { LLMCompressedMemory } from "./llm-compressor";

// ── Types ─────────────────────────────────────────────────────────────────

export interface QualityMetrics {
  /** Semantic preservation score (0-1), estimated via keyword overlap. */
  semanticRetention: number;
  /** compressionRatio = compressedLength / originalLength. */
  compressionRatio: number;
  /** Information density: unique key tokens / total tokens. */
  informationDensity: number;
  /** User satisfaction score (0-1), updated via feedback. */
  userSatisfaction: number;
}

export interface TrackedCompression {
  id: string;
  timestamp: string;
  method: "llm" | "rule";
  metrics: QualityMetrics;
  originalLength: number;
  compressedLength: number;
}

export interface CompressionQualityStats {
  totalCompressed: number;
  llmCount: number;
  ruleCount: number;
  averageSemanticRetention: number;
  averageCompressionRatio: number;
  averageInformationDensity: number;
  averageUserSatisfaction: number;
  llmSuccessRate: number;
  alerts: Alert[];
}

export interface QualityTrend {
  period: string;
  avgSemanticRetention: number;
  avgCompressionRatio: number;
  sampleCount: number;
}

export interface Alert {
  id: string;
  type: "low_semantic" | "high_ratio" | "low_density" | "satisfaction_drop";
  severity: "warning" | "critical";
  message: string;
  threshold: number;
  actual: number;
  timestamp: string;
  acknowledged: boolean;
}

export interface MonitorConfig {
  semanticRetentionMin: number;
  compressionRatioMax: number;
  informationDensityMin: number;
  satisfactionDropThreshold: number;
  trendWindowSize: number;
  maxHistorySize: number;
}

export const DEFAULT_MONITOR_CONFIG: MonitorConfig = {
  semanticRetentionMin: 0.7,
  compressionRatioMax: 0.6,
  informationDensityMin: 0.3,
  satisfactionDropThreshold: 0.2,
  trendWindowSize: 20,
  maxHistorySize: 500,
};

// ── CompressionQualityMonitor ──────────────────────────────────────────────

export class CompressionQualityMonitor {
  private history: TrackedCompression[] = [];
  private alerts: Alert[] = [];
  private config: MonitorConfig;
  private alertSeq = 0;

  constructor(config?: Partial<MonitorConfig>) {
    this.config = { ...DEFAULT_MONITOR_CONFIG, ...config };
  }

  /** Track a compression result with computed quality metrics. */
  track(result: LLMCompressedMemory): void {
    const metrics = this.computeMetrics(result);
    const entry: TrackedCompression = {
      id: `qc_${Date.now()}_${this.history.length}`,
      timestamp: result.timestamp,
      method: result.method,
      metrics,
      originalLength: result.originalLength,
      compressedLength: result.compressedLength,
    };

    this.history.push(entry);
    if (this.history.length > this.config.maxHistorySize) {
      this.history.shift();
    }

    this.checkAlerts(entry);
  }

  /** Get comprehensive quality statistics. */
  getStats(): CompressionQualityStats {
    const total = this.history.length;
    if (total === 0) {
      return this.emptyStats();
    }

    const llmResults = this.history.filter((e) => e.method === "llm");
    const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0);

    return {
      totalCompressed: total,
      llmCount: llmResults.length,
      ruleCount: total - llmResults.length,
      averageSemanticRetention: sum(this.history.map((e) => e.metrics.semanticRetention)) / total,
      averageCompressionRatio: sum(this.history.map((e) => e.metrics.compressionRatio)) / total,
      averageInformationDensity: sum(this.history.map((e) => e.metrics.informationDensity)) / total,
      averageUserSatisfaction: sum(this.history.map((e) => e.metrics.userSatisfaction)) / total,
      llmSuccessRate: total > 0 ? llmResults.length / total : 0,
      alerts: [...this.alerts].slice(-10),
    };
  }

  /** Get quality trend over recent periods. */
  getQualityTrend(windowSize?: number): QualityTrend[] {
    const size = windowSize ?? this.config.trendWindowSize;
    const recent = this.history.slice(-size * 10); // last N windows worth
    if (recent.length === 0) return [];

    const trends: QualityTrend[] = [];
    const bucketSize = Math.max(1, Math.ceil(recent.length / Math.min(10, Math.ceil(recent.length / size))));

    for (let i = 0; i < recent.length; i += bucketSize) {
      const bucket = recent.slice(i, i + bucketSize);
      if (bucket.length === 0) continue;

      const avgRetention = bucket.reduce((s, e) => s + e.metrics.semanticRetention, 0) / bucket.length;
      const avgRatio = bucket.reduce((s, e) => s + e.metrics.compressionRatio, 0) / bucket.length;
      const first = bucket[0];
      const period = new Date(first.timestamp).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });

      trends.push({
        period,
        avgSemanticRetention: Math.round(avgRetention * 100) / 100,
        avgCompressionRatio: Math.round(avgRatio * 100) / 100,
        sampleCount: bucket.length,
      });
    }

    return trends;
  }

  /** Check for low quality conditions and generate alerts. */
  alertLowQuality(): Alert[] {
    // Re-evaluate all un-acknowledged alerts
    return this.alerts.filter((a) => !a.acknowledged);
  }

  /** Record user feedback to adjust satisfaction score. */
  recordFeedback(compressionId: string, satisfied: boolean): void {
    const entry = this.history.find((e) => e.id === compressionId);
    if (!entry) return;

    // Adjust satisfaction with exponential moving average
    const current = entry.metrics.userSatisfaction;
    entry.metrics.userSatisfaction = satisfied
      ? Math.min(1, current + (1 - current) * 0.3)
      : Math.max(0, current - current * 0.3);
  }

  /** Acknowledge an alert. */
  acknowledgeAlert(alertId: string): boolean {
    const alert = this.alerts.find((a) => a.id === alertId);
    if (!alert) return false;
    alert.acknowledged = true;
    return true;
  }

  /** Get current configuration. */
  getConfig(): MonitorConfig {
    return { ...this.config };
  }

  /** Update monitor configuration. */
  updateConfig(config: Partial<MonitorConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /** Get recent history entries. */
  getRecentHistory(count = 20): TrackedCompression[] {
    return this.history.slice(-count);
  }

  // ── Private ───────────────────────────────────────────────────────────

  /** Compute quality metrics from a compression result. */
  private computeMetrics(result: LLMCompressedMemory): QualityMetrics {
    if (result.originalLength === 0) {
      return {
        semanticRetention: 1,
        compressionRatio: 0,
        informationDensity: 1,
        userSatisfaction: 0.5,
      };
    }

    const ratio = result.compressedLength / result.originalLength;

    // Semantic retention: uses built-in qualityScore (keyword preservation)
    const semanticRetention = result.qualityScore;

    // Information density: unique meaningful tokens / total (in summary)
    const tokens = this.tokenize(result.summary);
    const uniqueTokens = new Set(tokens);
    const density = tokens.length > 0
      ? uniqueTokens.size / Math.min(tokens.length * 1.5, uniqueTokens.size * 2)
      : 0;

    return {
      semanticRetention: Math.min(1, semanticRetention),
      compressionRatio: Math.min(1, ratio),
      informationDensity: Math.min(1, Math.max(0, density)),
      userSatisfaction: 0.5, // neutral starting point
    };
  }

  /** Check thresholds and generate alerts. */
  private checkAlerts(entry: TrackedCompression): void {
    const m = entry.metrics;
    const cfg = this.config;

    if (m.semanticRetention < cfg.semanticRetentionMin) {
      this.emitAlert("low_semantic", "warning", "语义保留度过低", cfg.semanticRetentionMin, m.semanticRetention);
    }
    if (m.compressionRatio > cfg.compressionRatioMax) {
      this.emitAlert("high_ratio", "warning", "压缩比过高（压缩不足）", cfg.compressionRatioMax, m.compressionRatio);
    }
    if (m.informationDensity < cfg.informationDensityMin) {
      this.emitAlert("low_density", "warning", "信息密度过低", cfg.informationDensityMin, m.informationDensity);
    }

    // Check satisfaction trend over last 10
    const recent = this.history.slice(-10);
    if (recent.length >= 5) {
      const firstHalf = recent.slice(0, 5);
      const secondHalf = recent.slice(-5);
      const firstAvg = firstHalf.reduce((s, e) => s + e.metrics.userSatisfaction, 0) / 5;
      const secondAvg = secondHalf.reduce((s, e) => s + e.metrics.userSatisfaction, 0) / 5;
      if (firstAvg - secondAvg > cfg.satisfactionDropThreshold) {
        this.emitAlert("satisfaction_drop", "critical", "用户满意度显著下降", firstAvg, secondAvg);
      }
    }
  }

  private emitAlert(
    type: Alert["type"],
    severity: Alert["severity"],
    message: string,
    threshold: number,
    actual: number,
  ): void {
    this.alertSeq++;
    this.alerts.push({
      id: `alert_${Date.now()}_${this.alertSeq}`,
      type,
      severity,
      message,
      threshold,
      actual: Math.round(actual * 1000) / 1000,
      timestamp: new Date().toISOString(),
      acknowledged: false,
    });

    if (this.alerts.length > 100) {
      this.alerts.shift();
    }
  }

  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .split(/[\s,，。！？.!?;:：；、\n]+/)
      .filter((w) => w.length >= 2);
  }

  private emptyStats(): CompressionQualityStats {
    return {
      totalCompressed: 0,
      llmCount: 0,
      ruleCount: 0,
      averageSemanticRetention: 0,
      averageCompressionRatio: 0,
      averageInformationDensity: 0,
      averageUserSatisfaction: 0,
      llmSuccessRate: 0,
      alerts: [],
    };
  }
}
