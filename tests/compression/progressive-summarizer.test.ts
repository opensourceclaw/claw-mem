// Tests for ProgressiveSummarizer — claw-mem v6.4.0

import { describe, it, expect, beforeEach } from "vitest";
import {
  ProgressiveSummarizer,
  COMPRESSION_LEVELS,
} from "../../src/compression/progressive-summarizer";
import type { MemoryRecord } from "../../src/types";

function makeMemory(text: string): MemoryRecord {
  return {
    id: "test-1",
    text,
    memory_type: "episodic",
    created_at: new Date().toISOString(),
    metadata: {},
    tags: [],
  };
}

const sampleMemory = makeMemory(
  "决定：使用 TypeScript 替代 Python 进行开发。Peter 确认了 claw-mem 项目架构方案。" +
  "必须保持 API 向后兼容。该项目使用 Docker 和 Kubernetes 部署。"
);

describe("ProgressiveSummarizer", () => {
  let summarizer: ProgressiveSummarizer;

  beforeEach(() => {
    summarizer = new ProgressiveSummarizer();
  });

  describe("summarize", () => {
    it("should return raw content for L0 target", () => {
      const result = summarizer.summarize(sampleMemory, "L0");
      expect(result.level).toBe("L0");
      expect(result.ratio).toBe(1.0);
      expect(result.method).toBe("raw");
    });

    it("should extract entities and decisions at L0.5", () => {
      const result = summarizer.summarize(sampleMemory, "L0.5");
      expect(result.level).toBe("L0.5");
      expect(result.method).toBe("progressive");
      expect(result.ratio).toBeLessThan(1.0);
      expect(result.entities.length).toBeGreaterThan(0);
      expect(result.decisions.length).toBeGreaterThan(0);
    });

    it("should compress through all levels progressively", () => {
      const l1 = summarizer.summarize(sampleMemory, "L1");
      expect(l1.level).toBe("L1");
      expect(l1.ratio).toBeLessThan(1.0);

      const l2 = summarizer.summarize(sampleMemory, "L2");
      expect(l2.level).toBe("L2");

      const l3 = summarizer.summarize(sampleMemory, "L3");
      expect(l3.level).toBe("L3");
      expect(l3.compressedLength).toBeLessThan(l1.compressedLength);
    });
  });

  describe("canCompress", () => {
    it("should allow L0 for any content", () => {
      expect(summarizer.canCompress(makeMemory(""), "L0")).toBe(true);
    });

    it("should require minimum length for L0.5", () => {
      expect(summarizer.canCompress(makeMemory("短"), "L0.5")).toBe(false);
      expect(summarizer.canCompress(makeMemory("A".repeat(30)), "L0.5")).toBe(true);
    });

    it("should require more content for higher levels", () => {
      expect(summarizer.canCompress(makeMemory("短"), "L3")).toBe(false);
      expect(summarizer.canCompress(makeMemory("A".repeat(200)), "L3")).toBe(true);
    });
  });

  describe("getNextLevel", () => {
    it("should return L0.5 from L0", () => {
      expect(summarizer.getNextLevel("L0")).toBe("L0.5");
    });

    it("should return L3 from L3 (max level)", () => {
      expect(summarizer.getNextLevel("L3")).toBe("L3");
    });

    it("should progress through all levels", () => {
      let level = summarizer.getNextLevel("L0");
      expect(level).toBe("L0.5");
      level = summarizer.getNextLevel(level);
      expect(level).toBe("L1");
      level = summarizer.getNextLevel(level);
      expect(level).toBe("L2");
      level = summarizer.getNextLevel(level);
      expect(level).toBe("L3");
    });
  });

  describe("getAchievableLevels", () => {
    it("should return L0 through L0.5", () => {
      const levels = summarizer.getAchievableLevels("L0.5");
      expect(levels).toHaveLength(2);
      expect(levels[0].level).toBe("L0");
      expect(levels[1].level).toBe("L0.5");
    });
  });

  describe("COMPRESSION_LEVELS", () => {
    it("should have 5 levels in order", () => {
      expect(COMPRESSION_LEVELS).toHaveLength(5);
      expect(COMPRESSION_LEVELS[0].level).toBe("L0");
      expect(COMPRESSION_LEVELS[4].level).toBe("L3");
    });

    it("should have decreasing ratios", () => {
      for (let i = 1; i < COMPRESSION_LEVELS.length; i++) {
        expect(COMPRESSION_LEVELS[i].ratio).toBeLessThan(COMPRESSION_LEVELS[i - 1].ratio);
      }
    });
  });
});
