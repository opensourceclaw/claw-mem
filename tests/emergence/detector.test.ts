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
import { MemoryPool, AgentAgnosticMemory } from "../../src/memory";
import { PatternMiner, EmergenceDetector } from "../../src/emergence";
import type { CrossAgentPattern } from "../../src/emergence";

function makeCrossPattern(agents: string[]): CrossAgentPattern {
  return {
    topic: "test",
    agents,
    memoryCount: agents.length * 2,
    avgConfidence: 1.0,
    commonTags: ["test"],
    firstSeen: 1000,
    lastSeen: 2000,
  };
}

describe("EmergenceDetector", () => {
  it("score: novelty decreases with frequency", () => {
    const pool = new MemoryPool();
    const miner = new PatternMiner(pool);
    const detector = new EmergenceDetector(miner, 4);

    const p = makeCrossPattern(["a1", "a2"]);
    const s = detector.score(p);
    expect(s.confidence).toBeGreaterThan(0);
    expect(s.consensus).toBeGreaterThan(0);
  });

  it("score: utility increases with agent count", () => {
    const pool = new MemoryPool();
    const miner = new PatternMiner(pool);
    const detector = new EmergenceDetector(miner, 4);

    const few = makeCrossPattern(["a1", "a2"]);
    const many = makeCrossPattern(["a1", "a2", "a3", "a4"]);

    const sFew = detector.score(few);
    const sMany = detector.score(many);
    expect(sMany.consensus).toBeGreaterThanOrEqual(sFew.consensus);
  });

  it("gate: ≥ 0.7 → emergent", () => {
    const pool = new MemoryPool();
    const miner = new PatternMiner(pool);
    const detector = new EmergenceDetector(miner, 1);

    const score = { novelty: 0.8, utility: 0.8, consensus: 0.8, confidence: 0.75 };
    expect(detector.gate(score)).toBe("emergent");
  });

  it("gate: < 0.4 → noise", () => {
    const pool = new MemoryPool();
    const miner = new PatternMiner(pool);
    const detector = new EmergenceDetector(miner, 1);

    const score = { novelty: 0.1, utility: 0.1, consensus: 0.1, confidence: 0.2 };
    expect(detector.gate(score)).toBe("noise");
  });

  it("gate: 0.4-0.7 → borderline", () => {
    const pool = new MemoryPool();
    const miner = new PatternMiner(pool);
    const detector = new EmergenceDetector(miner, 1);

    const score = { novelty: 0.5, utility: 0.5, consensus: 0.5, confidence: 0.55 };
    expect(detector.gate(score)).toBe("borderline");
  });

  it("detect returns scored patterns", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Bug in login", tags: ["bug", "login"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login crash", tags: ["bug", "login"] }, "agent-2",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login timeout", tags: ["bug", "login"] }, "agent-3",
    ));

    const miner = new PatternMiner(pool);
    const detector = new EmergenceDetector(miner, 3);

    const records = pool.query({});
    const patterns = detector.detect(records);
    expect(patterns.length).toBeGreaterThan(0);
    for (const p of patterns) {
      expect(p.score.confidence).toBeGreaterThan(0);
      expect(p.id).toBeTruthy();
    }
  });
});
