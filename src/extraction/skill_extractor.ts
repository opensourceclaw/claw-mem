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
 * Skill Extraction
 *
 * Abstracts OpenIE triplets into reusable operational patterns (skills).
 * Supports three extraction modes: llm, rule, auto.
 */

import { Triplet } from "./openie_extractor";

// ── Data class ────────────────────────────────────────────────────────

export interface Skill {
  name: string;
  steps: string[];
  applicability: string;
  confidence: number;
  compression_ratio: number;
  source_triplets: number;
  created_at: number;
  source: "llm" | "rule" | "merged";
}

// ── LLM System Prompt ─────────────────────────────────────────────────

const LLM_SYSTEM_PROMPT =
  "You are a skill extraction engine. Given a group of related knowledge " +
  "triplets (all sharing the same subject-predicate pattern), abstract " +
  "them into a reusable skill.\n\n" +
  "Output a JSON array of skill objects. Each skill must have:\n" +
  '  - "name": short skill name (3\u20138 words)\n' +
  '  - "steps": list of actionable step descriptions (2\u20135 steps)\n' +
  '  - "applicability": when to apply this skill (1 sentence)\n' +
  '  - "confidence": float 0\u20131 indicating extraction confidence\n\n' +
  "Example input triplets:\n" +
  "  (Alice, manages, team), (Alice, manages, project), " +
  "(Alice, manages, budget)\n\n" +
  "Example output:\n" +
  '[{"name":"Resource Management",' +
  '"steps":["Identify resources","Assign priorities","Track progress",' +
  '"Adjust allocations"],' +
  '"applicability":"When managing teams, projects, or budgets",' +
  '"confidence":0.85}]\n\n' +
  "Only output valid JSON. Do not include markdown fences or commentary.";

// ── Rule-mode templates ──────────────────────────────────────────────

const RULE_SKILL_TEMPLATES: Record<string, { name: string; steps: string[]; applicability: string }> = {
  "\u8d1f\u8d23": {
    name: "\u8d23\u4efb\u5236\u5de5\u4f5c",
    steps: [
      "\u786e\u8ba4\u8d23\u4efb\u8303\u56f4",
      "\u89c4\u5212\u6267\u884c\u8def\u5f84",
      "\u63a8\u8fdb\u4ea4\u4ed8",
      "\u6c47\u62a5\u8fdb\u5c55",
    ],
    applicability: "\u5f53\u9700\u8981\u660e\u786e\u8d23\u4efb\u5206\u5de5\u548c\u63a8\u8fdb\u4efb\u52a1\u65f6",
  },
  "\u5f00\u53d1": {
    name: "\u8f6f\u4ef6\u5f00\u53d1",
    steps: [
      "\u7406\u89e3\u9700\u6c42",
      "\u8bbe\u8ba1\u65b9\u6848",
      "\u7f16\u7801\u5b9e\u73b0",
      "\u6d4b\u8bd5\u9a8c\u8bc1",
    ],
    applicability: "\u5f53\u6d89\u53ca\u8f6f\u4ef6\u5f00\u53d1\u6216\u6280\u672f\u5b9e\u73b0\u65f6",
  },
  is: {
    name: "Identity Classification",
    steps: [
      "Identify the entity",
      "Determine its category",
      "Apply categorization rules",
    ],
    applicability: "When classifying or categorizing entities",
  },
  has: {
    name: "Possession Pattern",
    steps: [
      "Identify the owner",
      "Catalog possessions",
      "Track changes over time",
    ],
    applicability: "When tracking ownership or possession relationships",
  },
};

const GENERIC_RULE_TEMPLATE = {
  name: "\u901a\u7528\u6a21\u5f0f",
  steps: [
    "\u5206\u6790\u8f93\u5165\u4fe1\u606f",
    "\u8bc6\u522b\u5173\u952e\u6a21\u5f0f",
    "\u5e94\u7528\u6a21\u5f0f\u89c4\u5219",
    "\u603b\u7ed3\u8f93\u51fa",
  ],
  applicability: "\u5f53\u51fa\u73b0\u91cd\u590d\u6a21\u5f0f\u65f6",
};

// ── SkillExtractor ────────────────────────────────────────────────────

export type SkillExtractionMode = "llm" | "rule" | "auto";

export class SkillExtractor {
  private static _MIN_GROUP_SIZE = 2;

  private _llm: any;
  private _mode: SkillExtractionMode;

  constructor(llm_provider?: any, mode: SkillExtractionMode = "auto") {
    this._llm = llm_provider;
    this._mode = ["llm", "rule", "auto"].includes(mode) ? mode : "auto";
  }

  get mode(): SkillExtractionMode {
    return this._mode;
  }

  // ── Public API ───────────────────────────────────────────────────

  /**
   * Extract skills from a list of triplets.
   *
   * @param triplets - List of Triplet objects (from OpenIEExtractor)
   * @returns List of Skill objects
   */
  extract(triplets: Triplet[]): Skill[] {
    if (triplets.length === 0) return [];

    // 1. Group by (subject, predicate)
    const groups = this._group_triplets(triplets);

    // 2. Filter: only groups with >= MIN_GROUP_SIZE triplets
    const validGroups: Record<string, Triplet[]> = {};
    for (const [key, group] of Object.entries(groups)) {
      if (group.length >= SkillExtractor._MIN_GROUP_SIZE) {
        validGroups[key] = group;
      }
    }

    if (Object.keys(validGroups).length === 0) return [];

    // 3. Extract skills based on mode
    let skills: Skill[];
    if (this._mode === "llm") {
      skills = this._extract_llm(validGroups);
    } else if (this._mode === "rule") {
      skills = this._extract_rule(validGroups);
    } else {
      skills = this._extract_auto(validGroups);
    }

    // 4. Calculate compression ratios
    for (const skill of skills) {
      if (skill.source_triplets > 0) {
        skill.compression_ratio = skill.source_triplets / 1.0;
      }
    }

    return skills;
  }

  // ── Grouping ─────────────────────────────────────────────────────

  private _group_triplets(triplets: Triplet[]): Record<string, Triplet[]> {
    const groups: Record<string, Triplet[]> = {};
    for (const t of triplets) {
      const key = `${t.subject}|${t.predicate}`;
      if (!groups[key]) groups[key] = [];
      groups[key].push(t);
    }
    return groups;
  }

  // ── Rule mode ────────────────────────────────────────────────────

  private _extract_rule(groups: Record<string, Triplet[]>): Skill[] {
    const skills: Skill[] = [];

    for (const [key, group] of Object.entries(groups)) {
      const [subject, predicate] = key.split("|");
      const count = group.length;

      let template = RULE_SKILL_TEMPLATES[predicate];
      if (!template) {
        template = {
          name: `${subject}-${predicate} \u6a21\u5f0f`,
          steps: [...GENERIC_RULE_TEMPLATE.steps],
          applicability: GENERIC_RULE_TEMPLATE.applicability,
        };
      }

      const confidence = Math.min(Math.round((0.5 + 0.1 * (count - 2)) * 100) / 100, 0.9);

      skills.push({
        name: template.name,
        steps: [...template.steps],
        applicability: template.applicability,
        confidence,
        compression_ratio: 1.0,
        source_triplets: count,
        created_at: Date.now() / 1000,
        source: "rule",
      });
    }

    return skills;
  }

  // ── LLM mode ────────────────────────────────────────────────────

  private _extract_llm(groups: Record<string, Triplet[]>): Skill[] {
    if (this._llm == null) return [];

    const allSkills: Skill[] = [];

    for (const [key, group] of Object.entries(groups)) {
      const [subject, predicate] = key.split("|");
      const count = group.length;

      const promptLines = [
        `Group: ${subject} -${predicate}-> ... (${count} instances)`,
      ];
      for (const t of group) {
        promptLines.push(`  (${t.subject}, ${t.predicate}, ${t.object})`);
      }
      const prompt = promptLines.join("\n");

      try {
        const raw = this._llm.generate({
          prompt,
          system: LLM_SYSTEM_PROMPT,
          max_tokens: 512,
        });
        const parsed = this._parse_skill_json(raw);
        for (const item of parsed) {
          allSkills.push({
            name: item.name ?? `${subject}-${predicate}`,
            steps: item.steps ?? [],
            applicability: item.applicability ?? "",
            confidence: Number(item.confidence ?? 0.7),
            compression_ratio: 1.0,
            source_triplets: count,
            created_at: Date.now() / 1000,
            source: "llm",
          });
        }
      } catch {
        continue;
      }
    }

    return allSkills;
  }

  private _parse_skill_json(raw: string): any[] {
    if (!raw || !raw.trim()) return [];

    let text = raw.trim();

    // Remove markdown code fences
    const fenceMatch = text.match(/```(?:json)?\s*\n?(.*?)\n?```/s);
    if (fenceMatch) {
      text = fenceMatch[1].trim();
    }

    // Try direct parse
    try {
      const result = JSON.parse(text);
      if (Array.isArray(result)) return result;
      return [];
    } catch {
      // Try to find JSON array
      const arrayMatch = text.match(/\[.*\]/s);
      if (arrayMatch) {
        try {
          const result = JSON.parse(arrayMatch[0]);
          if (Array.isArray(result)) return result;
        } catch {
          // fall through
        }
      }
      return [];
    }
  }

  // ── Auto mode ───────────────────────────────────────────────────

  private _extract_auto(groups: Record<string, Triplet[]>): Skill[] {
    if (this._llm != null) {
      try {
        const skills = this._extract_llm(groups);
        if (skills.length > 0) return skills;
      } catch {
        // fall through
      }
    }
    return this._extract_rule(groups);
  }
}
