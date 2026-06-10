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
 * EmergenceDetector — score, gate, and detect emergent patterns.
 */

import { randomUUID } from "crypto";
import type { MemoryRecord } from "../memory/agnostic.js";
import { PatternMiner } from "./miner.js";
import type {
  EmergenceScore,
  EmergentPattern,
  GateResult,
  CrossAgentPattern,
  TagCorrelation,
  TagFrequency,
} from "./types.js";

export class EmergenceDetector {
  private _miner: PatternMiner;
  private _totalAgents: number;

  constructor(miner: PatternMiner, totalAgents?: number) {
    this._miner = miner;
    this._totalAgents = totalAgents ?? 1;
  }

  score(pattern: CrossAgentPattern | TagCorrelation): EmergenceScore {
    let agentCount: number;
    let avgConfidence: number;

    if ("agents" in pattern) {
      agentCount = pattern.agents.length;
      avgConfidence = pattern.avgConfidence;
    } else {
      agentCount = pattern.agentOverlap;
      avgConfidence = 1.0;
    }

    const totalAgents = Math.max(this._totalAgents, agentCount);
    const consensus = agentCount / totalAgents;
    const utility = consensus * avgConfidence;
    const novelty = 0.5;
    const confidence = 0.3 * novelty + 0.3 * utility + 0.4 * consensus;

    return {
      novelty: Math.round(novelty * 1000) / 1000,
      utility: Math.round(utility * 1000) / 1000,
      consensus: Math.round(consensus * 1000) / 1000,
      confidence: Math.round(confidence * 1000) / 1000,
    };
  }

  gate(score: EmergenceScore, threshold: number = 0.4): GateResult {
    const conf = score.confidence;
    if (conf >= 0.7) return "emergent";
    if (conf >= threshold) return "borderline";
    return "noise";
  }

  detect(records: MemoryRecord[]): EmergentPattern[] {
    const patterns: EmergentPattern[] = [];

    // Cross-agent patterns
    const cross = this._miner.crossAgentPatterns(records);
    for (const p of cross) {
      const s = this.score(p);
      const g = this.gate(s);
      if (g === "noise") continue;
      patterns.push({
        id: randomUUID(),
        type: "cross_agent",
        description: p.topic,
        score: s,
        relatedRecords: [],
        detectedAt: Date.now() / 1000,
        tags: p.commonTags,
      });
    }

    // Tag correlations
    const corrs = this._miner.correlationAnalysis(records);
    for (const c of corrs) {
      const s = this.score(c);
      const g = this.gate(s);
      if (g === "noise") continue;
      patterns.push({
        id: randomUUID(),
        type: "correlation",
        description: `${c.tagA} ↔ ${c.tagB} (lift=${c.lift})`,
        score: s,
        relatedRecords: [],
        detectedAt: Date.now() / 1000,
        tags: [c.tagA, c.tagB],
      });
    }

    // Frequency patterns — high-frequency tags across agents
    const freqs = this._miner.frequencyAnalysis(records);
    for (const f of freqs) {
      if (f.agentCount < 2) continue;
      const agentRatio = f.agentCount / Math.max(this._totalAgents, f.agentCount);
      const score: EmergenceScore = {
        novelty: 0.3,
        utility: Math.round(agentRatio * 1000) / 1000,
        consensus: Math.round(agentRatio * 1000) / 1000,
        confidence: Math.round((0.3 * 0.3 + 0.3 * agentRatio + 0.4 * agentRatio) * 1000) / 1000,
      };
      const g = this.gate(score);
      if (g === "noise") continue;
      patterns.push({
        id: randomUUID(),
        type: "frequency",
        description: `Tag "${f.tag}" appears ${f.count}× across ${f.agentCount} agents`,
        score,
        relatedRecords: [],
        detectedAt: Date.now() / 1000,
        tags: [f.tag],
      });
    }

    return patterns;
  }
}
