import { describe, it, expect, beforeEach } from "vitest";
import { MemoryGovernance, DEFAULT_GOVERNANCE_CONFIG } from "../../src/memory/governance.js";

describe("MemoryGovernance", () => {
  let governance: MemoryGovernance;

  beforeEach(() => {
    governance = new MemoryGovernance();
  });

  describe("select()", () => {
    it("should store high importance memory", () => {
      expect(governance.select(0.8, 0.5)).toBe(true);
    });

    it("should reject low importance memory", () => {
      expect(governance.select(0.1, 0.1)).toBe(false);
    });

    it("should use weighted importance (0.6) over relevance (0.4)", () => {
      // High importance, low relevance should pass with default threshold 0.3
      // 0.8 * 0.6 + 0.1 * 0.4 = 0.52 > 0.3
      expect(governance.select(0.8, 0.1)).toBe(true);

      // Low importance, high relevance might fail
      // 0.2 * 0.6 + 0.9 * 0.4 = 0.48 > 0.3 → still passes
      expect(governance.select(0.2, 0.9)).toBe(true);

      // Very low both should fail
      // 0.2 * 0.6 + 0.2 * 0.4 = 0.2 < 0.3
      expect(governance.select(0.2, 0.2)).toBe(false);
    });

    it("should track stored and rejected counts", () => {
      governance.select(0.8, 0.5);
      governance.select(0.1, 0.1);

      const metrics = governance.getMetrics();
      expect(metrics.stored).toBe(1);
      expect(metrics.rejected).toBe(1);
      expect(metrics.totalDecisions).toBe(2);
    });
  });

  describe("maintain()", () => {
    it("should keep recently accessed memory", () => {
      expect(governance.maintain(5, 3)).toBe("keep");
    });

    it("should refresh frequently accessed memory", () => {
      // Default refreshThreshold = 5
      expect(governance.maintain(20, 10)).toBe("refresh");
    });

    it("should forget old unused memory", () => {
      // Default maxAge = 30, minAccessCount = 1
      expect(governance.maintain(40, 0)).toBe("forget");
    });

    it("should keep old memory with some access", () => {
      // Old but has access count >= minAccessCount
      expect(governance.maintain(40, 1)).toBe("keep");
    });
  });

  describe("metrics", () => {
    it("should track all decision types", () => {
      governance.select(0.8, 0.5); // stored
      governance.select(0.1, 0.1); // rejected
      governance.maintain(5, 3);   // kept
      governance.maintain(20, 10); // refreshed
      governance.maintain(40, 0);  // forgotten

      const metrics = governance.getMetrics();
      expect(metrics.stored).toBe(1);
      expect(metrics.rejected).toBe(1);
      expect(metrics.kept).toBe(1);
      expect(metrics.refreshed).toBe(1);
      expect(metrics.forgotten).toBe(1);
      expect(metrics.totalDecisions).toBe(5);
    });

    it("should reset metrics", () => {
      governance.select(0.8, 0.5);
      governance.maintain(5, 3);

      governance.resetMetrics();
      const metrics = governance.getMetrics();
      expect(metrics.totalDecisions).toBe(0);
    });
  });

  describe("configuration", () => {
    it("should use default config", () => {
      const config = governance.getConfig();
      expect(config).toEqual(DEFAULT_GOVERNANCE_CONFIG);
    });

    it("should accept custom config", () => {
      const custom = new MemoryGovernance({
        importanceThreshold: 0.5,
        maxAge: 60,
      });

      const config = custom.getConfig();
      expect(config.importanceThreshold).toBe(0.5);
      expect(config.maxAge).toBe(60);
      // Other defaults preserved
      expect(config.relevanceThreshold).toBe(DEFAULT_GOVERNANCE_CONFIG.relevanceThreshold);
    });

    it("should update config", () => {
      governance.updateConfig({ maxAge: 90 });
      expect(governance.getConfig().maxAge).toBe(90);
    });
  });
});
