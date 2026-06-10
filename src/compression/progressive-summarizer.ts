// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * ProgressiveSummarizer — progressive summary pipeline for claw-mem v6.4.0.
 *
 * Adds L0.5 intermediate compression layer between L0 (raw) and L1 (rule):
 * - L0:   raw memory, ratio 1.0
 * - L0.5: key entity + decision extraction, ratio 0.7
 * - L1:   rule-based compression, ratio 0.5
 * - L2:   LLM-driven compression, ratio 0.3
 * - L3:   principle extraction, ratio 0.1
 *
 * Integrates with existing CompressionSpectrum.
 */

import type { MemoryRecord } from "../types.js";

// ── Types ─────────────────────────────────────────────────────────────────

export type CompressionLevelKey = "L0" | "L0.5" | "L1" | "L2" | "L3";

export interface ProgressiveLevel {
  level: CompressionLevelKey;
  ratio: number;
  method: "raw" | "progressive" | "rule" | "llm" | "principle";
  description: string;
}

/** Ordered compression levels from least to most compressed. */
export const COMPRESSION_LEVELS: ProgressiveLevel[] = [
  { level: "L0",   ratio: 1.0, method: "raw",         description: "原始记忆" },
  { level: "L0.5", ratio: 0.7, method: "progressive",  description: "关键实体+决策提取" },
  { level: "L1",   ratio: 0.5, method: "rule",         description: "规 then 压缩" },
  { level: "L2",   ratio: 0.3, method: "llm",          description: "LLM 驱动压缩" },
  { level: "L3",   ratio: 0.1, method: "principle",    description: "原 then 提取" },
];

export interface ProgressiveResult {
  content: string;
  level: CompressionLevelKey;
  ratio: number;
  method: ProgressiveLevel["method"];
  originalLength: number;
  compressedLength: number;
  entities: string[];
  decisions: string[];
}

// ── ProgressiveSummarizer ─────────────────────────────────────────────────

export class ProgressiveSummarizer {
  /**
   * Progressively summarize a memory to a target compression level.
   * Goes through intermediate levels if needed.
   */
  summarize(
    memory: MemoryRecord,
    targetLevel: CompressionLevelKey,
  ): ProgressiveResult {
    const currentIdx = this.getLevelIndex("L0");
    const targetIdx = this.getLevelIndex(targetLevel);

    if (targetIdx <= currentIdx) {
      return this.formatResult(memory, "L0");
    }

    // Progress through intermediate levels
    let intermediate = this.formatResult(memory, "L0");

    for (let i = 1; i <= targetIdx; i++) {
      const level = COMPRESSION_LEVELS[i];
      intermediate = this.compressToLevel(intermediate, level);
    }

    return intermediate;
  }

  /**
   * Check if a memory can be compressed to the target level.
   * L0.5+ requires minimum content length and structure.
   */
  canCompress(memory: MemoryRecord, targetLevel: CompressionLevelKey): boolean {
    const text = memory.text ?? "";
    const minLengths: Record<string, number> = {
      "L0": 0,
      "L0.5": 30,
      "L1": 50,
      "L2": 100,
      "L3": 200,
    };

    const minLen = minLengths[targetLevel] ?? 0;
    return text.length >= minLen;
  }

  /** Get the next compression level up from the current one. */
  getNextLevel(currentLevel: CompressionLevelKey): CompressionLevelKey {
    const idx = this.getLevelIndex(currentLevel);
    if (idx >= COMPRESSION_LEVELS.length - 1) {
      return COMPRESSION_LEVELS[COMPRESSION_LEVELS.length - 1].level;
    }
    return COMPRESSION_LEVELS[idx + 1].level;
  }

  /** Get all levels that are <= target (achievable via progressive pipeline). */
  getAchievableLevels(targetLevel: CompressionLevelKey): ProgressiveLevel[] {
    const targetIdx = this.getLevelIndex(targetLevel);
    return COMPRESSION_LEVELS.slice(0, targetIdx + 1);
  }

  /** Get the compression level info by key. */
  getLevel(level: CompressionLevelKey): ProgressiveLevel {
    return COMPRESSION_LEVELS[this.getLevelIndex(level)];
  }

  // ── Private ───────────────────────────────────────────────────────────

  private getLevelIndex(level: CompressionLevelKey): number {
    const idx = COMPRESSION_LEVELS.findIndex((l) => l.level === level);
    return idx >= 0 ? idx : 0;
  }

  private compressToLevel(
    input: ProgressiveResult,
    target: ProgressiveLevel,
  ): ProgressiveResult {
    switch (target.level) {
      case "L0.5":
        return this.compressL05(input);
      case "L1":
        return this.compressL1(input);
      case "L2":
        return this.compressL2(input);
      case "L3":
        return this.compressL3(input);
      default:
        return input;
    }
  }

  /**
   * L0.5: Key entity + decision extraction.
   * Preserves named entities (people, projects, tools) and explicit decisions.
   * Target ratio: 0.7 (70% of original).
   */
  private compressL05(input: ProgressiveResult): ProgressiveResult {
    const content = input.content;
    const entities = this.extractEntities(content);
    const decisions = this.extractDecisions(content);

    let summary = "";
    if (entities.length > 0) {
      summary += `实体: ${entities.join("、")}。`;
    }
    if (decisions.length > 0) {
      summary += `决策: ${decisions.join("；")}。`;
    }
    if (!summary) {
      // Fallback: first substantial sentence
      summary = content.split(/[。！？.!?\n]/).filter((s) => s.trim().length > 10)[0]?.trim() ?? content.slice(0, 100);
    }

    return {
      content: summary,
      level: "L0.5",
      ratio: summary.length / Math.max(input.originalLength, 1),
      method: "progressive",
      originalLength: input.originalLength,
      compressedLength: summary.length,
      entities,
      decisions,
    };
  }

  /** L1: Rule-based compression — keep first sentences of each paragraph. */
  private compressL1(input: ProgressiveResult): ProgressiveResult {
    const sentences = input.content
      .split(/[。！？.!?\n]+/)
      .filter((s) => s.trim().length > 5);
    const kept = sentences.slice(0, Math.max(2, Math.ceil(sentences.length * 0.5)));
    const summary = kept.join("。") + (kept.length > 0 ? "。" : "");

    return {
      content: summary,
      level: "L1",
      ratio: summary.length / Math.max(input.originalLength, 1),
      method: "rule",
      originalLength: input.originalLength,
      compressedLength: summary.length,
      entities: input.entities,
      decisions: input.decisions,
    };
  }

  /** L2: Placeholder for LLM-driven compression (delegates to LLMCompressor). */
  private compressL2(input: ProgressiveResult): ProgressiveResult {
    // L2 compression is handled by LLMCompressor (v6.1.0)
    // Here we provide a lightweight fallback
    const words = input.content.split(/[\s,，。！？]+/).filter((w) => w.length > 1);
    const key = words.slice(0, Math.ceil(words.length * 0.3));
    const summary = key.join(" ");

    return {
      content: summary,
      level: "L2",
      ratio: summary.length / Math.max(input.originalLength, 1),
      method: "llm",
      originalLength: input.originalLength,
      compressedLength: summary.length,
      entities: input.entities,
      decisions: input.decisions,
    };
  }

  /** L3: Principle extraction — distill to core rules/principles. */
  private compressL3(input: ProgressiveResult): ProgressiveResult {
    const rules = this.extractRules(input.content);
    const summary = rules.length > 0
      ? `原 then : ${rules.join("；")}`
      : input.content.slice(0, 50) + "...";

    return {
      content: summary,
      level: "L3",
      ratio: summary.length / Math.max(input.originalLength, 1),
      method: "principle",
      originalLength: input.originalLength,
      compressedLength: summary.length,
      entities: input.entities,
      decisions: input.decisions,
    };
  }

  // ── Entity/Decision Extraction ─────────────────────────────────────────

  private extractEntities(text: string): string[] {
    const patterns = [
      // Named entities: capitalized words, project names
      /\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b/g,
      // Tool/tech names
      /\b(TypeScript|JavaScript|Python|Rust|Go|Java|React|Vue|Docker|Kubernetes|Git|npm|Node\.js|claw-[a-z-]+)\b/gi,
      // Person references
      /\b(Peter|[A-Z][a-z]{2,}(?:\s[A-Z][a-z]{2,})*)\b/g,
    ];

    const found = new Set<string>();
    for (const pattern of patterns) {
      const matches = text.matchAll(pattern);
      for (const m of matches) {
        const entity = m[0];
        if (entity.length > 1 && !/^(The|This|That|These|Those|When|Where|Which|There)$/i.test(entity)) {
          found.add(entity);
        }
      }
    }

    return [...found].slice(0, 10);
  }

  private extractDecisions(text: string): string[] {
    const decisionIndicators = [
      /决定[：:]\s*(.+?)(?:[。！？.!?\n]|$)/g,
      /选择[：:]\s*(.+?)(?:[。！？.!?\n]|$)/g,
      /采用[：:]\s*(.+?)(?:[。！？.!?\n]|$)/g,
      /确认[：:]\s*(.+?)(?:[。！？.!?\n]|$)/g,
      /使用[：:]\s*(.+?)(?:[。！？.!?\n]|$)/g,
    ];

    const decisions: string[] = [];
    for (const pattern of decisionIndicators) {
      const matches = text.matchAll(pattern);
      for (const m of matches) {
        const d = m[1].trim();
        if (d.length > 3 && d.length < 200) {
          decisions.push(d);
        }
      }
    }

    return decisions.slice(0, 5);
  }

  private extractRules(text: string): string[] {
    const rulePatterns = [
      /必须(.+?)(?:[。！？.!?\n]|$)/g,
      /应该(.+?)(?:[。！？.!?\n]|$)/g,
      /始终(.+?)(?:[。！？.!?\n]|$)/g,
      /原 then [：:]\s*(.+?)(?:[。！？.!?\n]|$)/g,
    ];

    const rules: string[] = [];
    for (const pattern of rulePatterns) {
      const matches = text.matchAll(pattern);
      for (const m of matches) {
        const r = m[1].trim();
        if (r.length > 3 && r.length < 150) {
          rules.push(r);
        }
      }
    }

    return rules.slice(0, 5);
  }

  private formatResult(memory: MemoryRecord, level: CompressionLevelKey): ProgressiveResult {
    return {
      content: memory.text,
      level,
      ratio: 1.0,
      method: "raw",
      originalLength: memory.text.length,
      compressedLength: memory.text.length,
      entities: [],
      decisions: [],
    };
  }
}
