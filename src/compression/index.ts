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
 * claw-mem compression module -- Memory Compression (v2.12.0)
 *
 * Active memory compression based on Focus and ProMem papers.
 * Provides multiple compression strategies: V1, V2, F5 V2, and Spectrum.
 */

// V1 compressor
export {
  CompressionLevel,
  MemoryCompressor,
  KeyInformationExtractor,
  getCompressor as getCompressorV1,
  resetCompressor as resetCompressorV1,
  compressMemory,
  type CompressionResult,
} from "./memory_compression";

// V2 compressor (recommended)
export {
  MemoryCompressorV2,
  SemanticDeduplicator,
  KnowledgeBlock,
  KnowledgeEntry,
  CompressionTrigger,
  DEFAULT_COMPRESSION_CONFIG,
  compressionConfigToDict,
  createCompressionResult,
  compressionResultToDict,
  createKnowledgeEntry,
  knowledgeEntryToDict,
  knowledgeEntryFromDict,
  getCompressor,
  resetCompressor,
  type CompressionConfig,
} from "./memory_compression_v2";

// F5 V2 compressor
export {
  CompressionLevelV2,
  F5CompressorV2,
  UltraCompressor,
  getF5Compressor,
  getUltraCompressor,
  resetF5Compressor,
  resetUltraCompressor,
  compressV2,
  type CompressionResultV2,
} from "./f5_v2";

// Compression spectrum
export {
  CompressionSpectrum,
  type SkillEntry,
  type RuleEntry,
  type PrincipleEntry,
  type CompressedMemory,
  type SpectrumMemoryManager,
} from "./spectrum";
