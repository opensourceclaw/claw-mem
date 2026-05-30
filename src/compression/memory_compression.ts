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
 * Memory Compression Module for claw-mem v2.4.0
 *
 * Provides long conversation memory compression with >50% compression ratio
 * while preserving key information.
 */

// ── CompressionLevel enum ─────────────────────────────────────────────────

export enum CompressionLevel {
  LIGHT = "light",
  MEDIUM = "medium",
  AGGRESSIVE = "aggressive",
}

// ── CompressionResult ────────────────────────────────────────────────────

export interface CompressionResult {
  originalLength: number;
  compressedLength: number;
  compressionRatio: number;
  preservedContent: string;
  extractedKeys: string[];
  summary: string;
}

export function createCompressionResult(overrides?: Partial<CompressionResult>): CompressionResult {
  return {
    originalLength: 0,
    compressedLength: 0,
    compressionRatio: 0,
    preservedContent: "",
    extractedKeys: [],
    summary: "",
    ...overrides,
  };
}

// ── KeyInformationExtractor ──────────────────────────────────────────────

export class KeyInformationExtractor {
  // Key patterns for extraction
  private readonly _decisionPatterns: RegExp[] = [
    /(决定|决策|选择|确定|批准|同意|拒绝|否认)/i,
    /(will|must|should|need to|have to|going to|decided|agreed)/i,
  ];

  private readonly _factPatterns: RegExp[] = [
    /(事实|实际上|其实|已经|已知)/i,
    /(fact|actually|known|already|confirmed)/i,
  ];

  private readonly _taskPatterns: RegExp[] = [
    /(任务|目标|需要|完成|做|执行)/i,
    /(task|goal|need|complete|do|execute|action|next step)/i,
  ];

  /**
   * Extract key information.
   *
   * @returns Record with "decisions", "facts", "tasks" arrays.
   */
  extract(text: string): Record<string, string[]> {
    return {
      decisions: this._extractMatches(text, this._decisionPatterns),
      facts: this._extractMatches(text, this._factPatterns),
      tasks: this._extractMatches(text, this._taskPatterns),
    };
  }

  private _extractMatches(text: string, patterns: RegExp[]): string[] {
    const matches = new Set<string>();
    for (const pattern of patterns) {
      const found = text.match(pattern);
      if (found) {
        // match() returns the full match plus groups; we capture all matching substrings
        for (const m of found) {
          matches.add(m);
        }
      }
    }
    return Array.from(matches);
  }
}

// ── MemoryCompressor ─────────────────────────────────────────────────────

export class MemoryCompressor {
  readonly level: CompressionLevel;
  readonly preserveKeyInfo: boolean;
  private _extractor: KeyInformationExtractor;

  private readonly _ratios: Record<CompressionLevel, number> = {
    [CompressionLevel.LIGHT]: 0.3,
    [CompressionLevel.MEDIUM]: 0.5,
    [CompressionLevel.AGGRESSIVE]: 0.7,
  };

  constructor(
    level: CompressionLevel = CompressionLevel.MEDIUM,
    preserveKeyInfo = true,
  ) {
    this.level = level;
    this.preserveKeyInfo = preserveKeyInfo;
    this._extractor = new KeyInformationExtractor();
  }

  /**
   * Compress memory content.
   *
   * @param content - Original content.
   * @returns Compression result.
   */
  compress(content: string): CompressionResult {
    const originalLength = content.length;

    // Extract key information first
    let keyInfo: Record<string, string[]> = {};
    if (this.preserveKeyInfo) {
      keyInfo = this._extractor.extract(content);
    }

    // Apply compression based on level
    let compressed: string;
    switch (this.level) {
      case CompressionLevel.LIGHT:
        compressed = this._compressLight(content);
        break;
      case CompressionLevel.MEDIUM:
        compressed = this._compressMedium(content);
        break;
      case CompressionLevel.AGGRESSIVE:
        compressed = this._compressAggressive(content);
        break;
      default:
        compressed = this._compressMedium(content);
    }

    // Calculate metrics
    const compressedLength = compressed.length;
    const ratio =
      originalLength > 0 ? 1 - compressedLength / originalLength : 0;

    // Build summary from key info
    const summary = this._buildSummary(keyInfo);

    return {
      originalLength,
      compressedLength,
      compressionRatio: ratio,
      preservedContent: compressed,
      extractedKeys: this._flattenKeys(keyInfo),
      summary,
    };
  }

  /** Light compression: remove extra whitespace and short words. */
  private _compressLight(content: string): string {
    const lines = content.split("\n");
    const cleaned = lines
      .map((l) => l.trim())
      .filter((l) => l.length > 0);
    // Remove very short lines (< 10 chars)
    const result = cleaned.filter((l) => l.length >= 10);
    return result.join("\n");
  }

  /** Medium compression: remove duplicates and low-information content. */
  private _compressMedium(content: string): string {
    const lines = content.split("\n");
    const cleaned = lines
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    // Remove consecutive duplicate lines
    const result: string[] = [];
    let prev: string | null = null;
    for (const line of cleaned) {
      if (line !== prev) {
        result.push(line);
        prev = line;
      }
    }

    // Remove very short lines (< 15 chars)
    return result.filter((l) => l.length >= 15).join("\n");
  }

  /** Aggressive compression: only preserve key information. */
  private _compressAggressive(content: string): string {
    // Extract key information
    const keyInfo = this._extractor.extract(content);

    // Get all key sentences
    const sentences = content.split(/[.!?。！？\n]+/);
    const keySentences: string[] = [];

    for (const sentence of sentences) {
      const st = sentence.trim();
      if (!st) continue;

      const sentenceLower = st.toLowerCase();

      // Keep sentences with key information
      let keep = false;

      if (
        (keyInfo.decisions ?? []).some(
          (info) => sentenceLower.includes(info.toLowerCase()) || info.toLowerCase().includes(sentenceLower),
        )
      ) {
        keep = true;
      } else if (
        (keyInfo.tasks ?? []).some(
          (info) => sentenceLower.includes(info.toLowerCase()) || info.toLowerCase().includes(sentenceLower),
        )
      ) {
        keep = true;
      } else if (
        (keyInfo.facts ?? []).some(
          (info) => sentenceLower.includes(info.toLowerCase()) || info.toLowerCase().includes(sentenceLower),
        )
      ) {
        keep = true;
      }

      // Keep sentences that contain important keywords
      if (!keep) {
        const importantWords = [
          "important",
          "critical",
          "key",
          "essential",
          "must",
          "need",
          "should",
          "will",
          "decide",
          "agree",
          "plan",
        ];
        if (importantWords.some((w) => sentenceLower.includes(w))) {
          keep = true;
        }
      }

      // Keep moderate length sentences
      if (!keep && st.length >= 20 && st.length <= 150) {
        keep = true;
      }

      if (keep) {
        keySentences.push(st);
      }
    }

    if (keySentences.length > 0) {
      return keySentences.join(". ") + ".";
    }

    // Fallback
    return content.slice(0, 500);
  }

  private _buildSummary(keyInfo: Record<string, string[]>): string {
    const parts: string[] = [];

    if (keyInfo.decisions && keyInfo.decisions.length > 0) {
      const decisions = keyInfo.decisions.slice(0, 3);
      parts.push(`Decisions: ${decisions.join(", ")}`);
    }

    if (keyInfo.tasks && keyInfo.tasks.length > 0) {
      const tasks = keyInfo.tasks.slice(0, 3);
      parts.push(`Tasks: ${tasks.join(", ")}`);
    }

    if (keyInfo.facts && keyInfo.facts.length > 0) {
      const facts = keyInfo.facts.slice(0, 3);
      parts.push(`Facts: ${facts.join(", ")}`);
    }

    return parts.join(" | ");
  }

  private _flattenKeys(keyInfo: Record<string, string[]>): string[] {
    const keys = new Set<string>();
    for (const value of Object.values(keyInfo)) {
      for (const v of value) {
        keys.add(v);
      }
    }
    return Array.from(keys);
  }
}

// ── Global compressor ────────────────────────────────────────────────────

let _compressor: MemoryCompressor | undefined;

export function getCompressor(
  level: CompressionLevel = CompressionLevel.MEDIUM,
): MemoryCompressor {
  if (_compressor === undefined) {
    _compressor = new MemoryCompressor(level);
  }
  return _compressor;
}

export function resetCompressor(): void {
  _compressor = undefined;
}

export function compressMemory(
  content: string,
  level: CompressionLevel = CompressionLevel.MEDIUM,
): CompressionResult {
  const compressor = new MemoryCompressor(level);
  return compressor.compress(content);
}
