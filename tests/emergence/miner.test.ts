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
import { PatternMiner } from "../../src/emergence";

function seed(pool: MemoryPool) {
  pool.store(AgentAgnosticMemory.to_shared_format(
    { content: "Auth module", tags: ["auth", "security"], timestamp: 1000 }, "agent-1",
  ));
  pool.store(AgentAgnosticMemory.to_shared_format(
    { content: "Auth config", tags: ["auth", "config"], timestamp: 2000 }, "agent-1",
  ));
  pool.store(AgentAgnosticMemory.to_shared_format(
    { content: "Deploy pipeline", tags: ["deploy", "ci"], timestamp: 3000 }, "agent-2",
  ));
  pool.store(AgentAgnosticMemory.to_shared_format(
    { content: "Security audit", tags: ["security", "audit"], timestamp: 4000 }, "agent-2",
  ));
}

describe("PatternMiner", () => {
  it("frequencyAnalysis returns sorted by count", () => {
    const pool = new MemoryPool();
    seed(pool);
    const miner = new PatternMiner(pool);

    const freqs = miner.frequencyAnalysis();
    expect(freqs.length).toBeGreaterThan(0);
    expect(freqs[0].count).toBeGreaterThanOrEqual(freqs[freqs.length - 1].count);
  });

  it("frequencyAnalysis tracks agentCount", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["shared"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["shared"] }, "agent-2",
    ));
    const miner = new PatternMiner(pool);

    const freqs = miner.frequencyAnalysis();
    const shared = freqs.find((f) => f.tag === "shared")!;
    expect(shared.agentCount).toBe(2);
  });

  it("correlationAnalysis lift > 1 for co-occurring tags", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["alpha", "beta"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["alpha", "beta"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "C", tags: ["gamma"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "D", tags: ["delta"] }, "agent-1",
    ));
    const miner = new PatternMiner(pool);

    const corrs = miner.correlationAnalysis();
    const ab = corrs.find((c) => c.tagA === "alpha" && c.tagB === "beta")!;
    expect(ab).toBeDefined();
    expect(ab.lift).toBeGreaterThan(1);
  });

  it("correlationAnalysis lift ≈ 1 for independent tags", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["alpha"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["alpha"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "C", tags: ["beta"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "D", tags: ["beta"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "E", tags: ["alpha", "beta"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "F", tags: ["alpha", "beta"] }, "agent-1",
    ));
    const miner = new PatternMiner(pool);

    const corrs = miner.correlationAnalysis();
    const ab = corrs.find((c) => c.tagA === "alpha" && c.tagB === "beta")!;
    expect(ab).toBeDefined();
    expect(ab.lift).toBeLessThanOrEqual(2);
  });

  it("crossAgentPatterns requires ≥ 2 agents", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["solo"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["solo"] }, "agent-1",
    ));
    const miner = new PatternMiner(pool);

    const patterns = miner.crossAgentPatterns();
    expect(patterns.length).toBe(0);
  });

  it("crossAgentPatterns groups by shared tags across agents", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["bug", "frontend"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["bug", "frontend"] }, "agent-2",
    ));
    const miner = new PatternMiner(pool);

    const patterns = miner.crossAgentPatterns();
    expect(patterns.length).toBe(1);
    expect(patterns[0].agents.length).toBe(2);
    expect(patterns[0].commonTags).toContain("bug");
  });
});
