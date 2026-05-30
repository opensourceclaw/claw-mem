// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * F5 Compression V2 for claw-mem v2.5.0
 *
 * Improved memory compression with better quality-to-size ratio.
 */

// ── CompressionLevelV2 enum ──────────────────────────────────────────────

export enum CompressionLevelV2 {
  LIGHT = 0.3,
  MEDIUM = 0.5,
  AGGRESSIVE = 0.7,
  ULTRA = 0.85,
}

// ── CompressionResultV2 ─────────────────────────────────────────────────

export interface CompressionResultV2 {
  originalLength: number;
  compressedLength: number;
  compressionRatio: number;
  preservedContent: string;
  summary: string;
  keyPoints: string[];
  entities: string[];
  topics: string[];
}

export function createCompressionResultV2(
  overrides?: Partial<CompressionResultV2>,
): CompressionResultV2 {
  return {
    originalLength: 0,
    compressedLength: 0,
    compressionRatio: 0,
    preservedContent: "",
    summary: "",
    keyPoints: [],
    entities: [],
    topics: [],
    ...overrides,
  };
}

// ── F5CompressorV2 ──────────────────────────────────────────────────────

export class F5CompressorV2 {
  readonly level: CompressionLevelV2;
  readonly preserveEntities: boolean;
  readonly generateSummary: boolean;

  // Important entity patterns
  private readonly _entityPatterns: Record<string, RegExp> = {
    person: /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b/,
    email: /\b[\w.-]+@[\w.-]+\.\w+\b/,
    date: /\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b/,
    time: /\b(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\b/,
    number: /\b(\d+(?:,\d{3})*(?:\.\d+)?)\b/,
    url: /https?:\/\/[^\s]+/,
  };

  // Topic keywords
  private readonly _topicKeywords: Record<string, string[]> = {
    meeting: ["meeting", "discuss", "schedule", "agenda", "会议", "讨论", "安排"],
    project: ["project", "task", "milestone", "deadline", "项目", "任务", "里程碑"],
    decision: ["decided", "agreed", "approved", "decision", "决定", "同意", "批准"],
    request: ["request", "ask", "need", "want", "would like", "请求", "需要", "想要"],
    information: ["know", "learn", "remember", "information", "知道", "了解", "记得"],
    problem: ["issue", "bug", "error", "fix", "problem", "问题", "错误", "修复"],
    success: ["success", "complete", "finish", "done", "成功", "完成"],
  };

  constructor(
    level: CompressionLevelV2 = CompressionLevelV2.MEDIUM,
    preserveEntities = true,
    generateSummary = true,
  ) {
    this.level = level;
    this.preserveEntities = preserveEntities;
    this.generateSummary = generateSummary;
  }

  /**
   * Compress content.
   *
   * @param content - Original content.
   * @returns CompressionResultV2.
   */
  compress(content: string): CompressionResultV2 {
    const originalLength = content.length;

    // Step 1: Extract entities
    const entities = this._extractEntities(content);

    // Step 2: Identify topics
    const topics = this._identifyTopics(content);

    // Step 3: Extract key points
    const keyPoints = this._extractKeyPoints(content);

    // Step 4: Generate summary
    const summary = this.generateSummary
      ? this._generateSummary(content, keyPoints, topics)
      : "";

    // Step 5: Compress content
    const compressed = this._compressContent(content, keyPoints, entities);

    const compressedLength = compressed.length;
    const ratio =
      originalLength > 0 ? Math.max(0, 1 - compressedLength / originalLength) : 0;

    return {
      originalLength,
      compressedLength,
      compressionRatio: ratio,
      preservedContent: compressed,
      summary,
      keyPoints,
      entities,
      topics,
    };
  }

  /** Extract important entities. */
  private _extractEntities(text: string): string[] {
    const entities = new Set<string>();

    for (const pattern of Object.values(this._entityPatterns)) {
      const matches = text.match(pattern);
      if (matches) {
        for (const m of matches) {
          entities.add(m);
        }
      }
    }

    return Array.from(entities).slice(0, 20);
  }

  /** Identify topics in content. */
  private _identifyTopics(text: string): string[] {
    const textLower = text.toLowerCase();
    const topics: string[] = [];

    for (const [topic, keywords] of Object.entries(this._topicKeywords)) {
      if (keywords.some((kw) => textLower.includes(kw))) {
        topics.push(topic);
      }
    }

    return topics.slice(0, 5);
  }

  /** Extract key points from content. */
  private _extractKeyPoints(content: string): string[] {
    // Split into sentences
    let sentences = content.split(/[.!?\n]+/);
    sentences = sentences
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    if (sentences.length === 0) return [];

    // Score each sentence
    const scored: Array<[string, number]> = sentences.map((sentence) => [
      sentence,
      this._scoreSentence(sentence),
    ]);

    // Sort by score descending
    scored.sort((a, b) => b[1] - a[1]);

    // Select top sentences based on compression level
    const targetCount = this._getTargetSentenceCount(sentences.length);

    // Get top sentences while maintaining order
    const selectedIndices = new Set<number>();
    for (const [sentence] of scored) {
      if (selectedIndices.size >= targetCount) break;
      const idx = sentences.findIndex(
        (s, i) => s === sentence && !selectedIndices.has(i),
      );
      if (idx >= 0) selectedIndices.add(idx);
    }

    // Sort by original position
    const result = Array.from(selectedIndices)
      .sort((a, b) => a - b)
      .map((i) => sentences[i]);

    return result;
  }

  /** Score sentence importance. */
  private _scoreSentence(sentence: string): number {
    let score = 0;
    const sentenceLower = sentence.toLowerCase();

    // Length factor (prefer medium length)
    const length = sentence.length;
    if (length >= 20 && length <= 100) score += 2;
    else if (length > 100 && length <= 200) score += 1;
    else if (length < 10) score -= 1;

    // Important keywords
    const importantKeywords = [
      "decide", "agree", "approve", "reject", "important", "critical",
      "need", "must", "should", "will", "plan", "schedule",
      "决定", "同意", "重要", "需要", "必须", "计划",
      "bug", "fix", "error", "issue", "problem", "solve",
    ];
    for (const kw of importantKeywords) {
      if (sentenceLower.includes(kw)) score += 2;
    }

    // Numbers and entities (likely important)
    if (/\d+/.test(sentence)) score += 1;

    // Question (keep for context)
    if (sentence.includes("?")) score += 0.5;

    return score;
  }

  /** Get target number of sentences based on compression level. */
  private _getTargetSentenceCount(total: number): number {
    switch (this.level) {
      case CompressionLevelV2.LIGHT:
        return Math.max(Math.round(total * 0.8), 1);
      case CompressionLevelV2.MEDIUM:
        return Math.max(Math.round(total * 0.5), 1);
      case CompressionLevelV2.AGGRESSIVE:
        return Math.max(Math.round(total * 0.3), 1);
      case CompressionLevelV2.ULTRA:
        return Math.max(Math.round(total * 0.15), 1);
      default:
        return Math.max(Math.round(total * 0.5), 1);
    }
  }

  /** Compress content while preserving key information. */
  private _compressContent(
    content: string,
    keyPoints: string[],
    entities: string[],
  ): string {
    if (keyPoints.length === 0) {
      // Fallback: truncate
      const maxLen = Math.round(content.length * (1 - this.level.valueOf()));
      return content.length > maxLen ? content.slice(0, maxLen) + "..." : content;
    }

    // Combine key points
    let compressed = keyPoints.join(". ");

    // Add entity reference if important
    if (this.preserveEntities && entities.length > 0) {
      compressed += ` [Entities: ${entities.slice(0, 5).join(", ")}]`;
    }

    // Ensure punctuation
    if (compressed.length > 0 && !compressed.endsWith(".")) {
      compressed += ".";
    }

    return compressed;
  }

  /** Generate a summary string. */
  private _generateSummary(
    _content: string,
    keyPoints: string[],
    topics: string[],
  ): string {
    const parts: string[] = [];

    if (topics.length > 0) {
      parts.push(`Topics: ${topics.join(", ")}`);
    }

    if (keyPoints.length > 0) {
      let first = keyPoints[0];
      if (first.length > 50) {
        first = first.slice(0, 50) + "...";
      }
      parts.push(`Summary: ${first}`);
    }

    return parts.join(" | ");
  }
}

// ── UltraCompressor ──────────────────────────────────────────────────────

export class UltraCompressor {
  private readonly _abbreviations: Record<string, string> = {
    information: "info",
    application: "app",
    example: "eg",
    number: "num",
    message: "msg",
    previous: "prev",
    following: "fol",
    including: "incl",
    without: "w/o",
    with: "w/",
  };

  private readonly _abbrevRe: RegExp;

  constructor() {
    const keys = Object.keys(this._abbreviations).join("|");
    this._abbrevRe = new RegExp(`\\b(${keys})\\b`, "gi");
  }

  /**
   * Ultra compress content.
   *
   * @param content - Original content.
   * @param maxLength - Maximum output length (default 200).
   * @returns Compressed content.
   */
  compress(content: string, maxLength = 200): string {
    // Extract core facts
    const facts = this._extractFacts(content);

    // Build compressed output
    let result = facts.join("; ");

    // Truncate if needed
    if (result.length > maxLength) {
      result = result.slice(0, maxLength - 3) + "...";
    }

    return result;
  }

  /** Extract core facts. */
  private _extractFacts(content: string): string[] {
    const sentences = content
      .split(/[.!?\n]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const facts: string[] = [];
    for (const sentence of sentences) {
      // Keep sentences with numbers, names, or key verbs
      if (/\d+/.test(sentence) || this._hasKeyVerb(sentence)) {
        // Abbreviate
        facts.push(this._abbreviate(sentence));
      }
    }

    return facts.slice(0, 5);
  }

  /** Check if sentence has key verbs. */
  private _hasKeyVerb(sentence: string): boolean {
    const verbs = [
      "decide", "agree", "create", "update", "delete",
      "send", "receive",
      "决定", "同意", "创建", "更新", "发送", "接收",
    ];
    return verbs.some((v) => sentence.toLowerCase().includes(v));
  }

  /** Apply abbreviations. */
  private _abbreviate(text: string): string {
    return text.replace(this._abbrevRe, (match) => {
      const lower = match.toLowerCase();
      return this._abbreviations[lower] ?? match;
    });
  }
}

// ── Global instances ─────────────────────────────────────────────────────

let _f5Compressor: F5CompressorV2 | undefined;
let _ultraCompressor: UltraCompressor | undefined;

export function getF5Compressor(
  level: CompressionLevelV2 = CompressionLevelV2.MEDIUM,
): F5CompressorV2 {
  if (_f5Compressor === undefined || _f5Compressor.level !== level) {
    _f5Compressor = new F5CompressorV2(level);
  }
  return _f5Compressor;
}

export function getUltraCompressor(): UltraCompressor {
  if (_ultraCompressor === undefined) {
    _ultraCompressor = new UltraCompressor();
  }
  return _ultraCompressor;
}

export function resetF5Compressor(): void {
  _f5Compressor = undefined;
}

export function resetUltraCompressor(): void {
  _ultraCompressor = undefined;
}

export function compressV2(
  content: string,
  level: CompressionLevelV2 = CompressionLevelV2.MEDIUM,
): CompressionResultV2 {
  const compressor = new F5CompressorV2(level);
  return compressor.compress(content);
}
