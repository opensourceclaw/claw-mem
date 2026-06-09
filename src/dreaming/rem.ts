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
 * Dreaming Engine -- REM Phase (Pattern Extractor | v4.12.0)
 *
 * Builds triplets from scored candidates, runs SkillExtractor,
 * and groups results into topic summaries by tag.
 */

import type { ScoredCandidate } from "./deep";

// ── REMResult ────────────────────────────────────────────────────────────

export interface REMResult {
  /** List of extracted (s, p, o) dicts. */
  triplets: Triplet[];
  /** List of extracted Skill objects. */
  skills: unknown[];
  /** Dict mapping topic tag to summary string. */
  topicSummaries: Record<string, string>;
  /** Total number of triplets extracted. */
  extractedCount: number;
  /** Total number of skills extracted. */
  skillsCount: number;
}

export interface Triplet {
  s: string;
  p: string;
  o: string;
}

export function createREMResult(overrides?: Partial<REMResult>): REMResult {
  return {
    triplets: [],
    skills: [],
    topicSummaries: {},
    extractedCount: 0,
    skillsCount: 0,
    ...overrides,
  };
}

export function remResultToDict(r: REMResult): Record<string, unknown> {
  return {
    extracted_count: r.extractedCount,
    skills_count: r.skillsCount,
    topic_summaries: r.topicSummaries,
    triplets: r.triplets,
  };
}

// ── PatternExtractor ─────────────────────────────────────────────────────

export class PatternExtractor {
  private _llm: unknown;

  constructor(llmProvider?: unknown) {
    this._llm = llmProvider;
  }

  /**
   * Run pattern extraction on scored candidates.
   *
   * @param candidates - Filtered ScoredCandidate list from deep phase.
   * @returns REMResult with triplets, skills, and topic summaries.
   */
  extract(candidates: ScoredCandidate[]): REMResult {
    const result = createREMResult();

    // 1. Build triplets from candidate content
    const triplets = this._buildTriplets(candidates);
    result.triplets = triplets;
    result.extractedCount = triplets.length;

    // 2. Run SkillExtractor (stub -- no dependency in TS)
    //    In the Python version this delegates to SkillExtractor(llm, mode="rule").
    //    Here we produce a simplified stub.
    const skills = this._extractSkills(triplets);
    result.skills = skills;
    result.skillsCount = skills.length;

    // 3. Build topic summaries by tag
    result.topicSummaries = this._buildTopicSummaries(candidates);

    return result;
  }

  // ── triplet construction ───────────────────────────────────────────────

  /**
   * Build simple (subject, predicate, object) triplets from candidates.
   *
   * Uses a simple heuristic: content before a colon is the subject,
   * after the colon is the object. Falls back to word splitting.
   */
  private _buildTriplets(candidates: ScoredCandidate[]): Triplet[] {
    const triplets: Triplet[] = [];
    for (const c of candidates) {
      const content = c.signal.content;
      if (!content) continue;

      let subject: string;
      let obj: string;

      // Simple split heuristic
      const colonIdx = content.indexOf(":");
      const cnColonIdx = content.indexOf("\uff1a");
      const splitIdx = colonIdx >= 0 ? colonIdx : cnColonIdx;

      if (splitIdx >= 0) {
        subject = content.slice(0, splitIdx).trim().slice(0, 50);
        obj = content.slice(splitIdx + 1).trim().slice(0, 100);
      } else {
        const words = content.split(/\s+/);
        if (words.length >= 3) {
          subject = words.slice(0, 2).join(" ").slice(0, 50);
          obj = words.slice(2).join(" ").slice(0, 100);
        } else {
          subject = content.slice(0, 50);
          obj = "";
        }
      }

      triplets.push({ s: subject, p: "relates_to", o: obj });
    }
    return triplets;
  }

  /**
   * Run SkillExtractor on the constructed triplets.
   *
   * Stub implementation -- returns empty list since the Python
   * SkillExtractor dependency is not available in TS.
   */
  private _extractSkills(_triplets: Triplet[]): unknown[] {
    // In Python this imports and invokes:
    //   from claw_mem.extraction.openie_extractor import Triplet
    //   from claw_mem.extraction.skill_extractor import SkillExtractor
    //   extractor = SkillExtractor(llm_provider=self._llm, mode="rule")
    //   return extractor.extract(triplet_objs)
    // For TS we return an empty list as a no-op stub.
    return [];
  }

  // ── topic summaries ────────────────────────────────────────────────────

  /**
   * Group candidates by tags and build concise topic summaries.
   */
  private _buildTopicSummaries(
    candidates: ScoredCandidate[],
  ): Record<string, string> {
    const topicGroups = new Map<string, string[]>();

    for (const c of candidates) {
      const tags = c.signal.tags?.length ? c.signal.tags : ["general"];
      for (const tag of tags) {
        if (!topicGroups.has(tag)) {
          topicGroups.set(tag, []);
        }
        topicGroups.get(tag)!.push(c.signal.content);
      }
    }

    const summaries: Record<string, string> = {};
    for (const [tag, contents] of topicGroups) {
      if (contents.length === 1) {
        summaries[tag] = contents[0].slice(0, 100);
      } else {
        const preview = contents
          .slice(0, 5)
          .map((c) => c.slice(0, 60))
          .join(" | ");
        const suffix =
          contents.length > 5
            ? ` ... (+${contents.length - 5} more)`
            : "";
        summaries[tag] = `[${contents.length} items] ${preview}${suffix}`;
      }
    }

    return summaries;
  }
}
