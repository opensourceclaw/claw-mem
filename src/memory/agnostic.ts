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
 * AgentAgnosticMemory - cross-agent memory format
 *
 * Provides standardized memory records, format conversion between
 * local and shared representations, PII filtering, and query filters.
 */

import { randomUUID } from "crypto";

// ── PII patterns ──────────────────────────────────────────────────────

const PII_PATTERNS: [RegExp, string][] = [
  [/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, "[EMAIL]"],
  [/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, "[PHONE]"],
  [/\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/g, "[SSN]"],
  [
    /(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\w-]+/gi,
    "[API_KEY]",
  ],
  [/sk-[a-zA-Z0-9]{20,}/g, "[API_KEY]"],
];

// ── MemoryRecord ──────────────────────────────────────────────────────

export interface MemoryRecord {
  id: string;
  agent_id: string;
  memory_type: string;
  content: string;
  tags: string[];
  timestamp: number;
  confidence: number;
  source: string;
}

// ── AgentAgnosticMemory ───────────────────────────────────────────────

export class AgentAgnosticMemory {
  /**
   * Convert a local memory dict to shared MemoryRecord format.
   *
   * @param memory - Dictionary with memory data (content, tags, etc.)
   * @param agentId - ID of the agent that created the memory
   * @returns Standardized MemoryRecord
   */
  static to_shared_format(
    memory: Record<string, unknown>,
    agentId: string,
  ): MemoryRecord {
    const content = String(memory.content ?? "");
    if (!content.trim()) {
      throw new Error("Content is required for MemoryRecord");
    }

    const cleanContent = AgentAgnosticMemory._strip_pii(content);

    return {
      id: (memory.id as string) ?? randomUUID(),
      agent_id: agentId,
      memory_type: (memory.memory_type as string) ?? "shared",
      content: cleanContent,
      tags: [...((memory.tags as string[]) ?? [])],
      timestamp: (memory.timestamp as number) ?? Date.now() / 1000,
      confidence: (memory.confidence as number) ?? 1.0,
      source: "shared",
    };
  }

  /**
   * Convert a shared MemoryRecord back to local format.
   *
   * @param record - The shared MemoryRecord
   * @returns Dictionary in local memory format
   */
  static from_shared_format(record: MemoryRecord): Record<string, unknown> {
    return {
      id: record.id,
      content: record.content,
      memory_type: record.memory_type,
      tags: record.tags,
      timestamp: record.timestamp,
      confidence: record.confidence,
      agent_id: record.agent_id,
      source: record.source,
    };
  }

  /**
   * Create a filter dict for querying MemoryPool.
   *
   * @param agentId - Filter by agent ID
   * @param memoryType - Filter by memory type
   * @param tags - Filter by tags (superset match)
   * @param since - Filter records after timestamp
   * @param until - Filter records before timestamp
   * @param minConfidence - Minimum confidence threshold
   * @returns Filter dictionary for MemoryPool.query()
   */
  static create_filter(
    agentId?: string,
    memoryType?: string,
    tags?: string[],
    since?: number,
    until?: number,
    minConfidence: number = 0.0,
  ): Record<string, unknown> {
    const filt: Record<string, unknown> = {};
    if (agentId != null) filt.agent_id = agentId;
    if (memoryType != null) filt.memory_type = memoryType;
    if (tags != null) filt.tags = tags;
    if (since != null) filt.since = since;
    if (until != null) filt.until = until;
    if (minConfidence > 0.0) filt.min_confidence = minConfidence;
    return filt;
  }

  /**
   * Strip known PII patterns from content.
   *
   * @param content - Original content string
   * @returns Content with PII patterns replaced by placeholders
   */
  static _strip_pii(content: string): string {
    for (const [pattern, replacement] of PII_PATTERNS) {
      content = content.replace(pattern, replacement);
    }
    return content;
  }
}
