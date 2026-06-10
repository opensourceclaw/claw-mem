// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * LLMCompressorV2 — Enhanced LLM-driven memory compression for claw-mem v6.7.0.
 *
 * Extends the base LLMCompressor with quality metrics, adaptive compression,
 * and reasoning chain preservation.
 */

import type { MemoryRecord } from "../types.js";

// ── Types ─────────────────────────────────────────────────────────────────

export interface CompressionQualityMetrics {
  /** Semantic content retention rate (0-1) */
  semanticRetention: number;
  /** Key information preservation rate (0-1) */
  keyInformationPreserved: number;
  /** Reasoning chain integrity (0-1) */
  reasoningChainIntegrity: number;
  /** Overall quality score */
  overallQuality: number;
  /** Compression ratio achieved */
  compressionRatio: number;
  /** Original token count (estimated) */
  originalTokens: number;
  /** Compressed token count (estimated) */
  compressedTokens: number;
}

export interface CompressionResult {
  summary: string;
  originalIds: string[];
  quality: CompressionQualityMetrics;
  method: "llm" | "rule" | "adaptive";
  reasoningPreserved: boolean;
  timestamp: string;
}

export interface AdaptiveConfig {
  targetTokens?: number;
  minQuality?: number;
  preserveReasoning?: boolean;
  reasoningKeywords?: string[];
  maxRetries?: number;
}

export const DEFAULT_ADAPTIVE_CONFIG: AdaptiveConfig = {
  minQuality: 0.8,
  preserveReasoning: true,
  maxRetries: 2,
  reasoningKeywords: [
    "because", "therefore", "so", "thus", "hence", "导致", "因此", " which 以",
    "since", "as a result", "consequently", "由于", "原因", "结果",
    "depends on", "requires", "需 to ", "依赖于",
  ],
};

// ── Reasoning chain keywords ────────────────────────────────────────────

const REASONING_CHAINS = [
  /\b(?:first|firstly|step \d)\b[^.]*\./gi,
  /\b(?:then|next|second|third|finally|lastly)\b[^.]*\./gi,
  /\b(?:because|since|due to)\b[^.]*\./gi,
  /\b(?:therefore|thus|hence|so|as a result)\b[^.]*\./gi,
  /\b(?:第一步|第二步|第三步|首先|然后| most 后|接着)\b[^。]*。/g,
  /\b(?:因 for |由于| which 以|因此| from  and )\b[^。]*。/g,
];

// ── LLMCompressorV2 ─────────────────────────────────────────────────────

export class LLMCompressorV2 {
  private config: AdaptiveConfig;
  private qualityHistory: CompressionQualityMetrics[] = [];
  private totalCompressions = 0;

  constructor(config?: Partial<AdaptiveConfig>) {
    this.config = { ...DEFAULT_ADAPTIVE_CONFIG, ...config };
  }

  /** Compress memory with full quality evaluation metrics. */
  compressWithQualityEvaluation(
    memory: MemoryRecord,
    context?: MemoryRecord[],
  ): CompressionResult {
    const originalTokens = this.estimateTokens(memory.text);
    const contextText = context?.map((m) => m.text).join("\n") ?? "";

    // Generate compressed summary
    const summary = this.compressText(memory.text, contextText);
    const compressedTokens = this.estimateTokens(summary);

    // Calculate quality metrics
    const semanticRetention = this.evaluateSemanticRetention(
      memory.text,
      summary,
    );
    const keyInformationPreserved = this.evaluateKeyInformation(
      memory.text,
      summary,
    );
    const reasoningChainIntegrity = this.evaluateReasoningChain(
      memory.text,
      summary,
    );

    const compressionRatio = compressedTokens / Math.max(originalTokens, 1);
    const overallQuality =
      semanticRetention * 0.35 +
      keyInformationPreserved * 0.35 +
      reasoningChainIntegrity * 0.3;

    const quality: CompressionQualityMetrics = {
      semanticRetention,
      keyInformationPreserved,
      reasoningChainIntegrity,
      overallQuality,
      compressionRatio,
      originalTokens,
      compressedTokens,
    };

    const result: CompressionResult = {
      summary,
      originalIds: [memory.id],
      quality,
      method: "rule",
      reasoningPreserved: reasoningChainIntegrity >= 0.7,
      timestamp: new Date().toISOString(),
    };

    this.recordQuality(quality);
    return result;
  }

  /** Adaptively compress memory to a target token count. */
  adaptiveCompress(
    memory: MemoryRecord,
    targetTokens: number,
    context?: MemoryRecord[],
  ): CompressionResult {
    const base = this.compressWithQualityEvaluation(memory, context);

    if (base.quality.compressedTokens <= targetTokens) {
      base.method = "adaptive";
      return base;
    }

    // Progressive truncation until target met
    let summary = base.summary;
    let attempts = 0;
    const maxAttempts = this.config.maxRetries ?? 2;

    while (
      this.estimateTokens(summary) > targetTokens &&
      attempts < maxAttempts
    ) {
      // More aggressive compression: split by sentences, keep most important
      const sentences = summary.split(/[.。!！?？\n]+/).filter((s) => s.trim());
      if (sentences.length <= 1) break;

      // Keep sentences with highest keyword density
      const keywords = this.extractKeywords(memory.text);
      const scored = sentences.map((s) => ({
        text: s.trim(),
        score: this.sentenceRelevance(s, keywords),
      }));
      scored.sort((a, b) => b.score - a.score);

      // Keep top fraction of sentences
      const keepCount = Math.max(
        1,
        Math.floor(scored.length * (targetTokens / this.estimateTokens(summary))),
      );
      summary = scored
        .slice(0, keepCount)
        .map((s) => s.text)
        .join(". ");

      attempts++;
    }

    const compressedTokens = this.estimateTokens(summary);
    const updatedQuality = {
      ...base.quality,
      compressedTokens,
      compressionRatio: compressedTokens / Math.max(base.quality.originalTokens, 1),
    };

    return {
      ...base,
      summary,
      quality: updatedQuality,
      method: "adaptive",
    };
  }

  /** Check if reasoning chains should be preserved in a memory. */
  preserveReasoningChain(memory: MemoryRecord): boolean {
    if (!this.config.preserveReasoning) return false;

    const text = memory.text.toLowerCase();
    const keywordCount = (this.config.reasoningKeywords ?? []).filter((kw) =>
      text.includes(kw.toLowerCase()),
    ).length;

    // Also check for reasoning chain patterns
    const chainMatches = REASONING_CHAINS.reduce(
      (count, pattern) => count + (text.match(pattern)?.length ?? 0),
      0,
    );

    return keywordCount >= 2 || chainMatches >= 3;
  }

  /** Batch-compress multiple memories with quality evaluation. */
  batchCompressWithQuality(
    memories: MemoryRecord[],
  ): CompressionResult[] {
    return memories.map((m, i) => {
      const context = [
        ...memories.slice(0, i),
        ...memories.slice(i + 1),
      ];
      return this.compressWithQualityEvaluation(m, context);
    });
  }

  /** Get historical quality statistics. */
  getQualityStats(): {
    avgSemanticRetention: number;
    avgKeyInfoPreserved: number;
    avgReasoningIntegrity: number;
    avgOverallQuality: number;
    avgCompressionRatio: number;
    totalCompressions: number;
  } {
    if (this.qualityHistory.length === 0) {
      return {
        avgSemanticRetention: 0,
        avgKeyInfoPreserved: 0,
        avgReasoningIntegrity: 0,
        avgOverallQuality: 0,
        avgCompressionRatio: 0,
        totalCompressions: 0,
      };
    }
    const n = this.qualityHistory.length;
    return {
      avgSemanticRetention: this.sumOf("semanticRetention") / n,
      avgKeyInfoPreserved: this.sumOf("keyInformationPreserved") / n,
      avgReasoningIntegrity: this.sumOf("reasoningChainIntegrity") / n,
      avgOverallQuality: this.sumOf("overallQuality") / n,
      avgCompressionRatio: this.sumOf("compressionRatio") / n,
      totalCompressions: this.totalCompressions,
    };
  }

  /** Update configuration. */
  updateConfig(config: Partial<AdaptiveConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /** Reset quality history. */
  reset(): void {
    this.qualityHistory = [];
    this.totalCompressions = 0;
  }

  // ── Private helpers ────────────────────────────────────────────────────

  private compressText(text: string, context: string): string {
    // Rule-based smart compression: extract key sentences
    const sentences = text.split(/[.。!！?？\n]+/).filter((s) => s.trim());
    if (sentences.length <= 2) return sentences.join(". ");

    const keywords = this.extractKeywords(context || text);
    const scored = sentences.map((s) => ({
      text: s.trim(),
      score: this.sentenceRelevance(s, keywords),
    }));

    scored.sort((a, b) => b.score - a.score);
    const keepCount = Math.max(2, Math.ceil(sentences.length * 0.4));
    return scored
      .slice(0, keepCount)
      .sort((a, b) => text.indexOf(a.text) - text.indexOf(b.text)) // Preserve order
      .map((s) => s.text)
      .join(". ");
  }

  private estimateTokens(text: string): number {
    // CJK-aware token estimation (~1.5 chars/token for CJK, ~4 chars/token for Latin)
    const cjkChars = (text.match(/[\u4e00-\u9fff\u3400-\u4dbf]/g) || []).length;
    const latinChars = text.length - cjkChars;
    return Math.ceil(cjkChars / 1.5 + latinChars / 4);
  }

  private evaluateSemanticRetention(original: string, summary: string): number {
    const origWords = this.normalizeWords(original);
    const summaryWords = new Set(this.normalizeWords(summary));
    if (origWords.length === 0) return 1;
    const preserved = origWords.filter((w) => summaryWords.has(w)).length;
    return Math.min(1, preserved / origWords.length);
  }

  private evaluateKeyInformation(original: string, summary: string): number {
    const keywords = this.extractKeywords(original);
    if (keywords.length === 0) return 0.8;

    const summaryLower = summary.toLowerCase();
    const preserved = keywords.filter((kw) =>
      summaryLower.includes(kw.toLowerCase()),
    ).length;
    return Math.min(1, preserved / keywords.length);
  }

  private evaluateReasoningChain(original: string, summary: string): number {
    const chainCount = REASONING_CHAINS.reduce(
      (count, pattern) => count + (original.match(pattern)?.length ?? 0),
      0,
    );
    if (chainCount === 0) return 1; // No chains to preserve

    const preservedCount = REASONING_CHAINS.reduce(
      (count, pattern) => count + (summary.match(pattern)?.length ?? 0),
      0,
    );
    return Math.min(1, preservedCount / chainCount);
  }

  private extractKeywords(text: string): string[] {
    const words = text
      .toLowerCase()
      .split(/[\s,，。！？.!?;:：；、\n]+/)
      .filter((w) => w.length >= 3);

    const freq = new Map<string, number>();
    for (const w of words) {
      if (w.length >= 20) continue;
      freq.set(w, (freq.get(w) ?? 0) + 1);
    }

    return [...freq.entries()]
      .filter(([, count]) => count >= 2)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([w]) => w);
  }

  private normalizeWords(text: string): string[] {
    return text
      .toLowerCase()
      .split(/[\s,，。！？.!?;:：；、\n]+/)
      .filter((w) => w.length >= 2);
  }

  private sentenceRelevance(
    sentence: string,
    keywords: string[],
  ): number {
    const s = sentence.toLowerCase();
    let score = 1; // Base score for all sentences
    for (const kw of keywords) {
      if (s.includes(kw.toLowerCase())) score += 2;
    }
    // Bonus for proper nouns (capitalized words)
    const properNouns = sentence.match(/\b[A-Z][a-z]+\b/g);
    if (properNouns) score += properNouns.length;
    return score;
  }

  private sumOf(field: keyof CompressionQualityMetrics): number {
    return this.qualityHistory.reduce(
      (sum, q) => sum + (q[field] as number),
      0,
    );
  }

  private recordQuality(quality: CompressionQualityMetrics): void {
    this.totalCompressions++;
    this.qualityHistory.push(quality);
    if (this.qualityHistory.length > 100) {
      this.qualityHistory.shift();
    }
  }
}
