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
  DEFAULT_DREAMING_CONFIG,
  validateDreamingConfig,
} from "../../src/dreaming/config";
import { createSignal, SignalIngestor, type Signal } from "../../src/dreaming/light";
import {
  CandidateScorer,
  createScoredCandidate,
} from "../../src/dreaming/deep";
import { DreamingPipeline, type DreamingResult } from "../../src/dreaming/pipeline";
import {
  Promoter,
  createPromotionResult,
  type MemoryManagerWithStorage,
} from "../../src/dreaming/promote";
import { createREMResult, PatternExtractor } from "../../src/dreaming/rem";
import { describe, it, expect } from "vitest";
import assert from "assert";

// --------------------------------------------------------------------------
// Test 1: DreamingConfig validation
// --------------------------------------------------------------------------
describe("DreamingConfig", () => {
  it("default config weights sum to ~1.0", () => {
    assert.ok(validateDreamingConfig(DEFAULT_DREAMING_CONFIG));
  });

  it("invalid config fails validation", () => {
    const bad = { ...DEFAULT_DREAMING_CONFIG, frequencyWeight: 0.99 };
    assert.ok(!validateDreamingConfig(bad));
  });
});

// --------------------------------------------------------------------------
// Test 2: Light phase -- SignalIngestor with mock memory manager
// --------------------------------------------------------------------------
describe("SignalIngestor", () => {
  it("stages signals from episodic memories and deduplicates", () => {
    const mockMM = {
      episodic: {
        getRecent(_count: number) {
          return [
            { id: "m1", content: "Alice met Bob", tags: ["meeting"], type: "episodic", timestamp: "2026-05-01T00:00:00" },
            { id: "m2", content: "Alice met Bob", tags: ["meeting"], type: "episodic", timestamp: "2026-05-01T01:00:00" },
            { id: "m3", content: "New insight about Rust", tags: ["tech"], type: "episodic", timestamp: "2026-05-02T00:00:00" },
          ];
        },
      },
      semantic: {
        getAll() {
          return [{ id: "s1", content: "Existing semantic fact" }];
        },
      },
    };

    const ingestor = new SignalIngestor(mockMM as any);
    const count = ingestor.ingest();
    // m1 and m2 are duplicates (same content), m3 is unique and not a substring of s1
    // => 2 unique content signals staged
    assert.strictEqual(count, 2);

    const staged = ingestor.getStaged();
    // First staged (Alice met Bob) should have recallCount = 2
    const aliceSignal = staged.find((s) => (s.content as string).includes("Alice"));
    assert.ok(aliceSignal);
    assert.strictEqual(aliceSignal!.recall_count, 2);

    // Third signal is fresh
    const rustSignal = staged.find((s) => (s.content as string).includes("Rust"));
    assert.ok(rustSignal);
    assert.strictEqual(rustSignal!.memory_type, "episodic");
  });

  it("deduplicates against existing semantic memory", () => {
    const mockMM = {
      episodic: {
        getRecent(_count: number) {
          return [
            { id: "m1", content: "Existing semantic fact", tags: [], type: "episodic", timestamp: "" },
            { id: "m2", content: "Brand new content", tags: [], type: "episodic", timestamp: "" },
          ];
        },
      },
      semantic: {
        getAll() {
          return [{ id: "s1", content: "Existing semantic fact" }];
        },
      },
    };

    const ingestor = new SignalIngestor(mockMM as any);
    const count = ingestor.ingest();
    // Only "Brand new content" should pass dedup
    assert.strictEqual(count, 1);
  });
});

// --------------------------------------------------------------------------
// Test 3: Deep phase -- CandidateScorer scoring and filtering
// --------------------------------------------------------------------------
describe("CandidateScorer", () => {
  it("scores signals and filters by threshold", () => {
    const signals: Signal[] = [
      createSignal({
        memoryId: "a",
        content: "Alice went to Paris for a Conference",
        recallCount: 10,
        uniqueQueries: 5,
        relevanceScores: [0.9, 0.8],
        tags: ["travel", "work"],
        timestamp: new Date().toISOString(),
      }),
      createSignal({
        memoryId: "b",
        content: "short",
        recallCount: 1,
        uniqueQueries: 1,
        relevanceScores: [],
        tags: [],
        timestamp: "",
      }),
    ];

    const scorer = new CandidateScorer(DEFAULT_DREAMING_CONFIG);
    const all = scorer.scoreAll(signals);
    assert.strictEqual(all.length, 2);
    // First candidate should have higher composite
    assert.ok(all[0].composite > all[1].composite);

    const filtered = scorer.filter(all);
    assert.ok(filtered.length >= 1);
    // The low-score "short" signal should not pass an aggressive threshold
    assert.ok(filtered.every((c) => c.composite >= DEFAULT_DREAMING_CONFIG.scoreThreshold));
  });
});

// --------------------------------------------------------------------------
// Test 4: Pipeline dry_run mode
// --------------------------------------------------------------------------
describe("DreamingPipeline", () => {
  it("dry_run returns result without persisting", () => {
    const mockMM = {
      episodic: {
        getRecent(_count: number) {
          return [
            { id: "m1", content: "User discussed TypeScript types", tags: ["ts", "types"], type: "episodic", timestamp: new Date().toISOString() },
            { id: "m2", content: "User installed pnpm", tags: ["tool"], type: "episodic", timestamp: new Date().toISOString() },
          ];
        },
      },
      semantic: {
        getAll() {
          return [];
        },
        store(_data: Record<string, unknown>) {},
        update(_id: string, _content: string) {},
      },
      procedural: {
        store(_data: Record<string, unknown>) {},
      },
    };

    const config = { ...DEFAULT_DREAMING_CONFIG, dryRun: true };
    const pipeline = new DreamingPipeline(mockMM as any, config);
    const result: DreamingResult = pipeline.run();

    assert.ok(result.durationMs >= 0);
    assert.ok(result.staged >= 1);
    assert.ok(result.scored >= 1);
    // dry_run should be true
    assert.strictEqual(result.dryRun, true);
    assert.strictEqual(result.error, undefined);
  });
});

// --------------------------------------------------------------------------
// Test 5: Promoter dry_run behavior
// --------------------------------------------------------------------------
describe("Promoter", () => {
  it("dry run counts promotions without persisting", () => {
    const signal: Signal = createSignal({
      memoryId: "t1",
      content: "test content",
      memoryType: "episodic",
      recallCount: 3,
      tags: ["test"],
      timestamp: new Date().toISOString(),
    });

    const candidate = createScoredCandidate(signal, {
      frequencyScore: 0.3,
      relevanceScore: 0.5,
      composite: 0.4,
    });

    const remResult = createREMResult();

    const mockMM: MemoryManagerWithStorage = {
      semantic: {
        store(_data: Record<string, unknown>) {},
        getAll() { return []; },
        update(_id: string, _content: string) {},
      },
      procedural: {
        store(_data: Record<string, unknown>) {},
      },
    };

    const promoter = new Promoter(mockMM, true);
    const result = promoter.promote([candidate], remResult);
    assert.strictEqual(result.episodicPromoted, 1);
    assert.strictEqual(result.dryRun, true);
    assert.strictEqual(result.semanticReinforced, 0);
  });
});

// --------------------------------------------------------------------------
// Test 6: REM phase -- PatternExtractor builds triplets and summaries
// --------------------------------------------------------------------------
describe("PatternExtractor", () => {
  it("builds triplets and topic summaries from candidates", () => {
    const signals: Signal[] = [
      createSignal({
        memoryId: "r1",
        content: "TypeScript: A typed superset of JavaScript",
        tags: ["typescript", "language"],
      }),
      createSignal({
        memoryId: "r2",
        content: "Functional programming in Rust",
        tags: ["rust", "functional"],
      }),
    ];

    const scorer = new CandidateScorer(DEFAULT_DREAMING_CONFIG);
    const candidates = scorer.scoreAll(signals);

    const extractor = new PatternExtractor();
    const result = extractor.extract(candidates);

    assert.strictEqual(result.extractedCount, 2);
    assert.ok(result.triplets.length >= 1);
    // Check triplet structure
    const tsTriplet = result.triplets.find((t) => t.s.includes("TypeScript"));
    assert.ok(tsTriplet);
    assert.strictEqual(tsTriplet!.p, "relates_to");

    // Topic summaries should be built from tags
    assert.ok(Object.keys(result.topicSummaries).length > 0);
    assert.ok(result.topicSummaries["typescript"] || result.topicSummaries["rust"]);
  });
});
