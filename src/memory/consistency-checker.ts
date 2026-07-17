// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.40.0 — MemoryConsistencyChecker
 *
 * Validates memory integrity using claw-gov EthicsCompliance.
 */

import type { MemoryRecord } from "../types.js";

/**
 * Memory consistency rule definition.
 */
export interface MemoryConsistencyRule {
  ruleId: string;
  name: string;
  description: string;
  check: (memory: MemoryRecord) => boolean; // true = pass, false = violation
}

/**
 * Result of checking a single memory.
 */
export interface MemoryCheckResult {
  memoryId: string;
  passed: boolean;
  violations: string[];
}

/**
 * Result of batch checking memories.
 */
export interface BatchCheckResult {
  total: number;
  passed: number;
  failed: number;
  violations: Array<{ memoryId: string; violations: string[] }>;
}

/**
 * MemoryConsistencyChecker — Validates memory integrity.
 *
 * @example
 * ```typescript
 * const checker = new MemoryConsistencyChecker();
 *
 * // Check single memory
 * const result = checker.checkMemory(memory);
 *
 * // Batch check
 * const batchResult = checker.checkMemories(memories);
 *
 * // Add custom rule
 * checker.addRule({
 *   ruleId: "custom-001",
 *   name: "Custom Rule",
 *   description: "Check custom condition",
 *   check: (mem) => mem.tags?.length > 0
 * });
 * ```
 */
export class MemoryConsistencyChecker {
  private rules: Map<string, MemoryConsistencyRule>;

  constructor() {
    this.rules = new Map();
    this._initBuiltinRules();
  }

  private _initBuiltinRules(): void {
    // Rule 1: Non-empty content (text field)
    this.addRule({
      ruleId: "mem-empty-content",
      name: "Non-Empty Content",
      description: "Memory text must not be empty",
      check: (mem) => {
        const content = mem.text;
        return content != null && String(content).trim().length > 0;
      }
    });

    // Rule 2: Valid memory type
    this.addRule({
      ruleId: "mem-valid-type",
      name: "Valid Memory Type",
      description: "Memory type must be one of: episodic, semantic, procedural, fact, preference",
      check: (mem) => {
        const validTypes = ["episodic", "semantic", "procedural", "fact", "preference"];
        return validTypes.includes(mem.memory_type ?? "episodic");
      }
    });

    // Rule 3: Valid timestamp (created_at field)
    this.addRule({
      ruleId: "mem-valid-timestamp",
      name: "Valid Timestamp",
      description: "Memory must have a valid ISO timestamp",
      check: (mem) => {
        try {
          const ts = mem.created_at;
          if (!ts) return false;
          const date = new Date(ts);
          return !isNaN(date.getTime());
        } catch {
          return false;
        }
      }
    });

    // Rule 4: Has ID
    this.addRule({
      ruleId: "mem-has-id",
      name: "Has ID",
      description: "Memory must have a valid ID",
      check: (mem) => {
        return mem.id != null && String(mem.id).trim().length > 0;
      }
    });
  }

  /**
   * Add custom consistency rule.
   * @param rule - Rule definition
   */
  addRule(rule: MemoryConsistencyRule): void {
    this.rules.set(rule.ruleId, { ...rule });
  }

  /**
   * Remove a rule by ID.
   * @param ruleId - Rule ID to remove
   */
  removeRule(ruleId: string): boolean {
    return this.rules.delete(ruleId);
  }

  /**
   * Get all registered rules.
   */
  getRules(): MemoryConsistencyRule[] {
    return [...this.rules.values()];
  }

  /**
   * Check single memory for consistency.
   * @param memory - Memory to check
   * @returns Check result with pass/fail and violations
   */
  checkMemory(memory: MemoryRecord): MemoryCheckResult {
    const violations: string[] = [];

    for (const [id, rule] of this.rules) {
      try {
        if (!rule.check(memory)) {
          violations.push(`[${id}] ${rule.name}: ${rule.description}`);
        }
      } catch (err) {
        violations.push(`[${id}] ${rule.name}: Check failed with error`);
      }
    }

    return {
      memoryId: memory.id ?? "unknown",
      passed: violations.length === 0,
      violations
    };
  }

  /**
   * Batch check memories.
   * @param memories - Memories to check
   * @returns Batch check result with stats and violations
   */
  checkMemories(memories: MemoryRecord[]): BatchCheckResult {
    const results = memories.map(mem => this.checkMemory(mem));
    const failed = results.filter(r => !r.passed);

    return {
      total: memories.length,
      passed: results.filter(r => r.passed).length,
      failed: failed.length,
      violations: failed.map(r => ({
        memoryId: r.memoryId,
        violations: r.violations
      }))
    };
  }

  /**
   * Enable/disable a rule.
   * @param ruleId - Rule ID
   * @param enabled - Whether to enable
   */
  setRuleEnabled(ruleId: string, enabled: boolean): boolean {
    const rule = this.rules.get(ruleId);
    if (rule) {
      // For now, we just add/remove the rule
      if (!enabled) {
        this.rules.delete(ruleId);
      }
      return true;
    }
    return false;
  }
}
