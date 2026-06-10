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

export interface PoolFilters {
  agentId?: string;
  memoryType?: string;
  tags?: string[];
  since?: number;
  until?: number;
  minConfidence?: number;
}

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

  /**
   * Search records by substring matching on content + tags.
   *
   * @param query - Search query string
   * @param limit - Maximum results to return (default: 10)
   * @param filters - Optional PoolFilters
   * @returns Ranked list of matching MemoryRecords
   */
  search(query: string, limit: number = 10, filters?: PoolFilters): MemoryRecord[] {
    const q = query.toLowerCase();
    let candidates = this._records.filter((r) => {
      const inContent = r.content.toLowerCase().includes(q);
      const inTags = r.tags.some((t) => t.toLowerCase().includes(q));
      return inContent || inTags;
    });

    if (filters) {
      candidates = candidates.filter((r) => this._matchesFilters(r, filters));
    }

    return this.rankByRelevance(candidates, query).slice(0, limit);
  }

  /**
   * Rank records by relevance to a query string.
   * Scores by term match count in content, boosted by confidence.
   *
   * @param results - List of candidate MemoryRecords
   * @param query - The search query
   * @returns Records sorted by relevance (descending)
   */
  rankByRelevance(results: MemoryRecord[], query: string): MemoryRecord[] {
    const terms = query.toLowerCase().split(/\s+/);
    const scored = results.map((r) => {
      const contentLower = r.content.toLowerCase();
      let score = 0;
      for (const term of terms) {
        let idx = -1;
        while ((idx = contentLower.indexOf(term, idx + 1)) !== -1) {
          score++;
        }
      }
      for (const tag of r.tags) {
        for (const term of terms) {
          if (tag.toLowerCase().includes(term)) score++;
        }
      }
      score += r.confidence;
      return { record: r, score };
    });

    return scored.sort((a, b) => b.score - a.score).map((s) => s.record);
  }

  /**
   * Get all records from a specific agent, optionally since a timestamp.
   *
   * @param agentId - The agent ID to query
   * @param since - Optional timestamp filter
   * @returns List of MemoryRecords
   */
  getByAgent(agentId: string, since?: number): MemoryRecord[] {
    return this._records.filter((r) => {
      if (r.agent_id !== agentId) return false;
      if (since != null && r.timestamp < since) return false;
      return true;
    });
  }

  /**
   * Get records matching specific tags.
   *
   * @param tags - List of tag strings
   * @param matchAll - If true, require all tags; if false, any tag matches
   * @returns List of matching MemoryRecords
   */
  getByTags(tags: string[], matchAll: boolean = false): MemoryRecord[] {
    return this._records.filter((r) => {
      if (matchAll) {
        return tags.every((t) => r.tags.includes(t));
      }
      return tags.some((t) => r.tags.includes(t));
    });
  }

  // ── Private helpers ──────────────────────────────────────────────

  private _matchesFilters(
    record: MemoryRecord,
    filters: PoolFilters,
  ): boolean {
    if (filters.agentId != null && record.agent_id !== filters.agentId) return false;
    if (filters.memoryType != null && record.memory_type !== filters.memoryType) return false;
    if (filters.tags?.length) {
      if (!filters.tags.every((t) => record.tags.includes(t))) return false;
    }
    if (filters.since != null && record.timestamp < filters.since) return false;
    if (filters.until != null && record.timestamp > filters.until) return false;
    if (filters.minConfidence != null && record.confidence < filters.minConfidence) return false;
    return true;
  }

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
