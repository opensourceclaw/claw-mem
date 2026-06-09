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
 * MemoryPool - shared memory pool for cross-agent memory sharing.
 *
 * In-memory storage with optional file-backed persistence.
 * Supports store, query, filtering, PII auto-filtering.
 */

import * as fs from "fs";
import { AgentAgnosticMemory, MemoryRecord } from "./agnostic.js";

export class MemoryPool {
  private _records: MemoryRecord[] = [];
  storage_path?: string;

  /**
   * Initialize pool with optional file-backed storage.
   *
   * @param storagePath - Path to JSON file for persistence
   */
  constructor(storagePath?: string) {
    this.storage_path = storagePath;

    if (storagePath) {
      try {
        if (fs.existsSync(storagePath)) {
          this._load();
        }
      } catch {
        // File doesn't exist yet
      }
    }
  }

  /**
   * Store a record to the shared pool. Auto-filters PII.
   *
   * @param record - The MemoryRecord to store
   * @returns The record ID
   */
  store(record: MemoryRecord): string {
    if (record.source === "local") {
      record.content = AgentAgnosticMemory._strip_pii(record.content);
    }

    this._records.push(record);

    if (this.storage_path) {
      this._save();
    }

    return record.id;
  }

  /**
   * Query across all agents' memories with optional filters.
   *
   * @param filter - Dict with optional keys: agent_id, memory_type,
   *                 tags (any match), since, until, min_confidence
   * @returns List of matching MemoryRecords
   */
  query(filter: Record<string, unknown>): MemoryRecord[] {
    const results: MemoryRecord[] = [];
    for (const record of this._records) {
      if (this._matches(record, filter)) {
        results.push(record);
      }
    }
    return results;
  }

  /**
   * Get all memories from a specific agent.
   *
   * @param agentId - The agent ID to query
   * @returns List of MemoryRecords for the agent
   */
  get_agent_memories(agentId: string): MemoryRecord[] {
    return this.query({ agent_id: agentId });
  }

  /**
   * Get pool statistics.
   *
   * @returns Dict with total_records, agent_count, top_tags, oldest/newest
   */
  stats(): Record<string, unknown> {
    if (this._records.length === 0) {
      return {
        total_records: 0,
        agent_count: 0,
        top_tags: [],
        oldest: null,
        newest: null,
      };
    }

    const agents = new Set(this._records.map((r) => r.agent_id));
    const tagCounts: Record<string, number> = {};
    for (const r of this._records) {
      for (const tag of r.tags) {
        tagCounts[tag] = (tagCounts[tag] ?? 0) + 1;
      }
    }
    const topTags = Object.entries(tagCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([tag]) => tag);

    const timestamps = this._records.map((r) => r.timestamp);

    return {
      total_records: this._records.length,
      agent_count: agents.size,
      top_tags: topTags,
      oldest: Math.min(...timestamps),
      newest: Math.max(...timestamps),
    };
  }

  /**
   * Remove records older than maxAgeDays.
   *
   * @param maxAgeDays - Remove records older than this many days
   * @returns Number of records removed
   */
  cleanup(maxAgeDays: number = 30): number {
    const cutoff = Date.now() / 1000 - maxAgeDays * 86400;
    const before = this._records.length;
    this._records = this._records.filter((r) => r.timestamp > cutoff);
    const removed = before - this._records.length;

    if (removed > 0 && this.storage_path) {
      this._save();
    }
    return removed;
  }

  /** Clear all records (for testing). */
  clear(): void {
    this._records = [];
    if (this.storage_path) {
      try {
        fs.unlinkSync(this.storage_path);
      } catch {
        // File may not exist
      }
    }
  }

  // ── Private helpers ──────────────────────────────────────────────

  private _matches(
    record: MemoryRecord,
    filt: Record<string, unknown>,
  ): boolean {
    if (filt.agent_id != null && record.agent_id !== filt.agent_id) return false;
    if (filt.memory_type != null && record.memory_type !== filt.memory_type) return false;
    if (filt.tags != null) {
      const reqTags = new Set(filt.tags as string[]);
      const recordTags = new Set(record.tags);
      for (const tag of reqTags) {
        if (!recordTags.has(tag)) return false;
      }
    }
    if (filt.since != null && record.timestamp < (filt.since as number)) return false;
    if (filt.until != null && record.timestamp > (filt.until as number)) return false;
    if (filt.min_confidence != null && record.confidence < (filt.min_confidence as number)) {
      return false;
    }
    return true;
  }

  private _save(): void {
    if (!this.storage_path) return;
    const data = this._records.map((r) => ({
      id: r.id,
      agent_id: r.agent_id,
      memory_type: r.memory_type,
      content: r.content,
      tags: r.tags,
      timestamp: r.timestamp,
      confidence: r.confidence,
      source: r.source,
    }));
    fs.writeFileSync(this.storage_path, JSON.stringify(data));
  }

  private _load(): void {
    if (!this.storage_path) return;
    try {
      const data = JSON.parse(fs.readFileSync(this.storage_path, "utf-8"));
      this._records = data.map((d: any) => ({
        id: d.id,
        agent_id: d.agent_id,
        memory_type: d.memory_type,
        content: d.content,
        tags: d.tags,
        timestamp: d.timestamp,
        confidence: d.confidence ?? 1.0,
        source: d.source ?? "shared",
      }));
    } catch {
      this._records = [];
    }
  }
}
