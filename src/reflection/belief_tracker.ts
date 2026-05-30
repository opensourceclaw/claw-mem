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
 * Belief Tracker
 *
 * Tracks belief versions over time, recording when beliefs are
 * created, updated, or contradicted. Provides version history
 * for audit and debugging.
 */

// ── Data classes ──────────────────────────────────────────────────────

export interface BeliefVersion {
  belief_id: string;
  statement: string;
  confidence: number;
  version: number;
  created_at: string;
  previous_statement: string;
}

export interface BeliefHistory {
  belief_id: string;
  versions: BeliefVersion[];

  /** Current (latest) version. */
  readonly current: BeliefVersion | null;
  /** Number of versions. */
  readonly version_count: number;

  /** Whether this belief has been updated more than once. */
  was_updated(): boolean;
}

// ── BeliefTracker ─────────────────────────────────────────────────────

export class BeliefTracker {
  private _store: Map<string, BeliefVersion[]> = new Map();

  /**
   * Record a new belief (v1).
   *
   * @param beliefId - Unique belief identifier
   * @param statement - Belief statement
   * @param confidence - Confidence score (0.0-1.0)
   */
  record(beliefId: string, statement: string, confidence: number): void {
    const version: BeliefVersion = {
      belief_id: beliefId,
      statement,
      confidence,
      version: 1,
      created_at: new Date().toISOString(),
      previous_statement: "",
    };
    if (!this._store.has(beliefId)) {
      this._store.set(beliefId, []);
    }
    this._store.get(beliefId)!.push(version);
  }

  /**
   * Update an existing belief to a new version.
   *
   * @param beliefId - Existing belief identifier
   * @param statement - Updated statement
   * @param confidence - Updated confidence
   */
  update(beliefId: string, statement: string, confidence: number): void {
    if (!this._store.has(beliefId)) {
      this.record(beliefId, statement, confidence);
      return;
    }

    const versions = this._store.get(beliefId)!;
    const previous = versions[versions.length - 1];

    const newVersion: BeliefVersion = {
      belief_id: beliefId,
      statement,
      confidence,
      version: previous.version + 1,
      created_at: new Date().toISOString(),
      previous_statement: previous.statement,
    };
    versions.push(newVersion);
  }

  /**
   * Get the current (latest) version of a belief.
   *
   * @param beliefId - The belief ID
   * @returns The latest version or null if not found
   */
  get_current(beliefId: string): BeliefVersion | null {
    const versions = this._store.get(beliefId);
    if (!versions || versions.length === 0) return null;
    return versions[versions.length - 1];
  }

  /**
   * Get all versions of a belief.
   *
   * @param beliefId - The belief ID
   * @returns Array of all versions
   */
  get_history(beliefId: string): BeliefVersion[] {
    return this._store.get(beliefId) ?? [];
  }

  /**
   * Get all belief IDs.
   *
   * @returns Array of belief IDs
   */
  get_all_ids(): string[] {
    return Array.from(this._store.keys());
  }

  /**
   * Get current version of all beliefs.
   *
   * @returns Array of current BeliefVersion objects
   */
  get_all_current(): BeliefVersion[] {
    const result: BeliefVersion[] = [];
    for (const versions of this._store.values()) {
      if (versions.length > 0) {
        result.push(versions[versions.length - 1]);
      }
    }
    return result;
  }

  /**
   * Get beliefs changed after a timestamp.
   *
   * @param cutoff - ISO timestamp string
   * @returns Array of matching BeliefVersion objects
   */
  get_changes_since(cutoff: string): BeliefVersion[] {
    const changed: BeliefVersion[] = [];
    for (const versions of this._store.values()) {
      for (const v of versions) {
        if (v.created_at > cutoff) {
          changed.push(v);
        }
      }
    }
    return changed;
  }

  /** Count unique beliefs. */
  count_beliefs(): number {
    return this._store.size;
  }

  /** Count total belief versions. */
  count_versions(): number {
    let total = 0;
    for (const versions of this._store.values()) {
      total += versions.length;
    }
    return total;
  }
}
