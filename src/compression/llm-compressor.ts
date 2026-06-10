// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * LLMCompressor — LLM-driven memory compression for claw-mem v6.1.0.
 *
 * Compresses memories using a configurable LLM backend with graceful fallback
 * to rule-based compression when the LLM is unavailable or quality is insufficient.
 */

import type { MemoryRecord } from "../types.js";

// ── Types ─────────────────────────────────────────────────────────────────

export interface CompressionConfig {
  target_ratio: number;
  min_quality: number;
  fallback_to_rule: boolean;
  model?: string;
  maxRetries?: number;
}

export const DEFAULT_LLM_COMPRESSION_CONFIG: CompressionConfig = {
  target_ratio: 0.3,
  min_quality: 0.8,
  fallback_to_rule: true,
  maxRetries: 2,
};

export interface LLMCompressedMemory {
  summary: string;
  originalIds: string[];
  originalLength: number;
  compressedLength: number;
  ratio: number;
  qualityScore: number;
  method: "llm" | "rule";
  timestamp: string;
}

export interface CompressionQuality {
  avgRatio: number;
  avgQualityScore: number;
  totalCompressed: number;
  llmSuccessRate: number;
  recentSamples: LLMCompressedMemory[];
}

// ── Prompt template ───────────────────────────────────────────────────────

const COMPRESSION_PROMPT = `Please compress the following memories into a concise summary, preserving core information:

{memories}

Requirements:
1. Preserve core facts and user preferences
2. Compress to approximately 30% of original length
3. Reply in the same language as the input

Compressed:`;

// ── LLMCompressor ─────────────────────────────────────────────────────────

export class LLMCompressor {
  private config: CompressionConfig;
  private qualitySamples: LLMCompressedMemory[] = [];
  private totalCompressed = 0;
  private llmSuccessCount = 0;

  constructor(config?: Partial<CompressionConfig>) {
    this.config = { ...DEFAULT_LLM_COMPRESSION_CONFIG, ...config };
  }

  /** Compress a batch of memories using LLM, falling back to rule-based. */
  async compress(memories: MemoryRecord[]): Promise<LLMCompressedMemory> {
    if (memories.length === 0) {
      return this.emptyResult();
    }

    const originalText = memories.map((m) => m.text).join("\n");
    const originalLength = originalText.length;

    // Try LLM compression
    for (let attempt = 0; attempt < (this.config.maxRetries ?? 2) + 1; attempt++) {
      try {
        const summary = await this.callLLM(originalText);
        const compressedLength = summary.length;
        const ratio = compressedLength / Math.max(originalLength, 1);
        const qualityScore = this.estimateQuality(summary, memories);

        const result: LLMCompressedMemory = {
          summary,
          originalIds: memories.map((m) => m.id),
          originalLength,
          compressedLength,
          ratio,
          qualityScore,
          method: "llm",
          timestamp: new Date().toISOString(),
        };

        this.recordSample(result);
        return result;
      } catch (err) {
        if (!this.config.fallback_to_rule) {
          throw err;
        }
        // Retry after brief delay
        if (attempt < (this.config.maxRetries ?? 2)) {
          await this.delay(200 * (attempt + 1));
        }
      }
    }

    // Fallback to rule-based compression
    return this.ruleCompress(memories);
  }

  /** Decompress a LLMCompressedMemory back to Memory-like records. */
  async decompress(compressed: LLMCompressedMemory): Promise<Pick<MemoryRecord, "id" | "text" | "memory_type">[]> {
    return compressed.originalIds.map((id) => ({
      id,
      text: `[compressed] ${compressed.summary}`,
      memory_type: "episodic" as const,
    }));
  }

  /** Estimate compression ratio for given memories without actually compressing. */
  estimateCompressionRatio(memories: MemoryRecord[]): number {
    const totalLen = memories.reduce((s, m) => s + m.text.length, 0);
    const targetLen = Math.ceil(totalLen * this.config.target_ratio);
    // Clamp to reasonable range
    return Math.max(50, Math.min(targetLen, 500));
  }

  /** Get quality statistics for monitoring. */
  getQualityStats(): CompressionQuality {
    const samples = this.qualitySamples.slice(-20);
    return {
      avgRatio: samples.length > 0
        ? samples.reduce((s, r) => s + r.ratio, 0) / samples.length
        : 0,
      avgQualityScore: samples.length > 0
        ? samples.reduce((s, r) => s + r.qualityScore, 0) / samples.length
        : 0,
      totalCompressed: this.totalCompressed,
      llmSuccessRate: this.totalCompressed > 0
        ? this.llmSuccessCount / this.totalCompressed
        : 0,
      recentSamples: samples.slice(-5),
    };
  }

  /** Update compression configuration at runtime. */
  updateConfig(config: Partial<CompressionConfig>): void {
    this.config = { ...this.config, ...config };
  }

  // ── Private ───────────────────────────────────────────────────────────

  private async callLLM(text: string): Promise<string> {
    const prompt = COMPRESSION_PROMPT.replace("{memories}", text);

    // Use configurable LLM endpoint via fetch
    const endpoint = process.env.CLAW_MEM_LLM_ENDPOINT
      || process.env.OPENAI_BASE_URL
      || "http://localhost:18789/v1";

    const apiKey = process.env.CLAW_MEM_LLM_API_KEY
      || process.env.OPENAI_API_KEY
      || "";

    const model = this.config.model
      || process.env.CLAW_MEM_LLM_MODEL
      || "gpt-4o-mini";

    const response = await fetch(`${endpoint}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: "You are a professional memory compression assistant." },
          { role: "user", content: prompt },
        ],
        max_tokens: Math.ceil(text.length * this.config.target_ratio * 0.5),
        temperature: 0.3,
      }),
    });

    if (!response.ok) {
      throw new Error(`LLM API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json() as any;
    const content = data?.choices?.[0]?.message?.content;
    if (!content || typeof content !== "string") {
      throw new Error("LLM response missing content");
    }

    return content.trim();
  }

  /** Rule-based compression as fallback. */
  private ruleCompress(memories: MemoryRecord[]): LLMCompressedMemory {
    const originalText = memories.map((m) => m.text).join("\n");
    const originalLength = originalText.length;

    // Extract first sentence/key info from each memory
    const summaries = memories.map((m) => {
      const firstSentence = m.text.split(/[。！？.!?\n]/)[0]?.trim() || "";
      return firstSentence.slice(0, 80);
    });

    const summary = summaries.join("；");
    const result: LLMCompressedMemory = {
      summary,
      originalIds: memories.map((m) => m.id),
      originalLength,
      compressedLength: summary.length,
      ratio: summary.length / Math.max(originalLength, 1),
      qualityScore: 0.5,
      method: "rule",
      timestamp: new Date().toISOString(),
    };

    this.recordSample(result);
    return result;
  }

  /** Simple quality estimation based on keyword preservation. */
  private estimateQuality(summary: string, originals: MemoryRecord[]): number {
    const originalText = originals.map((m) => m.text).join(" ");
    const summaryWords = new Set(this.tokenize(summary));
    const originalWords = this.tokenize(originalText);

    if (originalWords.length === 0) return 0;

    const preserved = originalWords.filter((w) => summaryWords.has(w)).length;
    const keywordScore = preserved / originalWords.length;

    // Length ratio penalty: too short or too long reduces quality
    const targetLen = Math.ceil(originalText.length * this.config.target_ratio);
    const actualLen = summary.length;
    const lengthScore = 1 - Math.abs(actualLen - targetLen) / Math.max(targetLen, 1);

    return Math.min(1, keywordScore * 0.7 + Math.max(0, lengthScore) * 0.3);
  }

  private tokenize(text: string): string[] {
    return text
      .toLowerCase()
      .split(/[\s,，。！？.!?;:：；、]+/)
      .filter((w) => w.length >= 2);
  }

  private recordSample(result: LLMCompressedMemory): void {
    this.totalCompressed++;
    if (result.method === "llm") this.llmSuccessCount++;
    this.qualitySamples.push(result);
    if (this.qualitySamples.length > 100) {
      this.qualitySamples.shift();
    }
  }

  private emptyResult(): LLMCompressedMemory {
    return {
      summary: "",
      originalIds: [],
      originalLength: 0,
      compressedLength: 0,
      ratio: 0,
      qualityScore: 1,
      method: "rule",
      timestamp: new Date().toISOString(),
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// ── LLMCompressorMonitor (lightweight wrapper for backward compat) ──────────

export class LLMCompressorMonitor {
  private compressor: LLMCompressor;

  constructor(compressor: LLMCompressor) {
    this.compressor = compressor;
  }

  getQualityStats(): CompressionQuality {
    return this.compressor.getQualityStats();
  }

  isQualityAcceptable(): boolean {
    const stats = this.getQualityStats();
    return stats.avgQualityScore >= 0.8 || stats.llmSuccessRate >= 0.9;
  }

  recommendation(): "llm" | "rule" | "mixed" {
    const stats = this.getQualityStats();
    if (stats.totalCompressed < 5) return "llm";
    if (stats.llmSuccessRate >= 0.9 && stats.avgQualityScore >= 0.8) return "llm";
    if (stats.llmSuccessRate < 0.3) return "rule";
    return "mixed";
  }
}
