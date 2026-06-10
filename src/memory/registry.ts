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

/**
 * FederationRegistry - member management for cross-agent memory federation.
 */

export interface FederationMember {
  agentId: string;
  endpoint: string;
  capabilities: string[];
  status: "active" | "inactive" | "suspended";
  lastHeartbeat: number;
  metadata: Record<string, unknown>;
}

export class FederationRegistry {
  private _members: Map<string, FederationMember> = new Map();

  register(member: FederationMember): void {
    this._members.set(member.agentId, { ...member });
  }

  unregister(agentId: string): boolean {
    return this._members.delete(agentId);
  }

  discover(query?: { capabilities?: string[]; status?: string }): FederationMember[] {
    let results = Array.from(this._members.values());

    if (query?.capabilities?.length) {
      results = results.filter((m) =>
        query.capabilities!.some((c) => m.capabilities.includes(c)),
      );
    }
    if (query?.status) {
      results = results.filter((m) => m.status === query.status);
    }

    return results;
  }

  heartbeat(agentId: string): void {
    const member = this._members.get(agentId);
    if (member) {
      member.lastHeartbeat = Date.now() / 1000;
      if (member.status === "inactive") {
        member.status = "active";
      }
    }
  }

  getMember(agentId: string): FederationMember | undefined {
    return this._members.get(agentId);
  }

  getStats(): { total: number; active: number; inactive: number } {
    let active = 0;
    let inactive = 0;
    for (const m of this._members.values()) {
      if (m.status === "active") active++;
      else inactive++;
    }
    return { total: this._members.size, active, inactive };
  }
}
