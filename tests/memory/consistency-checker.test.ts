import { describe, it, expect, beforeEach } from "vitest";
import { MemoryConsistencyChecker } from "../../src/memory/consistency-checker.js";
import type { MemoryRecord } from "../../src/types.js";

describe("MemoryConsistencyChecker", () => {
  let checker: MemoryConsistencyChecker;

  beforeEach(() => {
    checker = new MemoryConsistencyChecker();
  });

  // Helper to create valid memory
  const createMemory = (overrides?: Partial<MemoryRecord>): MemoryRecord => ({
    id: "test-1",
    text: "Test content",
    memory_type: "episodic",
    created_at: new Date().toISOString(),
    ...overrides
  });

  describe("built-in rules", () => {
    it("should pass valid memory", () => {
      const memory = createMemory();
      const result = checker.checkMemory(memory);
      expect(result.passed).toBe(true);
      expect(result.violations).toHaveLength(0);
    });

    it("should fail empty content", () => {
      const memory = createMemory({ text: "" });
      const result = checker.checkMemory(memory);
      expect(result.passed).toBe(false);
      expect(result.violations.some(v => v.includes("mem-empty-content"))).toBe(true);
    });

    it("should fail invalid type", () => {
      const memory = createMemory({ memory_type: "invalid" as any });
      const result = checker.checkMemory(memory);
      expect(result.passed).toBe(false);
      expect(result.violations.some(v => v.includes("mem-valid-type"))).toBe(true);
    });

    it("should fail missing ID", () => {
      const memory = createMemory({ id: "" });
      const result = checker.checkMemory(memory);
      expect(result.passed).toBe(false);
      expect(result.violations.some(v => v.includes("mem-has-id"))).toBe(true);
    });

    it("should fail invalid timestamp", () => {
      const memory = createMemory({ created_at: "invalid-date" });
      const result = checker.checkMemory(memory);
      expect(result.passed).toBe(false);
      expect(result.violations.some(v => v.includes("mem-valid-timestamp"))).toBe(true);
    });
  });

  describe("batch check", () => {
    it("should batch check memories", () => {
      const memories = [
        createMemory({ id: "m1", text: "Valid content" }),
        createMemory({ id: "m2", text: "" }), // Invalid
        createMemory({ id: "m3", text: "Another valid" }),
      ];

      const result = checker.checkMemories(memories);
      expect(result.total).toBe(3);
      expect(result.passed).toBe(2);
      expect(result.failed).toBe(1);
      expect(result.violations).toHaveLength(1);
    });
  });

  describe("custom rules", () => {
    it("should support custom rules", () => {
      checker.addRule({
        ruleId: "custom-tag-check",
        name: "Has Tags",
        description: "Memory must have at least one tag",
        check: (mem) => (mem.tags?.length ?? 0) > 0
      });

      const memory = createMemory({ tags: [] });
      const result = checker.checkMemory(memory);
      expect(result.passed).toBe(false);
      expect(result.violations.some(v => v.includes("custom-tag-check"))).toBe(true);
    });

    it("should remove rules", () => {
      checker.addRule({
        ruleId: "temp-rule",
        name: "Temp",
        description: "Temporary rule",
        check: () => false
      });

      expect(checker.getRules().length).toBe(5); // 4 builtin + 1 custom

      checker.removeRule("temp-rule");
      expect(checker.getRules().length).toBe(4);
    });
  });

  describe("getRules()", () => {
    it("should return all registered rules", () => {
      const rules = checker.getRules();
      expect(rules.length).toBeGreaterThan(0);
      expect(rules.some(r => r.ruleId === "mem-empty-content")).toBe(true);
      expect(rules.some(r => r.ruleId === "mem-valid-type")).toBe(true);
    });
  });
});
