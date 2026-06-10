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

/** Shared types for emergent memory detection. */

export interface TagFrequency {
  tag: string;
  count: number;
  agentCount: number;
  firstSeen: number;
  lastSeen: number;
}

export interface TagCorrelation {
  tagA: string;
  tagB: string;
  cooccurrence: number;
  lift: number;
  agentOverlap: number;
}

export interface CrossAgentPattern {
  topic: string;
  agents: string[];
  memoryCount: number;
  avgConfidence: number;
  commonTags: string[];
  firstSeen: number;
  lastSeen: number;
}

export interface EmergenceScore {
  novelty: number;
  utility: number;
  consensus: number;
  confidence: number;
}

export interface EmergentPattern {
  id: string;
  type: "frequency" | "correlation" | "cross_agent";
  description: string;
  score: EmergenceScore;
  relatedRecords: string[];
  detectedAt: number;
  tags: string[];
}

export type GateResult = "emergent" | "borderline" | "noise";

export interface TrendPoint {
  timestamp: number;
  count: number;
  agentCount: number;
}

export interface TrendLine {
  tag: string;
  points: TrendPoint[];
  slope: number;
  direction: "rising" | "falling" | "stable";
}

export interface TagTrend {
  tag: string;
  currentCount: number;
  previousCount: number;
  changePercent: number;
  direction: "rising" | "falling" | "stable";
}
