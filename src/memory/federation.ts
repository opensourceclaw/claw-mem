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
 * MemoryFederation - cross-agent memory sharing with full component integration.
 */

import type { MemoryRecord } from "./agnostic.js";
import { FederationRegistry } from "./registry.js";
import type { FederationMember } from "./registry.js";
import { MemoryPool } from "./pool.js";
import type { PoolFilters } from "./pool.js";
import { CrossAgentSync } from "./sync.js";
import type { SyncBatch } from "./sync.js";
import { ConflictResolver } from "./conflict.js";
import type { Conflict, ConflictStrategy } from "./conflict.js";
import { PrivacyFilter } from "./privacy.js";
import type { PrivacyLevel } from "./privacy.js";

export interface FederationConfig {
  workspaces: string[];
  sharedTags?: string[];
  maxResults?: number;
}

export class MemoryFederation {
  private _registry: FederationRegistry;
  private _pool: MemoryPool;
  private _sync: CrossAgentSync;
  private _conflictResolver: ConflictResolver;
  private _privacyFilter: PrivacyFilter;
  private _config: FederationConfig;

  constructor(config: FederationConfig) {
    this._config = config;
    this._registry = new FederationRegistry();
    this._pool = new MemoryPool();
    this._sync = new CrossAgentSync(this._pool);
    this._conflictResolver = new ConflictResolver();
    this._privacyFilter = new PrivacyFilter();
  }

  get registry(): FederationRegistry { return this._registry; }
  get pool(): MemoryPool { return this._pool; }
  get sync(): CrossAgentSync { return this._sync; }
  get conflictResolver(): ConflictResolver { return this._conflictResolver; }
  get privacyFilter(): PrivacyFilter { return this._privacyFilter; }

  /**
   * Search across the federated pool.
   *
   * @param query - Search query string
   * @param limit - Max results (default: 10)
   * @returns List of matching MemoryRecords
   */
  search(query: string, limit: number = 10): MemoryRecord[] {
    return this._pool.search(query, limit);
  }

  /**
   * Share a record to the federation with privacy filtering.
   *
   * @param record - The MemoryRecord to share
   * @param level - Privacy level for filtering (default: "shared")
   * @returns The stored record ID
   */
  share(record: MemoryRecord, level: PrivacyLevel = "shared"): string {
    const filtered = this._privacyFilter.filter(record, level);
    return this._pool.store(filtered);
  }

  /**
   * Sync across all registered agents.
   *
   * @returns List of SyncBatches for each agent
   */
  syncAll(): SyncBatch[] {
    const members = this._registry.discover();
    return members.map((m) => this._sync.pull(m.agentId));
  }

  getStats(): Record<string, unknown> {
    return {
      workspaceCount: this._config.workspaces.length,
      sharedTags: this._config.sharedTags,
      registry: this._registry.getStats(),
      pool: this._pool.stats(),
      sync: this._sync.get_stats(),
    };
  }
}
