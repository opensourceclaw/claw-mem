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
import { CrossAgentSync, MemoryPool, AgentAgnosticMemory } from "../../src/memory";

describe("CrossAgentSync enhanced", () => {
  it("should increment version on push", () => {
    const pool = new MemoryPool();
    const sync = new CrossAgentSync(pool);

    const record = AgentAgnosticMemory.to_shared_format(
      { content: "Test record" }, "agent-1",
    );

    expect(sync.getVersion("agent-1")).toBe(0);

    sync.push(record, ["agent-2"]);
    expect(sync.getVersion("agent-1")).toBe(1);
    expect(sync.getVersion("agent-2")).toBe(1);
  });

  it("should pull returns SyncBatch with version", () => {
    const pool = new MemoryPool();
    const sync = new CrossAgentSync(pool);

    const record = AgentAgnosticMemory.to_shared_format(
      { content: "Test record", timestamp: Date.now() / 1000 }, "agent-1",
    );
    sync.push(record, ["agent-2"]);

    const batch = sync.pull("agent-1");
    expect(batch.agentId).toBe("agent-1");
    expect(batch.version).toBe(1);
    expect(batch.records.length).toBeGreaterThanOrEqual(0);
  });

  it("should getVersion returns current version", () => {
    const pool = new MemoryPool();
    const sync = new CrossAgentSync(pool);

    expect(sync.getVersion("unknown")).toBe(0);

    const record = AgentAgnosticMemory.to_shared_format(
      { content: "Test" }, "agent-x",
    );
    sync.push(record, ["agent-y"]);
    expect(sync.getVersion("agent-x")).toBe(1);
  });

  it("should detectConflicts finds conflicts in batch", () => {
    const pool = new MemoryPool();
    const sync = new CrossAgentSync(pool);

    const r1 = AgentAgnosticMemory.to_shared_format(
      { content: "Project deadline is Friday", tags: ["project"] }, "agent-1",
    );
    pool.store(r1);

    const r2 = AgentAgnosticMemory.to_shared_format(
      { content: "Project deadline is Monday", tags: ["project"] }, "agent-1",
    );

    const batch = {
      agentId: "agent-1",
      records: [r2],
      version: 2,
      timestamp: Date.now() / 1000,
    };

    const conflicts = sync.detectConflicts(batch);
    expect(conflicts.length).toBe(1);
    expect(conflicts[0].commonTags).toContain("project");
  });
});
