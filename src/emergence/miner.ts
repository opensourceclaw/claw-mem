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
 * PatternMiner — mine patterns, correlations, and cross-agent signals
 * from the federated memory pool.
 */

import type { MemoryPool } from "../memory/pool.js";
import type { MemoryRecord } from "../memory/agnostic.js";
import type {
  TagFrequency,
  TagCorrelation,
  CrossAgentPattern,
} from "./types.js";

export class PatternMiner {
  private _pool: MemoryPool;

  constructor(pool: MemoryPool) {
    this._pool = pool;
  }

  frequencyAnalysis(records?: MemoryRecord[]): TagFrequency[] {
    const recs = records ?? this._pool.query({});
    const tagMap = new Map<string, { count: number; agents: Set<string>; first: number; last: number }>();

    for (const r of recs) {
      for (const tag of r.tags) {
        let entry = tagMap.get(tag);
        if (!entry) {
          entry = { count: 0, agents: new Set(), first: r.timestamp, last: r.timestamp };
          tagMap.set(tag, entry);
        }
        entry.count++;
        entry.agents.add(r.agent_id);
        if (r.timestamp < entry.first) entry.first = r.timestamp;
        if (r.timestamp > entry.last) entry.last = r.timestamp;
      }
    }

    const results: TagFrequency[] = [];
    for (const [tag, e] of tagMap) {
      results.push({
        tag,
        count: e.count,
        agentCount: e.agents.size,
        firstSeen: e.first,
        lastSeen: e.last,
      });
    }
    return results.sort((a, b) => b.count - a.count);
  }

  correlationAnalysis(records?: MemoryRecord[]): TagCorrelation[] {
    const recs = records ?? this._pool.query({});

    // Count individual tag frequencies and pairwise co-occurrences
    const tagCounts = new Map<string, number>();
    const pairCounts = new Map<string, { co: number; agentsA: Set<string>; agentsB: Set<string>; overlap: Set<string> }>();
    const tagAgents = new Map<string, Set<string>>();

    for (const r of recs) {
      const tags = [...new Set(r.tags)];
      for (const tag of tags) {
        tagCounts.set(tag, (tagCounts.get(tag) ?? 0) + 1);
        if (!tagAgents.has(tag)) tagAgents.set(tag, new Set());
        tagAgents.get(tag)!.add(r.agent_id);
      }
      for (let i = 0; i < tags.length; i++) {
        for (let j = i + 1; j < tags.length; j++) {
          const key = [tags[i], tags[j]].sort().join("||");
          let pair = pairCounts.get(key);
          if (!pair) {
            pair = { co: 0, agentsA: new Set(), agentsB: new Set(), overlap: new Set() };
            pairCounts.set(key, pair);
          }
          pair.co++;
          pair.agentsA.add(r.agent_id);
          pair.agentsB.add(r.agent_id);
        }
      }
    }

    const total = recs.length;
    const results: TagCorrelation[] = [];

    for (const [key, pair] of pairCounts) {
      if (pair.co < 2) continue;
      const [a, b] = key.split("||");
      const pA = (tagCounts.get(a) ?? 1) / total;
      const pB = (tagCounts.get(b) ?? 1) / total;
      const pAB = pair.co / total;
      const lift = pAB / (pA * pB);

      const agentsA = tagAgents.get(a) ?? new Set();
      const agentsB = tagAgents.get(b) ?? new Set();
      let overlap = 0;
      for (const ag of agentsA) {
        if (agentsB.has(ag)) overlap++;
      }

      results.push({
        tagA: a,
        tagB: b,
        cooccurrence: pair.co,
        lift: Math.round(lift * 1000) / 1000,
        agentOverlap: overlap,
      });
    }

    return results.sort((a, b) => b.lift - a.lift);
  }

  crossAgentPatterns(records?: MemoryRecord[]): CrossAgentPattern[] {
    const recs = records ?? this._pool.query({});

    // Group records by shared tag combos across agents
    const tagKeyToRecords = new Map<string, MemoryRecord[]>();

    for (const r of recs) {
      if (r.tags.length === 0) continue;
      const key = [...r.tags].sort().join(",");
      let group = tagKeyToRecords.get(key);
      if (!group) {
        group = [];
        tagKeyToRecords.set(key, group);
      }
      group.push(r);
    }

    const patterns: CrossAgentPattern[] = [];
    for (const [key, group] of tagKeyToRecords) {
      const agents = new Set(group.map((r) => r.agent_id));
      if (agents.size < 2) continue;

      const timestamps = group.map((r) => r.timestamp);
      const avgConf = group.reduce((s, r) => s + r.confidence, 0) / group.length;
      const commonTags = key.split(",");

      patterns.push({
        topic: `Cross-agent: ${commonTags.join(", ")}`,
        agents: [...agents],
        memoryCount: group.length,
        avgConfidence: Math.round(avgConf * 1000) / 1000,
        commonTags,
        firstSeen: Math.min(...timestamps),
        lastSeen: Math.max(...timestamps),
      });
    }

    return patterns.sort((a, b) => b.agents.length - a.agents.length);
  }
}
