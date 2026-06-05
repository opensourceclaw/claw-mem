// Tests for CompressionQualityMonitor — claw-mem v6.2.0

import { describe, it, expect, beforeEach } from "vitest";
import {
  CompressionQualityMonitor,
  DEFAULT_MONITOR_CONFIG,
  type TrackedCompression,
  type QualityMetrics,
} from "../../src/compression/compression-quality-monitor";
import type { LLMCompressedMemory } from "../../src/compression/llm-compressor";

function makeResult(overrides?: Partial<LLMCompressedMemory>): LLMCompressedMemory {
  return {
    summary: "用户偏好 TypeScript 开发。",
    originalIds: ["1"],
    originalLength: 100,
    compressedLength: 30,
    ratio: 0.3,
    qualityScore: 0.85,
    method: "llm",
    timestamp: new Date().toISOString(),
    ...overrides,
  };
}

describe("CompressionQualityMonitor", () => {
  let monitor: CompressionQualityMonitor;

  beforeEach(() => {
    monitor = new CompressionQualityMonitor();
  });

  describe("track", () => {
    it("should track a compression result", () => {
      monitor.track(makeResult());
      const stats = monitor.getStats();
      expect(stats.totalCompressed).toBe(1);
      expect(stats.llmCount).toBe(1);
    });

    it("should compute metrics for tracked entries", () => {
      monitor.track(makeResult());
      const history = monitor.getRecentHistory(1);
      expect(history[0].metrics).toBeDefined();
      expect(history[0].metrics.semanticRetention).toBeGreaterThan(0);
      expect(history[0].metrics.compressionRatio).toBeGreaterThan(0);
      expect(history[0].metrics.informationDensity).toBeGreaterThanOrEqual(0);
    });
  });

  describe("getStats", () => {
    it("should return empty stats for fresh monitor", () => {
      const stats = monitor.getStats();
      expect(stats.totalCompressed).toBe(0);
      expect(stats.averageSemanticRetention).toBe(0);
      expect(stats.alerts).toEqual([]);
    });

    it("should aggregate stats correctly", () => {
      monitor.track(makeResult({ method: "llm" }));
      monitor.track(makeResult({ method: "rule", qualityScore: 0.5 }));
      const stats = monitor.getStats();
      expect(stats.totalCompressed).toBe(2);
      expect(stats.llmCount).toBe(1);
      expect(stats.ruleCount).toBe(1);
      expect(stats.averageSemanticRetention).toBeGreaterThan(0);
      expect(stats.llmSuccessRate).toBe(0.5);
    });
  });

  describe("getQualityTrend", () => {
    it("should return empty array for fresh monitor", () => {
      expect(monitor.getQualityTrend()).toEqual([]);
    });

    it("should return trend data after tracking", () => {
      for (let i = 0; i < 5; i++) {
        monitor.track(makeResult({ qualityScore: 0.7 + i * 0.05 }));
      }
      const trends = monitor.getQualityTrend(3);
      expect(trends.length).toBeGreaterThan(0);
      expect(trends[0].avgSemanticRetention).toBeGreaterThan(0);
      expect(trends[0].sampleCount).toBeGreaterThan(0);
    });
  });

  describe("alertLowQuality", () => {
    it("should generate alert for low semantic retention", () => {
      monitor.track(makeResult({ qualityScore: 0.3 }));
      const alerts = monitor.alertLowQuality();
      expect(alerts.length).toBeGreaterThan(0);
      expect(alerts[0].type).toBe("low_semantic");
    });

    it("should generate alert for high compression ratio", () => {
      // ratio = compressedLength / originalLength = 80/100 = 0.8 > 0.6 threshold
      monitor.track(makeResult({ compressedLength: 80, originalLength: 100 }));
      const alerts = monitor.alertLowQuality();
      const highRatioAlerts = alerts.filter((a) => a.type === "high_ratio");
      expect(highRatioAlerts.length).toBeGreaterThan(0);
    });
  });

  describe("recordFeedback", () => {
    it("should update satisfaction score on positive feedback", () => {
      monitor.track(makeResult());
      const history = monitor.getRecentHistory(1);
      const id = history[0].id;
      const before = history[0].metrics.userSatisfaction;

      monitor.recordFeedback(id, true);
      const after = monitor.getRecentHistory(1)[0].metrics.userSatisfaction;
      expect(after).toBeGreaterThan(before);
    });

    it("should decrease satisfaction on negative feedback", () => {
      monitor.track(makeResult());
      const id = monitor.getRecentHistory(1)[0].id;
      const before = monitor.getRecentHistory(1)[0].metrics.userSatisfaction;

      monitor.recordFeedback(id, false);
      const after = monitor.getRecentHistory(1)[0].metrics.userSatisfaction;
      expect(after).toBeLessThan(before);
    });
  });

  describe("acknowledgeAlert", () => {
    it("should mark alert as acknowledged", () => {
      monitor.track(makeResult({ qualityScore: 0.3 }));
      const alerts = monitor.alertLowQuality();
      expect(alerts[0].acknowledged).toBe(false);

      monitor.acknowledgeAlert(alerts[0].id);
      const remaining = monitor.alertLowQuality();
      expect(remaining.length).toBe(0);
    });
  });

  describe("updateConfig", () => {
    it("should update configuration", () => {
      monitor.updateConfig({ semanticRetentionMin: 0.9 });
      monitor.track(makeResult({ qualityScore: 0.85 }));
      const alerts = monitor.alertLowQuality();
      expect(alerts.length).toBeGreaterThan(0);
    });
  });

  describe("DEFAULT_MONITOR_CONFIG", () => {
    it("should have sensible defaults", () => {
      expect(DEFAULT_MONITOR_CONFIG.semanticRetentionMin).toBe(0.7);
      expect(DEFAULT_MONITOR_CONFIG.compressionRatioMax).toBe(0.6);
      expect(DEFAULT_MONITOR_CONFIG.maxHistorySize).toBe(500);
    });
  });
});
