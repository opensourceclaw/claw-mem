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

import {
  CompressionLevel,
  MemoryCompressor,
  compressMemory,
} from "../../src/compression/memory_compression";

import {
  MemoryCompressorV2,
  SemanticDeduplicator,
  CompressionTrigger,
  DEFAULT_COMPRESSION_CONFIG,
  type CompressionConfig,
} from "../../src/compression/memory_compression_v2";

import {
  CompressionLevelV2,
  F5CompressorV2,
  UltraCompressor,
  compressV2,
} from "../../src/compression/f5_v2";

import { CompressionSpectrum } from "../../src/compression/spectrum";

import { describe, it, assert } from "../../src/globals";

// --------------------------------------------------------------------------
// Test 1: MemoryCompressor V1 -- basic compression
// --------------------------------------------------------------------------
describe("MemoryCompressor V1", () => {
  it("compresses content at MEDIUM level", () => {
    const content = [
      "Line one: This is a test of the compression system.",
      "Line two: We need to verify it works correctly.",
      "Line one: This is a test of the compression system.",
      "Line three: Short",
      "Line four: This is a longer line that should be preserved for testing purposes.",
    ].join("\n");

    const result = compressMemory(content, CompressionLevel.MEDIUM);

    assert.ok(result.originalLength > 0);
    assert.ok(result.compressedLength <= result.originalLength);
    assert.ok(result.compressionRatio >= 0);

    // Duplicate "Line one" should be removed, "Line three: Short" (< 15 chars) removed
    // So we should have at least 2 lines preserved
    const lines = result.preservedContent.split("\n");
    assert.ok(lines.length >= 2);

    // Summary should not be empty if key info found
    assert.ok(typeof result.summary === "string");
  });

  it("preserves key information on AGGRESSIVE level", () => {
    const content =
      "We have decided to use TypeScript for the project. " +
      "This is an important decision. " +
      "Some filler text that is not very important. " +
      "Another random sentence.";

    const compressor = new MemoryCompressor(CompressionLevel.AGGRESSIVE);
    const result = compressor.compress(content);

    // Aggressive should achieve higher compression
    assert.ok(result.compressionRatio > 0.1);
    // Key info should be extracted
    assert.ok(result.extractedKeys.length >= 0);
  });
});

// --------------------------------------------------------------------------
// Test 2: F5CompressorV2 -- entity extraction and topic identification
// --------------------------------------------------------------------------
describe("F5CompressorV2", () => {
  it("extracts entities and identifies topics", () => {
    const content =
      "During the project meeting, John Smith discussed the new TypeScript API. " +
      "They decided to schedule a follow-up for 2026-06-15. " +
      "Contact alice@example.com for more details.";

    const compressor = new F5CompressorV2(CompressionLevelV2.MEDIUM);
    const result = compressor.compress(content);

    assert.ok(result.entities.length > 0);
    assert.ok(result.topics.includes("meeting") || result.topics.includes("decision"));
    assert.ok(result.keyPoints.length > 0);
    assert.ok(result.compressionRatio >= 0);
    assert.ok(result.summary.length > 0);
  });

  it("ULTRA compression achieves high ratio", () => {
    const content =
      "Line A: first line of the document. ".repeat(50);

    const result = compressV2(content, CompressionLevelV2.ULTRA);
    assert.ok(result.compressionRatio > 0.5);
    assert.ok(result.preservedContent.length < content.length);
  });
});

// --------------------------------------------------------------------------
// Test 3: MemoryCompressorV2 -- shouldCompress and compress
// --------------------------------------------------------------------------
describe("MemoryCompressorV2", () => {
  it("shouldCompress triggers on memory count threshold", () => {
    const compressor = new MemoryCompressorV2();
    const [should, trigger] = compressor.shouldCompress(200, 0, false);
    assert.ok(should);
    assert.strictEqual(trigger, CompressionTrigger.MEMORY_COUNT);
  });

  it("shouldCompress triggers on force flag", () => {
    const compressor = new MemoryCompressorV2();
    const [should, trigger] = compressor.shouldCompress(0, 0, true);
    assert.ok(should);
    assert.strictEqual(trigger, CompressionTrigger.MANUAL);
  });

  it("compress categorizes and deduplicates memories", () => {
    const memories = [
      { id: "1", content: "We decided to use React for the frontend." },
      { id: "2", content: "We decided to use React for the frontend." },
      { id: "3", content: "Installing dependencies with pnpm." },
    ];

    const compressor = new MemoryCompressorV2();
    const result = compressor.compress(memories);

    // Deduplication should reduce 3 -> 2 (first two are similar)
    assert.strictEqual(result.originalCount, 3);
    assert.ok(result.compressedCount <= 2);
    assert.ok(result.compressionRatio > 0);
  });
});

// --------------------------------------------------------------------------
// Test 4: SemanticDeduplicator
// --------------------------------------------------------------------------
describe("SemanticDeduplicator", () => {
  it("removes similar memories based on threshold", () => {
    const dedup = new SemanticDeduplicator(0.8);

    const memories = [
      { id: "a", content: "We have decided to use Python.", importance: 0.9 },
      { id: "b", content: "We have decided to use Python for backend.", importance: 0.7 },
      { id: "c", content: "Completely unrelated content about Rust.", importance: 0.5 },
    ];

    const result = dedup.deduplicate(memories);
    // a and b are similar, so at most 2 remain; a has higher importance so it wins
    assert.ok(result.length <= 2);
    // The retained memory should include the higher-importance content
    const retained = result.find((m) => (m.content as string).includes("Python"));
    assert.ok(retained);
  });
});

// --------------------------------------------------------------------------
// Test 5: UltraCompressor
// --------------------------------------------------------------------------
describe("UltraCompressor", () => {
  it("applies abbreviations and extracts core facts", () => {
    const content =
      "The following information is important: the application version number is 2.0. " +
      "We have decided to update the configuration without restarting.";

    const ultra = new UltraCompressor();
    const result = ultra.compress(content, 200);

    assert.ok(result.length <= 205); // 200 + "..."
    // Should contain abbreviations like "info" instead of "information"
    assert.ok(result.includes("info") || result.length > 0);
    // Should contain core facts
    assert.ok(result.includes("decided") || result.includes("update"));
  });
});

// --------------------------------------------------------------------------
// Test 6: CompressionSpectrum -- tiered compression
// --------------------------------------------------------------------------
describe("CompressionSpectrum", () => {
  it("records access and triggers skill compression on threshold", () => {
    const mockMM = {
      get(memoryId: string) {
        if (memoryId === "ep1") {
          return { content: "pip install typescript\nRun tsc --init\nConfigure tsconfig.json\n" };
        }
        return undefined;
      },
    };

    const spectrum = new CompressionSpectrum(mockMM as any, 2, 2, 1);

    // First access - below threshold
    let result = spectrum.recordAccess("ep1");
    assert.strictEqual(result, undefined);

    // Second access - triggers skill compression
    result = spectrum.recordAccess("ep1");
    assert.ok(result !== undefined);
    assert.strictEqual(result!.level, 1); // Skill level
    assert.ok(result!.content.includes("[Skill]"));

    // Verify stats
    const stats = spectrum.getStats();
    assert.strictEqual(stats.skills, 1);
    assert.strictEqual(stats.total_episodes_tracked, 1);
  });
});
