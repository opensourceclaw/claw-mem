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
import { PatternMiner, EmergenceDetector, TrendAnalyzer } from "../../src/emergence";

describe("Emergence integration", () => {
  it("should run full pipeline: pool → mine → score → gate → trends", () => {
    const pool = new MemoryPool();
    const now = Date.now() / 1000;

    // Simulate 3 agents all reporting login issues
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login page crash", tags: ["bug", "login", "critical"], timestamp: now - 5000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login redirect loop", tags: ["bug", "login"], timestamp: now - 4000 }, "agent-2",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login token expiry", tags: ["bug", "login", "auth"], timestamp: now - 3000 }, "agent-3",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login OAuth flow broken", tags: ["bug", "login", "auth"], timestamp: now - 2000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Login session timeout", tags: ["bug", "login"], timestamp: now - 1000 }, "agent-2",
    ));

    // Pattern mining
    const miner = new PatternMiner(pool);
    const freqs = miner.frequencyAnalysis();
    const login = freqs.find((f) => f.tag === "login")!;
    expect(login).toBeDefined();
    expect(login.count).toBe(5);
    expect(login.agentCount).toBe(3);

    const corrs = miner.correlationAnalysis();
    const loginBug = corrs.find((c) =>
      (c.tagA === "bug" && c.tagB === "login") || (c.tagA === "login" && c.tagB === "bug"),
    );
    expect(loginBug).toBeDefined();
    expect(loginBug!.cooccurrence).toBeGreaterThanOrEqual(4);

    const cross = miner.crossAgentPatterns();
    expect(cross.length).toBeGreaterThan(0);

    // Detection
    const detector = new EmergenceDetector(miner, 3);
    const records = pool.query({});
    const patterns = detector.detect(records);
    expect(patterns.length).toBeGreaterThan(0);

    // At least one cross_agent pattern for bug+login across 3 agents
    const crossPatterns = patterns.filter((p) => p.type === "cross_agent");
    expect(crossPatterns.length).toBeGreaterThan(0);

    // Trends
    const analyzer = new TrendAnalyzer(pool);
    const line = analyzer.track("login", 2000);
    expect(line.tag).toBe("login");
    expect(line.points.length).toBeGreaterThan(0);
  });
});
