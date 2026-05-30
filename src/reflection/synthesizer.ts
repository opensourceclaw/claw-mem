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
 * Belief Synthesizer
 *
 * Synthesizes observations into structured beliefs using keyword-based
 * heuristics (with LLM escalation for complex cases).
 */

// ── Data classes ──────────────────────────────────────────────────────

export interface Observation {
  source: string;
  content: string;
  timestamp: string;
  memory_id: string;
  metadata: Record<string, unknown>;
}

export interface Belief {
  id: string;
  statement: string;
  confidence: number;
  observations: string[];
  category: string;
  created_at: string;
  version: number;
}

export interface SynthesizerConfig {
  min_observations: number;
  min_confidence: number;
  use_llm: boolean;
  llm_model: string;
}

// ── BeliefSynthesizer ─────────────────────────────────────────────────

export class BeliefSynthesizer {
  // Patterns for extracting observations from memory content
  static OBSERVATION_PATTERNS: Array<[RegExp, string, number]> = [
    [/User prefers (.+)/i, "user_preference", 0.8],
    [/User likes (.+)/i, "user_preference", 0.8],
    [/User dislikes (.+)/i, "user_preference", 0.7],
    [/User (?:uses|needs|requires|wants) (.+)/i, "user_fact", 0.6],
    [/Important: (.+)/i, "fact", 0.9],
    [/Learned: (.+)/i, "fact", 0.8],
    [/(?:Decided|Resolved): (.+)/i, "decision", 0.7],
    [/Error: (.+?)(?:\. |$)/i, "error_pattern", 0.6],
    [/(?:Always|Never) (.+)/i, "pattern", 0.5],
  ];

  config: SynthesizerConfig;
  private _beliefCounter = 0;

  constructor(config?: Partial<SynthesizerConfig>) {
    this.config = {
      min_observations: config?.min_observations ?? 2,
      min_confidence: config?.min_confidence ?? 0.3,
      use_llm: config?.use_llm ?? false,
      llm_model: config?.llm_model ?? "",
    };
  }

  /**
   * Extract observations from memory records.
   *
   * @param memories - List of memory dicts with content and metadata
   * @returns List of extracted observations
   */
  extract_observations(memories: Record<string, unknown>[]): Observation[] {
    const observations: Observation[] = [];

    for (const mem of memories) {
      const content = (mem.content as string) ?? "";
      if (!content) continue;

      for (const [pattern, category, confidence] of BeliefSynthesizer.OBSERVATION_PATTERNS) {
        const match = pattern.exec(content);
        if (match) {
          const extracted = match[1].trim();
          observations.push({
            source: (mem.source as string) ?? "memory",
            content: extracted,
            timestamp: (mem.timestamp as string) ?? "",
            memory_id: (mem.id as string) ?? "",
            metadata: {
              category,
              extraction_confidence: confidence,
              original_content: content,
            },
          });
          break; // First match only per memory
        }
      }
    }

    return observations;
  }

  /**
   * Synthesize observations into beliefs.
   *
   * @param observations - Extracted observations
   * @param userId - User identifier for the belief
   * @returns List of synthesized beliefs
   */
  synthesize(
    observations: Observation[],
    userId: string = "",
  ): Belief[] {
    if (observations.length < this.config.min_observations) return [];

    const beliefs: Belief[] = [];
    const topics = this._group_by_topic(observations);

    for (const [topic, obsList] of Object.entries(topics)) {
      if (obsList.length < this.config.min_observations) continue;

      const avgConfidence =
        obsList.reduce(
          (sum, o) =>
            sum + ((o.metadata.extraction_confidence as number) ?? 0.5),
          0,
        ) / obsList.length;

      if (avgConfidence < this.config.min_confidence) continue;

      const statement = this._synthesize_statement(topic, obsList);
      this._beliefCounter++;

      beliefs.push({
        id: `BEL_${String(this._beliefCounter).padStart(4, "0")}`,
        statement,
        confidence: Math.round(avgConfidence * 100) / 100,
        observations: obsList
          .filter((o) => o.memory_id)
          .map((o) => o.memory_id),
        category: (obsList[0].metadata.category as string) ?? "general",
        created_at: new Date().toISOString(),
        version: 1,
      });
    }

    return beliefs;
  }

  private _group_by_topic(
    observations: Observation[],
  ): Record<string, Observation[]> {
    const topics: Record<string, Observation[]> = {};
    const stopWords = new Set([
      "the", "a", "an", "is", "are", "was", "were",
      "of", "in", "to", "for",
    ]);

    for (const obs of observations) {
      const words = new Set(
        obs.content
          .split(/\s+/)
          .map((w) => w.toLowerCase().replace(/[.,!?;:()\[\]{}]/g, "")),
      );
      for (const sw of stopWords) words.delete(sw);

      let bestTopic: string | null = null;
      let bestScore = 0;

      for (const topic of Object.keys(topics)) {
        const topicWords = new Set(topic.split(/\s+/));
        let score = 0;
        for (const w of topicWords) {
          if (words.has(w)) score++;
        }
        if (score > bestScore) {
          bestScore = score;
          bestTopic = topic;
        }
      }

      if (bestScore >= 1 && bestTopic) {
        topics[bestTopic].push(obs);
      } else {
        const key =
          words.size > 0
            ? [...words].sort((a, b) => b.length - a.length)[0]
            : "general";
        if (!topics[key]) topics[key] = [];
        topics[key].push(obs);
      }
    }

    return topics;
  }

  private _synthesize_statement(
    topic: string,
    obsList: Observation[],
  ): string {
    if (obsList.length === 0) return `Observed: ${topic}`;

    const best = obsList.reduce((a, b) =>
      ((a.metadata.extraction_confidence as number) ?? 0) >=
      ((b.metadata.extraction_confidence as number) ?? 0)
        ? a
        : b,
    );
    return `Belief about ${topic}: ${best.content}`;
  }
}
