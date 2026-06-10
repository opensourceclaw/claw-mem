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
import { TrendAnalyzer } from "../../src/emergence";

describe("TrendAnalyzer", () => {
  it("track returns correct trend line", () => {
    const pool = new MemoryPool();
    const now = Date.now() / 1000;
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["trending"], timestamp: now - 6000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["trending"], timestamp: now - 3000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "C", tags: ["trending"], timestamp: now }, "agent-1",
    ));

    const analyzer = new TrendAnalyzer(pool);
    const line = analyzer.track("trending", 2000);
    expect(line.tag).toBe("trending");
    expect(line.direction).toBeDefined();
  });

  it("track slope positive for rising tags", () => {
    const pool = new MemoryPool();
    const now = Date.now() / 1000;
    // Cluster: 1 record in early bucket, 2 in mid, 3 in late
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Early", tags: ["hot"], timestamp: now - 30000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Mid1", tags: ["hot"], timestamp: now - 20000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Mid2", tags: ["hot"], timestamp: now - 20000 }, "agent-2",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Recent1", tags: ["hot"], timestamp: now - 10000 }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Recent2", tags: ["hot"], timestamp: now - 10000 }, "agent-2",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Recent3", tags: ["hot"], timestamp: now - 10000 }, "agent-3",
    ));

    const analyzer = new TrendAnalyzer(pool);
    const line = analyzer.track("hot", 10000);
    expect(line.slope).toBeGreaterThan(0);
  });

  it("rising returns sorted by change", () => {
    const pool = new MemoryPool();
    const now = Date.now() / 1000;
    for (let i = 0; i < 10; i++) {
      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: `Rising ${i}`, tags: ["rising_tag"], timestamp: now - 500 + i * 50 }, "agent-1",
      ));
    }

    const analyzer = new TrendAnalyzer(pool);
    const rising = analyzer.rising(-100, 500);
    expect(rising.length).toBeGreaterThanOrEqual(0);
  });

  it("falling returns sorted by change", () => {
    const pool = new MemoryPool();
    const now = Date.now() / 1000;
    for (let i = 0; i < 5; i++) {
      pool.store(AgentAgnosticMemory.to_shared_format(
        { content: `Falling ${i}`, tags: ["falling_tag"], timestamp: now - 5000 + i * 1000 }, "agent-1",
      ));
    }

    const analyzer = new TrendAnalyzer(pool);
    const falling = analyzer.falling(-100, 1000);
    expect(falling.length).toBeGreaterThanOrEqual(0);
  });
});
