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

describe("MemoryPool enhanced", () => {
  function seed(pool: MemoryPool) {
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Authentication uses OAuth2 with JWT", tags: ["auth", "security"], memory_type: "semantic", timestamp: 1000 },
      "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Database uses PostgreSQL with pooling", tags: ["db", "postgres"], memory_type: "semantic", timestamp: 2000 },
      "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "Deployment pipeline runs on CI/CD", tags: ["deploy", "ci"], memory_type: "procedural", timestamp: 3000 },
      "agent-2",
    ));
  }

  it("should search and return matching records", () => {
    const pool = new MemoryPool();
    seed(pool);

    const results = pool.search("OAuth2");
    expect(results.length).toBe(1);
    expect(results[0].content).toContain("OAuth2");
  });

  it("should respect limit", () => {
    const pool = new MemoryPool();
    seed(pool);

    const results = pool.search("auth", 1);
    expect(results.length).toBe(1);
  });

  it("should search with filters", () => {
    const pool = new MemoryPool();
    seed(pool);

    const results = pool.search("deploy", 10, { agentId: "agent-2" });
    expect(results.length).toBe(1);
    expect(results[0].agent_id).toBe("agent-2");
  });

  it("should rank by relevance", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "auth auth auth config", tags: ["auth"] }, "agent-1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "some auth mention", tags: [] }, "agent-2",
    ));

    const results = pool.search("auth");
    expect(results[0].content).toContain("auth auth auth");
  });

  it("should getByAgent with optional since", () => {
    const pool = new MemoryPool();
    seed(pool);

    const all = pool.getByAgent("agent-1");
    expect(all.length).toBe(2);

    const since = pool.getByAgent("agent-1", 1500);
    expect(since.length).toBe(1);
    expect(since[0].content).toContain("PostgreSQL");
  });

  it("should getByTags with matchAll", () => {
    const pool = new MemoryPool();
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "A", tags: ["alpha", "beta"] }, "a1",
    ));
    pool.store(AgentAgnosticMemory.to_shared_format(
      { content: "B", tags: ["alpha"] }, "a1",
    ));

    const anyMatch = pool.getByTags(["alpha", "beta"], false);
    expect(anyMatch.length).toBe(2);

    const allMatch = pool.getByTags(["alpha", "beta"], true);
    expect(allMatch.length).toBe(1);
  });
});
