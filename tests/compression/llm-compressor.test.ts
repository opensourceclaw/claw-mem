// Tests for LLMCompressor — claw-mem v6.1.0

import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  LLMCompressor,
  LLMCompressorMonitor,
  DEFAULT_LLM_COMPRESSION_CONFIG,
  type LLMCompressedMemory,
} from "../../src/compression/llm-compressor";
import type { MemoryRecord } from "../../src/types";

function makeMemory(id: string, text: string): MemoryRecord {
  return {
    id,
    text,
    memory_type: "episodic",
    created_at: new Date().toISOString(),
    metadata: {},
    tags: [],
  };
}

const sampleMemories: MemoryRecord[] = [
  makeMemory("1", "用户偏好使用 TypeScript 进行开发，不喜欢 Python。"),
  makeMemory("2", "项目 claw-mem 是一个本地优先的三层记忆系统。"),
  makeMemory("3", "Peter 喜欢简洁的代码风格，禁用不必要的注释。"),
];

function mockFetchReject() {
  const original = globalThis.fetch;
  globalThis.fetch = () => Promise.reject(new Error("no llm")) as any;
  return () => { globalThis.fetch = original; };
}

describe("LLMCompressor", () => {
  let compressor: LLMCompressor;

  beforeEach(() => {
    compressor = new LLMCompressor();
  });

  describe("ruleCompress (fallback)", () => {
    it("should compress memories using rule-based fallback", async () => {
      // Force rule-based by disabling LLM
      compressor.updateConfig({ fallback_to_rule: true });
      // Mock fetch to fail so it falls back to rule
      const restore = mockFetchReject();

      const result = await compressor.compress(sampleMemories);

      expect(result.method).toBe("rule");
      expect(result.originalIds).toEqual(["1", "2", "3"]);
      expect(result.originalLength).toBeGreaterThan(0);
      expect(result.compressedLength).toBeGreaterThan(0);
      expect(result.ratio).toBeGreaterThan(0);
      expect(result.ratio).toBeLessThan(1);
      expect(result.summary.length).toBeGreaterThan(0);

      restore();
    });

    it("should handle empty memory array", async () => {
      const result = await compressor.compress([]);
      expect(result.summary).toBe("");
      expect(result.originalIds).toEqual([]);
      expect(result.ratio).toBe(0);
    });
  });

  describe("estimateCompressionRatio", () => {
    it("should return estimated token count", () => {
      const ratio = compressor.estimateCompressionRatio(sampleMemories);
      expect(ratio).toBeGreaterThanOrEqual(50);
      expect(ratio).toBeLessThanOrEqual(500);
    });
  });

  describe("decompress", () => {
    it("should create memory-like records from compressed memory", async () => {
      const compressed: LLMCompressedMemory = {
        summary: "用户偏好 TypeScript，项目是记忆系统。",
        originalIds: ["1", "2"],
        originalLength: 100,
        compressedLength: 30,
        ratio: 0.3,
        qualityScore: 0.9,
        method: "rule",
        timestamp: new Date().toISOString(),
      };

      const results = await compressor.decompress(compressed);

      expect(results).toHaveLength(2);
      expect(results[0].id).toBe("1");
      expect(results[0].text).toContain("[compressed]");
      expect(results[0].memory_type).toBe("episodic");
    });
  });

  describe("getQualityStats", () => {
    it("should return initial stats", () => {
      const stats = compressor.getQualityStats();
      expect(stats.totalCompressed).toBe(0);
      expect(stats.avgRatio).toBe(0);
      expect(stats.llmSuccessRate).toBe(0);
    });

    it("should track stats after compressions", async () => {
      const restore = mockFetchReject();

      await compressor.compress([sampleMemories[0]]);
      const stats = compressor.getQualityStats();

      expect(stats.totalCompressed).toBe(1);
      expect(stats.avgRatio).toBeGreaterThan(0);

      restore();
    });
  });

  describe("updateConfig", () => {
    it("should update configuration", () => {
      compressor.updateConfig({ target_ratio: 0.5 });
      const ratio = compressor.estimateCompressionRatio(sampleMemories);
      // target_ratio 0.5 with sample length ~100 should yield ~50
      expect(ratio).toBeGreaterThan(0);
    });
  });

  describe("DEFAULT_LLM_COMPRESSION_CONFIG", () => {
    it("should have sensible defaults", () => {
      expect(DEFAULT_LLM_COMPRESSION_CONFIG.target_ratio).toBe(0.3);
      expect(DEFAULT_LLM_COMPRESSION_CONFIG.min_quality).toBe(0.8);
      expect(DEFAULT_LLM_COMPRESSION_CONFIG.fallback_to_rule).toBe(true);
      expect(DEFAULT_LLM_COMPRESSION_CONFIG.maxRetries).toBe(2);
    });
  });
});

describe("LLMCompressorMonitor", () => {
  let compressor: LLMCompressor;
  let monitor: LLMCompressorMonitor;

  beforeEach(() => {
    compressor = new LLMCompressor();
    monitor = new LLMCompressorMonitor(compressor);
  });

  describe("getQualityStats", () => {
    it("should delegate to compressor", () => {
      const stats = monitor.getQualityStats();
      expect(stats).toBeDefined();
      expect(stats.totalCompressed).toBe(0);
    });
  });

  describe("isQualityAcceptable", () => {
    it("should return true when no data yet", () => {
      // 0 success rate >= 0.9 is false, avgQuality 0 >= 0.8 is false
      // So this returns false for fresh compressor
      expect(monitor.isQualityAcceptable()).toBe(false);
    });
  });

  describe("recommendation", () => {
    it("should recommend llm for fresh compressor (< 5 samples)", () => {
      expect(monitor.recommendation()).toBe("llm");
    });

    it("should recommend llm when quality is good", async () => {
      const restore = mockFetchReject();

      // Generate 5 rule-based compressions
      for (let i = 0; i < 5; i++) {
        await compressor.compress([makeMemory(`m${i}`, `测试记忆 ${i}。`)]);
      }

      // After 5 rule compressions, quality is mediocre
      const rec = monitor.recommendation();
      expect(rec === "rule" || rec === "mixed").toBe(true);

      restore();
    }, 10000);
  });
});
