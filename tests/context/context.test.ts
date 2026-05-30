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

import { describe, it, expect } from "vitest";
import { ConfidenceGate, ConfidenceLevel } from "../../src/context";
import { MemoryInjector } from "../../src/context/memory_injector";

describe("ConfidenceGate", () => {
  it("should classify confidence levels by composite score", () => {
    const gate = new ConfidenceGate();

    // High confidence: all scores high
    const highResult = gate.evaluate({
      score: 0.9,
      tags: ["critical"],
    });
    expect(highResult.confidence_level).toBe(ConfidenceLevel.HIGH);
    expect(highResult.confidence_score).toBeGreaterThanOrEqual(0.7);

    // Low confidence: all scores low
    const lowResult = gate.evaluate({
      score: 0.0,
      tags: [],
    });
    expect(lowResult.confidence_level).toBe(ConfidenceLevel.LOW);
    expect(lowResult.confidence_score).toBeLessThan(0.4);
  });

  it("should filter out LOW confidence memories in batch", () => {
    const gate = new ConfidenceGate();
    const memories = [
      { id: "m1", score: 0.9, tags: ["important"] },
      { id: "m2", score: 0.1, tags: [] },
      { id: "m3", score: 0.8, tags: [] },
    ];

    const kept = gate.filter(memories);
    expect(kept.length).toBeLessThan(memories.length);
    // LOW items should be dropped
    const keptIds = kept.map((m) => m.id);
    // m2 has score 0.0 + 0.5 (no tags) = 0.5 composite → MEDIUM with default thresholds
    // Actually: vec=0.1, time=N/A→redistributed, conflict=N/A→redistributed, freq=0.5
    // With redistribution: w_vec=0.4/(0.4+0.1)=0.8, w_freq=0.2 → composite = 0.1*0.8+0.5*0.2=0.08+0.1=0.18
    expect(keptIds).not.toContain("m2");
  });
});

describe("MemoryInjector", () => {
  it("should pass through all stages and return pipeline metadata", () => {
    const injector = new MemoryInjector(undefined, 2000, 0.8, 0.3);

    const memories = [
      { id: "m1", content: "first memory", score: 0.9, created_at: new Date().toISOString() },
      { id: "m2", content: "second memory", score: 0.6, created_at: new Date().toISOString() },
      { id: "m3", content: "third memory", score: 0.2, created_at: new Date().toISOString() },
    ];

    const result = injector.refine(memories);
    expect(result.total_candidates).toBe(3);
    expect(result.refined_memories.length).toBeGreaterThan(0);
    expect(result.refined_memories.length).toBeLessThanOrEqual(3);
    expect(result.total_removed).toBeGreaterThanOrEqual(0);
    expect(result.max_allowed).toBe(2000);
    expect(result.metadata.stages).toBeDefined();
    expect(Array.isArray(result.metadata.stages)).toBe(true);
  });

  it("should apply diversity dedup to remove near-duplicates", () => {
    const injector = new MemoryInjector(undefined, 5000, 0.5, 0.0);

    // Two very similar memories
    const memories = [
      { id: "m1", content: "User prefers Python for backend development", score: 0.9 },
      { id: "m2", content: "User prefers Python for backend development tasks", score: 0.85 },
      { id: "m3", content: "User likes JavaScript for frontend", score: 0.7 },
    ];

    const result = injector.refine(memories);
    // m1 and m2 should be deduped (high jaccard similarity)
    expect(result.refined_memories.length).toBeLessThan(3);
    expect(result.diversity_removed).toBeGreaterThanOrEqual(1);
  });
});
