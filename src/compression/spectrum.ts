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
 * CompressionSpectrum - Four-tier memory compression (v2.15.0).
 *
 * Tiered abstraction:
 *   L0 Episodes -> L1 Skills -> L2 Rules -> L3 Principles
 *
 * Trigger-based (not continuous): activated by access/apply/verify counts.
 * Rule-based extraction (no LLM dependency in MVP).
 * Default: disabled (enable_compression=false).
 */

import * as crypto from "crypto";

// ── Data structures ──────────────────────────────────────────────────────

export interface SkillEntry {
  skillId: string;
  title: string;
  description: string;
  steps: string[];
  sourceEpisodes: string[];
  tags: string[];
  applyCount: number;
  createdAt: number;
  updatedAt: number;
}

export interface RuleEntry {
  ruleId: string;
  condition: string;
  action: string;
  confidence: number;
  sourceSkills: string[];
  validationCount: number;
  createdAt: number;
}

export interface PrincipleEntry {
  principleId: string;
  content: string;
  confidence: number;
  sourceRules: string[];
  createdAt: number;
}

export interface CompressedMemory {
  memoryId: string;
  level: number;
  content: string;
  sourceIds: string[];
  createdAt: number;
  metadata: Record<string, unknown>;
}

function createSkillId(): string {
  return `skill_${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
}

function createRuleId(): string {
  return `rule_${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
}

function createPrincipleId(): string {
  return `prin_${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
}

// ── MemoryManager abstraction ────────────────────────────────────────────

export interface SpectrumMemoryManager {
  get(memoryId: string): Record<string, unknown> | undefined;
}

// ── CompressionSpectrum ──────────────────────────────────────────────────

export class CompressionSpectrum {
  private _skills: Map<string, SkillEntry> = new Map();
  private _rules: Map<string, RuleEntry> = new Map();
  private _principles: Map<string, PrincipleEntry> = new Map();
  private _episodeAccess: Map<string, number> = new Map();

  private _skillAccessThreshold: number;
  private _ruleApplyThreshold: number;
  private _principleVerifyThreshold: number;

  private _mm: SpectrumMemoryManager | undefined;

  constructor(
    memoryManager?: SpectrumMemoryManager,
    accessThreshold = 5,
    applyThreshold = 3,
    verifyThreshold = 2,
  ) {
    this._mm = memoryManager;
    this._skillAccessThreshold = accessThreshold;
    this._ruleApplyThreshold = applyThreshold;
    this._principleVerifyThreshold = verifyThreshold;
  }

  // ── Trigger ──────────────────────────────────────────────────────────

  recordAccess(memoryId: string): CompressedMemory | undefined {
    const count = (this._episodeAccess.get(memoryId) ?? 0) + 1;
    this._episodeAccess.set(memoryId, count);
    if (count >= this._skillAccessThreshold) {
      return this._compressToSkill(memoryId);
    }
    return undefined;
  }

  recordApply(skillId: string): CompressedMemory | undefined {
    const skill = this._skills.get(skillId);
    if (!skill) return undefined;

    skill.applyCount += 1;
    if (skill.applyCount >= this._ruleApplyThreshold) {
      return this._compressToRule(skillId);
    }
    return undefined;
  }

  recordVerify(ruleId: string): CompressedMemory | undefined {
    const rule = this._rules.get(ruleId);
    if (!rule) return undefined;

    rule.validationCount += 1;
    if (rule.validationCount >= this._principleVerifyThreshold) {
      return this._compressToPrinciple(ruleId);
    }
    return undefined;
  }

  // ── Compression ──────────────────────────────────────────────────────

  private _compressToSkill(episodeId: string): CompressedMemory | undefined {
    const content = this._getEpisodeContent(episodeId);
    if (!content) return undefined;

    const steps = this._extractSteps(content);
    if (steps.length < 2) return undefined;

    const title = content.split("\n")[0].trim().slice(0, 80);
    const tags = this._extractTags(content);
    const now = Date.now() / 1000;

    const skillId = createSkillId();
    const skill: SkillEntry = {
      skillId,
      title,
      description: content.slice(0, 200),
      steps,
      sourceEpisodes: [episodeId],
      tags,
      applyCount: 0,
      createdAt: now,
      updatedAt: now,
    };
    this._skills.set(skillId, skill);

    const body = [
      `[Skill] ${title}`,
      ...steps.map((s, i) => `  ${i + 1}. ${s}`),
    ].join("\n");

    return {
      memoryId: skillId,
      level: 1,
      content: body,
      sourceIds: [episodeId],
      createdAt: now,
      metadata: { type: "skill", tags },
    };
  }

  private _compressToRule(skillId: string): CompressedMemory | undefined {
    const skill = this._skills.get(skillId);
    if (!skill) return undefined;

    const condition = `User needs ${skill.title}`;
    const action = skill.steps.slice(0, 3).join(" -> ");
    const now = Date.now() / 1000;

    const ruleId = createRuleId();
    const rule: RuleEntry = {
      ruleId,
      condition,
      action,
      confidence: 0.7,
      sourceSkills: [skillId],
      validationCount: 0,
      createdAt: now,
    };
    this._rules.set(ruleId, rule);

    return {
      memoryId: ruleId,
      level: 2,
      content: `[Rule] IF ${condition} THEN ${action}`,
      sourceIds: [skillId],
      createdAt: now,
      metadata: { type: "rule", confidence: 0.7 },
    };
  }

  private _compressToPrinciple(ruleId: string): CompressedMemory | undefined {
    const rule = this._rules.get(ruleId);
    if (!rule) return undefined;

    const now = Date.now() / 1000;
    const content = `Prioritize: ${rule.action.slice(0, 100)}`;

    const principleId = createPrincipleId();
    const principle: PrincipleEntry = {
      principleId,
      content,
      confidence: rule.confidence,
      sourceRules: [ruleId],
      createdAt: now,
    };
    this._principles.set(principleId, principle);

    return {
      memoryId: principleId,
      level: 3,
      content,
      sourceIds: [ruleId],
      createdAt: now,
      metadata: { type: "principle", confidence: rule.confidence },
    };
  }

  // ── Runtime config ───────────────────────────────────────────────────

  configureThresholds(
    thresholds: { access?: number; apply?: number; verify?: number },
  ): void {
    if (thresholds.access !== undefined) this._skillAccessThreshold = thresholds.access;
    if (thresholds.apply !== undefined) this._ruleApplyThreshold = thresholds.apply;
    if (thresholds.verify !== undefined) this._principleVerifyThreshold = thresholds.verify;
  }

  // ── Query ────────────────────────────────────────────────────────────

  getCompressed(
    memoryId?: string,
    level?: number,
  ): CompressedMemory[] {
    const results: CompressedMemory[] = [];

    for (const skill of this._skills.values()) {
      if (memoryId && !skill.sourceEpisodes.includes(memoryId)) continue;
      if (level !== undefined && level !== 1) continue;
      results.push({
        memoryId: skill.skillId,
        level: 1,
        content: `[Skill] ${skill.title}`,
        sourceIds: skill.sourceEpisodes,
        createdAt: skill.createdAt,
        metadata: { type: "skill" },
      });
    }

    return results;
  }

  // ── Helpers ──────────────────────────────────────────────────────────

  private _getEpisodeContent(memoryId: string): string | undefined {
    if (!this._mm) return undefined;
    try {
      const r = this._mm.get(memoryId);
      return r ? (r.content as string) : undefined;
    } catch {
      return undefined;
    }
  }

  private _extractSteps(content: string): string[] {
    const patterns: RegExp[] = [
      /(?:install|pip install|npm install|brew install)\s+\S+/gi,
      /(?:配置|设置|修改|创建|使用|运行|启动|停止|删除)\s+\S+/g,
      /(?:create|configure|set up|run|start|stop|delete)\s+\S+/gi,
    ];

    const steps: string[] = [];
    for (const p of patterns) {
      const matches = content.match(p);
      if (matches) steps.push(...matches);
    }

    // Deduplicate keeping order
    const seen = new Set<string>();
    const unique: string[] = [];
    for (const s of steps) {
      const key = s.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        unique.push(s);
      }
    }

    return unique.slice(0, 10);
  }

  private _extractTags(content: string): string[] {
    const keywords = [
      "python", "javascript", "typescript", "go", "rust",
      "redis", "postgresql", "mysql", "mongodb",
      "docker", "kubernetes", "aws", "api", "rest",
    ];
    const lower = content.toLowerCase();
    return keywords.filter((k) => lower.includes(k)).slice(0, 5);
  }

  // ── Stats ────────────────────────────────────────────────────────────

  getStats(): Record<string, unknown> {
    return {
      skills: this._skills.size,
      rules: this._rules.size,
      principles: this._principles.size,
      total_episodes_tracked: this._episodeAccess.size,
      thresholds: {
        skill_access: this._skillAccessThreshold,
        rule_apply: this._ruleApplyThreshold,
        principle_verify: this._principleVerifyThreshold,
      },
      enabled: true,
    };
  }
}
