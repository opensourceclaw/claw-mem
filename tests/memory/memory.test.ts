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
import { MemoryPool, AgentAgnosticMemory, CrossAgentSync } from "../../src/memory";

describe("MemoryPool", () => {
  it("should store and query records with filters", () => {
    const pool = new MemoryPool();

    const record1 = AgentAgnosticMemory.to_shared_format(
      { content: "Hello world", tags: ["greeting"], memory_type: "semantic" },
      "agent1",
    );
    const record2 = AgentAgnosticMemory.to_shared_format(
      { content: "Important fact", tags: ["important", "fact"] },
      "agent1",
    );
    const record3 = AgentAgnosticMemory.to_shared_format(
      { content: "Agent2 data", tags: ["internal"] },
      "agent2",
    );

    pool.store(record1);
    pool.store(record2);
    pool.store(record3);

    // Query all
    expect(pool.query({}).length).toBe(3);

    // Query by agent
    const agent1Records = pool.get_agent_memories("agent1");
    expect(agent1Records.length).toBe(2);

    // Query by tag
    const importantRecords = pool.query({ tags: ["important"] });
    expect(importantRecords.length).toBe(1);

    // Stats
    const stats = pool.stats();
    expect(stats.total_records).toBe(3);
    expect(stats.agent_count).toBe(2);
  });
});

describe("AgentAgnosticMemory", () => {
  it("should convert between local and shared formats and filter PII", () => {
    // PII stripping
    const record = AgentAgnosticMemory.to_shared_format(
      {
        content: "Contact me at test@example.com or call 555-123-4567",
        tags: [],
      },
      "agent1",
    );
    expect(record.content).toContain("[EMAIL]");
    expect(record.content).toContain("[PHONE]");
    expect(record.content).not.toContain("test@example.com");

    // Round-trip conversion
    const localBack = AgentAgnosticMemory.from_shared_format(record);
    expect(localBack.id).toBe(record.id);
    expect(localBack.content).toBe(record.content);
    expect(localBack.agent_id).toBe("agent1");
    expect(localBack.source).toBe("shared");
  });
});

describe("CrossAgentSync", () => {
  it("should push, pull, and subscribe to memory updates", () => {
    const pool = new MemoryPool();
    const sync = new CrossAgentSync(pool);

    const record = AgentAgnosticMemory.to_shared_format(
      { content: "Sync test data", tags: ["sync"] },
      "agent1",
    );

    // Subscribe
    let received: any = null;
    const subId = sync.subscribe("agent2", (r) => {
      received = r;
    });

    // Push
    const pushed = sync.push(record, ["agent2"]);
    expect(pushed).toBe(true);

    // Subscriber should have been notified
    expect(received).not.toBeNull();
    expect(received!.content).toBe("Sync test data");

    // Unsubscribe
    const unsubscribed = sync.unsubscribe(subId);
    expect(unsubscribed).toBe(true);

    // Pull
    const pulled = sync.pull("agent1", 0.0);
    expect(pulled.length).toBe(1);
    expect(pulled[0].content).toBe("Sync test data");

    // Stats
    const stats = sync.get_stats();
    expect(stats.push_count).toBe(1);
    expect(stats.pull_count).toBe(1);
  });
});
