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
import { MemoryFederation, AgentAgnosticMemory } from "../../src/memory";

describe("MemoryFederation integration", () => {
  it("should run full flow: register → store → search → sync → resolve conflict", () => {
    const fed = new MemoryFederation({ workspaces: ["/tmp/test-ws"] });

    // Register agents
    fed.registry.register({
      agentId: "agent-1",
      endpoint: "http://localhost:8001",
      capabilities: ["memory"],
      status: "active",
      lastHeartbeat: Date.now() / 1000,
      metadata: {},
    });
    fed.registry.register({
      agentId: "agent-2",
      endpoint: "http://localhost:8002",
      capabilities: ["memory", "search"],
      status: "active",
      lastHeartbeat: Date.now() / 1000,
      metadata: {},
    });

    expect(fed.registry.getStats().active).toBe(2);

    // Share records
    const r1 = AgentAgnosticMemory.to_shared_format(
      { content: "Auth module uses OAuth2 with JWT", tags: ["auth", "security"] },
      "agent-1",
    );
    fed.share(r1, "shared");

    const r2 = AgentAgnosticMemory.to_shared_format(
      { content: "Deploy to Kubernetes on Fridays", tags: ["deploy", "schedule"] },
      "agent-2",
    );
    fed.share(r2, "shared");

    // Search
    const results = fed.search("OAuth2");
    expect(results.length).toBeGreaterThanOrEqual(1);
    expect(results[0].content).toContain("OAuth2");

    // Sync
    fed.sync.push(r1, ["agent-2"]);
    const batches = fed.syncAll();
    expect(batches.length).toBe(2);

    // Conflict detection
    const r1Conflicting = AgentAgnosticMemory.to_shared_format(
      { content: "Auth module uses basic auth only", tags: ["auth", "security"] },
      "agent-2",
    );
    fed.sync.push(r1Conflicting, ["agent-1"]);

    const conflict = fed.conflictResolver.detect(r1, r1Conflicting);
    expect(conflict).not.toBeNull();
    expect(conflict!.commonTags).toContain("auth");

    // Resolve with merge
    const resolved = fed.conflictResolver.resolve(conflict!, "merge");
    expect(resolved.content).toContain("OAuth2");
    expect(resolved.content).toContain("basic auth");

    // Privacy filter
    const sensitive = AgentAgnosticMemory.to_shared_format(
      { content: "Email admin@example.com with password secret123" },
      "agent-1",
    );
    const filtered = fed.privacyFilter.filter(sensitive, "shared");
    expect(filtered.content).not.toContain("admin@example.com");

    // Stats
    const stats = fed.getStats();
    expect(stats.workspaceCount).toBe(1);
    expect((stats.pool as any).total_records).toBeGreaterThanOrEqual(2);
  });
});
