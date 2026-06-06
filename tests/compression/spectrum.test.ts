import { describe, it, expect } from "vitest";
import { CompressionSpectrum } from "../../src/compression/spectrum";

describe("CompressionSpectrum", () => {
  describe("constructor", () => {
    it("creates with default thresholds", () => {
      const spectrum = new CompressionSpectrum();
      const stats = spectrum.getStats();
      expect(stats.thresholds.skill_access).toBe(5);
      expect(stats.thresholds.rule_apply).toBe(3);
      expect(stats.thresholds.principle_verify).toBe(2);
    });

    it("creates with custom thresholds", () => {
      const spectrum = new CompressionSpectrum(undefined, 10, 5, 3);
      const stats = spectrum.getStats();
      expect(stats.thresholds.skill_access).toBe(10);
      expect(stats.thresholds.rule_apply).toBe(5);
      expect(stats.thresholds.principle_verify).toBe(3);
    });

    it("accepts memory manager", () => {
      const mm = {
        get: (_id: string) => ({ content: "test content" }),
      };
      const spectrum = new CompressionSpectrum(mm);
      expect(spectrum).toBeDefined();
    });
  });

  describe("recordAccess", () => {
    it("increments access count and triggers compression at threshold", () => {
      const content = "install package\nconfigure settings\nrun tests";
      const mm = {
        get: (_id: string) => ({ content }),
      };
      const spectrum = new CompressionSpectrum(mm, 2); // threshold 2
      
      // First access - below threshold
      const result1 = spectrum.recordAccess("ep1");
      expect(result1).toBeUndefined();
      
      // Second access - at threshold
      const result2 = spectrum.recordAccess("ep1");
      expect(result2).toBeDefined();
      expect(result2?.level).toBe(1);
      expect(result2?.metadata.type).toBe("skill");
    });

    it("returns undefined below threshold", () => {
      const spectrum = new CompressionSpectrum(undefined, 5);
      const result = spectrum.recordAccess("ep1");
      expect(result).toBeUndefined();
    });

    it("returns undefined when no memory manager", () => {
      const spectrum = new CompressionSpectrum(undefined, 1);
      const result = spectrum.recordAccess("nonexistent");
      expect(result).toBeUndefined();
    });

    it("returns undefined when content not found", () => {
      const mm = { get: (_id: string) => undefined };
      const spectrum = new CompressionSpectrum(mm, 1);
      const result = spectrum.recordAccess("nonexistent");
      expect(result).toBeUndefined();
    });

    it("returns undefined when content has less than 2 extractable steps", () => {
      const mm = { get: (_id: string) => ({ content: "Only one step" }) };
      const spectrum = new CompressionSpectrum(mm, 1);
      // Multiple accesses to trigger threshold
      spectrum.recordAccess("ep1");
      const result = spectrum.recordAccess("ep1");
      expect(result).toBeUndefined();
    });
  });

  describe("recordApply", () => {
    it("increments apply count and triggers rule compression", () => {
      const content = "install package\nconfigure settings\nrun tests";
      const mm = { get: (_id: string) => ({ content }) };
      const spectrum = new CompressionSpectrum(mm, 2, 2); // both thresholds 2
      
      // Create skill
      spectrum.recordAccess("ep1");
      spectrum.recordAccess("ep1");
      const skillResult = spectrum.recordAccess("ep1");
      expect(skillResult).toBeDefined();
      
      if (skillResult) {
        // Apply skill once - below threshold
        const apply1 = spectrum.recordApply(skillResult.memoryId);
        expect(apply1).toBeUndefined();
        
        // Apply skill again - at threshold
        const apply2 = spectrum.recordApply(skillResult.memoryId);
        expect(apply2).toBeDefined();
        expect(apply2?.level).toBe(2);
      }
    });

    it("returns undefined for unknown skill", () => {
      const spectrum = new CompressionSpectrum();
      const result = spectrum.recordApply("unknown");
      expect(result).toBeUndefined();
    });
  });

  describe("recordVerify", () => {
    it("increments validation count", () => {
      const spectrum = new CompressionSpectrum(undefined, 1, 1, 1);
      
      // Create skill
      spectrum.recordAccess("ep1");
      spectrum.recordAccess("ep1");
      const skillResult = spectrum.recordAccess("ep1");
      
      // Create rule
      if (skillResult) {
        spectrum.recordApply(skillResult.memoryId);
        const ruleResult = spectrum.recordApply(skillResult.memoryId);
        
        // Verify rule
        if (ruleResult) {
          const principleResult = spectrum.recordVerify(ruleResult.memoryId);
          expect(principleResult).toBeDefined();
          expect(principleResult?.level).toBe(3);
        }
      }
    });

    it("returns undefined for unknown rule", () => {
      const spectrum = new CompressionSpectrum();
      const result = spectrum.recordVerify("unknown");
      expect(result).toBeUndefined();
    });
  });

  describe("configureThresholds", () => {
    it("updates access threshold", () => {
      const spectrum = new CompressionSpectrum();
      spectrum.configureThresholds({ access: 10 });
      const stats = spectrum.getStats();
      expect(stats.thresholds.skill_access).toBe(10);
    });

    it("updates apply threshold", () => {
      const spectrum = new CompressionSpectrum();
      spectrum.configureThresholds({ apply: 5 });
      const stats = spectrum.getStats();
      expect(stats.thresholds.rule_apply).toBe(5);
    });

    it("updates verify threshold", () => {
      const spectrum = new CompressionSpectrum();
      spectrum.configureThresholds({ verify: 3 });
      const stats = spectrum.getStats();
      expect(stats.thresholds.principle_verify).toBe(3);
    });

    it("updates multiple thresholds", () => {
      const spectrum = new CompressionSpectrum();
      spectrum.configureThresholds({ access: 8, apply: 4, verify: 2 });
      const stats = spectrum.getStats();
      expect(stats.thresholds.skill_access).toBe(8);
      expect(stats.thresholds.rule_apply).toBe(4);
      expect(stats.thresholds.principle_verify).toBe(2);
    });
  });

  describe("getCompressed", () => {
    it("returns compressed memories", () => {
      // Content must have at least 2 extractable steps
      const content = "pip install package\nnpm install dependencies\nconfigure settings";
      const mm = { get: (_id: string) => ({ content }) };
      const spectrum = new CompressionSpectrum(mm, 2);
      
      spectrum.recordAccess("ep1");
      spectrum.recordAccess("ep1");
      
      const results = spectrum.getCompressed();
      expect(results.length).toBeGreaterThan(0);
    });

    it("filters by memoryId", () => {
      const content = "Step 1: install package\nStep 2: configure";
      const mm = { get: (_id: string) => ({ content }) };
      const spectrum = new CompressionSpectrum(mm, 1);
      
      spectrum.recordAccess("ep1");
      spectrum.recordAccess("ep1");
      spectrum.recordAccess("ep2");
      spectrum.recordAccess("ep2");
      
      const results = spectrum.getCompressed("ep1");
      expect(Array.isArray(results)).toBe(true);
    });

    it("filters by level", () => {
      const spectrum = new CompressionSpectrum();
      const results = spectrum.getCompressed(undefined, 1);
      expect(Array.isArray(results)).toBe(true);
    });
  });

  describe("getStats", () => {
    it("returns stats object", () => {
      const spectrum = new CompressionSpectrum();
      const stats = spectrum.getStats();
      
      expect(stats.skills).toBe(0);
      expect(stats.rules).toBe(0);
      expect(stats.principles).toBe(0);
      expect(stats.total_episodes_tracked).toBe(0);
      expect(stats.enabled).toBe(true);
    });

    it("updates stats after compressions", () => {
      const content = "pip install package\nnpm install dep\nconfigure settings";
      const mm = { get: (_id: string) => ({ content }) };
      const spectrum = new CompressionSpectrum(mm, 2);
      
      spectrum.recordAccess("ep1");
      spectrum.recordAccess("ep1");
      
      const stats = spectrum.getStats();
      expect(stats.skills).toBe(1);
    });
  });
});