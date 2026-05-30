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
 * CrossAgentSync - push/pull memory synchronization
 *
 * Supports push/pull patterns, subscription-based event-driven sync,
 * and basic conflict detection for cross-agent memory sharing.
 */

import { randomUUID } from "crypto";
import { MemoryRecord } from "./agnostic";
import { MemoryPool } from "./pool";

export class CrossAgentSync {
  pool?: MemoryPool;
  private _subscriptions: Map<string, Array<{ subId: string; callback: (record: MemoryRecord) => void }>> = new Map();
  private _pushCount = 0;
  private _pullCount = 0;

  /**
   * Initialize sync with optional MemoryPool.
   *
   * @param pool - A MemoryPool instance for storage
   */
  constructor(pool?: MemoryPool) {
    this.pool = pool;
  }

  /**
   * Push memory to specific agents.
   *
   * @param record - The MemoryRecord to push
   * @param targetAgents - List of target agent IDs
   * @param bus - Optional message bus for agent communication
   * @returns True if push was successful
   */
  push(
    record: MemoryRecord,
    targetAgents: string[],
    bus?: any,
  ): boolean {
    if (this.pool) {
      this.pool.store(record);
    }

    for (const agentId of targetAgents) {
      this._notifySubscribers(agentId, record);
    }

    this._pushCount++;
    return true;
  }

  /**
   * Pull updates from an agent since a timestamp.
   *
   * @param agentId - The agent to pull from
   * @param since - Unix timestamp to pull updates after
   * @returns List of MemoryRecords newer than since
   */
  pull(agentId: string, since: number = 0.0): MemoryRecord[] {
    this._pullCount++;

    if (!this.pool) return [];

    const records = this.pool.query({ agent_id: agentId });
    return records.filter((r) => r.timestamp >= since);
  }

  /**
   * Subscribe to an agent's new memories.
   *
   * @param agentId - The agent ID to subscribe to
   * @param callback - Called with each new MemoryRecord
   * @returns Subscription ID for later unsubscribe
   */
  subscribe(
    agentId: string,
    callback: (record: MemoryRecord) => void,
  ): string {
    const subId = randomUUID();

    if (!this._subscriptions.has(agentId)) {
      this._subscriptions.set(agentId, []);
    }
    this._subscriptions.get(agentId)!.push({ subId, callback });

    return subId;
  }

  /**
   * Remove a subscription.
   *
   * @param subscriptionId - The subscription ID from subscribe()
   * @returns True if found and removed
   */
  unsubscribe(subscriptionId: string): boolean {
    for (const [agentId, subs] of this._subscriptions.entries()) {
      const idx = subs.findIndex((s) => s.subId === subscriptionId);
      if (idx !== -1) {
        subs.splice(idx, 1);
        if (subs.length === 0) {
          this._subscriptions.delete(agentId);
        }
        return true;
      }
    }
    return false;
  }

  /**
   * Detect conflicts between two records.
   *
   * A conflict is detected when two records share at least one tag
   * but have different content.
   *
   * @param record - New MemoryRecord
   * @param existing - Existing MemoryRecord
   * @returns Conflict description if detected, null otherwise
   */
  detect_conflict(record: MemoryRecord, existing: MemoryRecord): string | null {
    const commonTags = record.tags.filter((t) => existing.tags.includes(t));
    if (commonTags.length > 0 && record.content !== existing.content) {
      return (
        `Conflict: records from ${record.agent_id} and ` +
        `${existing.agent_id} share tags ${JSON.stringify(commonTags)} ` +
        "but have different content"
      );
    }
    return null;
  }

  /**
   * Get sync statistics.
   *
   * @returns Dict with push_count, pull_count, active_subscriptions
   */
  get_stats(): Record<string, unknown> {
    let active = 0;
    for (const subs of this._subscriptions.values()) {
      if (subs.length > 0) active++;
    }
    return {
      push_count: this._pushCount,
      pull_count: this._pullCount,
      active_subscriptions: active,
      subscribed_agents: this._subscriptions.size,
    };
  }

  // ── Private ──────────────────────────────────────────────────────

  private _notifySubscribers(
    agentId: string,
    record: MemoryRecord,
  ): void {
    const subs = this._subscriptions.get(agentId) ?? [];
    for (const { callback } of subs) {
      try {
        callback(record);
      } catch {
        // Silently handle subscriber errors
      }
    }
  }
}
