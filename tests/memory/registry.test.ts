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
import { FederationRegistry } from "../../src/memory";
import type { FederationMember } from "../../src/memory";

function makeMember(overrides?: Partial<FederationMember>): FederationMember {
  return {
    agentId: "agent-1",
    endpoint: "http://localhost:8080",
    capabilities: ["memory", "search"],
    status: "active",
    lastHeartbeat: Date.now() / 1000,
    metadata: {},
    ...overrides,
  };
}

describe("FederationRegistry", () => {
  it("should register and unregister members", () => {
    const reg = new FederationRegistry();
    const member = makeMember();
    reg.register(member);

    expect(reg.getMember("agent-1")).toBeDefined();
    expect(reg.getMember("agent-1")!.endpoint).toBe("http://localhost:8080");

    expect(reg.unregister("agent-1")).toBe(true);
    expect(reg.getMember("agent-1")).toBeUndefined();
    expect(reg.unregister("nonexistent")).toBe(false);
  });

  it("should discover members by capabilities", () => {
    const reg = new FederationRegistry();
    reg.register(makeMember({ agentId: "a1", capabilities: ["memory"] }));
    reg.register(makeMember({ agentId: "a2", capabilities: ["search"] }));
    reg.register(makeMember({ agentId: "a3", capabilities: ["memory", "search"] }));

    const memoryAgents = reg.discover({ capabilities: ["memory"] });
    expect(memoryAgents.length).toBe(2);
    expect(memoryAgents.map((m) => m.agentId).sort()).toEqual(["a1", "a3"]);
  });

  it("should discover members by status", () => {
    const reg = new FederationRegistry();
    reg.register(makeMember({ agentId: "a1", status: "active" }));
    reg.register(makeMember({ agentId: "a2", status: "inactive" }));

    expect(reg.discover({ status: "active" }).length).toBe(1);
    expect(reg.discover({ status: "inactive" }).length).toBe(1);
  });

  it("should update lastHeartbeat on heartbeat", () => {
    const reg = new FederationRegistry();
    const member = makeMember({ status: "inactive", lastHeartbeat: 0 });
    reg.register(member);

    reg.heartbeat("agent-1");
    const m = reg.getMember("agent-1")!;
    expect(m.lastHeartbeat).toBeGreaterThan(0);
    expect(m.status).toBe("active");
  });

  it("should return correct stats", () => {
    const reg = new FederationRegistry();
    reg.register(makeMember({ agentId: "a1", status: "active" }));
    reg.register(makeMember({ agentId: "a2", status: "active" }));
    reg.register(makeMember({ agentId: "a3", status: "inactive" }));

    const stats = reg.getStats();
    expect(stats.total).toBe(3);
    expect(stats.active).toBe(2);
    expect(stats.inactive).toBe(1);
  });
});
