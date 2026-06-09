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
 * Skill Store
 *
 * In-memory storage for extracted skills. Follows the lazy-load pattern:
 * no persistence by default.
 */

import { randomUUID } from "crypto";
import { Skill } from "./skill_extractor";

export class SkillStore {
  private _skills: Map<string, Skill> = new Map(); // id -> Skill
  private _nameIndex: Map<string, string> = new Map(); // name (lower) -> id

  // ── CRUD ─────────────────────────────────────────────────────────

  /**
   * Store a skill. If a skill with the same name exists, merge them.
   *
   * @param skill - Skill object to store
   * @returns skill_id: Unique skill identifier string
   */
  store(skill: Skill): string {
    const nameKey = skill.name.toLowerCase();

    if (this._nameIndex.has(nameKey)) {
      // Merge with existing
      const existingId = this._nameIndex.get(nameKey)!;
      const existing = this._skills.get(existingId)!;
      const merged = this._merge(existing, skill);
      this._skills.set(existingId, merged);
      return existingId;
    }

    // New skill
    const skillId = randomUUID().slice(0, 8);
    this._skills.set(skillId, skill);
    this._nameIndex.set(nameKey, skillId);
    return skillId;
  }

  /**
   * Retrieve a skill by ID.
   *
   * @param skillId - Skill identifier
   * @returns Skill object or undefined if not found
   */
  get(skillId: string): Skill | undefined {
    return this._skills.get(skillId);
  }

  /**
   * Delete a skill by ID.
   *
   * @param skillId - Skill identifier
   * @returns True if deleted, false if not found
   */
  delete(skillId: string): boolean {
    const skill = this._skills.get(skillId);
    if (skill == null) return false;

    this._skills.delete(skillId);

    const nameKey = skill.name.toLowerCase();
    if (this._nameIndex.get(nameKey) === skillId) {
      this._nameIndex.delete(nameKey);
    }
    return true;
  }

  /**
   * Return all stored skills.
   *
   * @returns Array of Skill objects
   */
  list_all(): Skill[] {
    return Array.from(this._skills.values());
  }

  /**
   * Search skills by keyword matching name and applicability.
   *
   * @param keyword - Search term (case-insensitive substring match)
   * @returns Array of matching Skill objects
   */
  search(keyword: string): Skill[] {
    const kw = keyword.toLowerCase();
    const results: Skill[] = [];
    for (const skill of this._skills.values()) {
      if (
        skill.name.toLowerCase().includes(kw) ||
        skill.applicability.toLowerCase().includes(kw)
      ) {
        results.push(skill);
      }
    }
    return results;
  }

  /** Return the number of stored skills. */
  count(): number {
    return this._skills.size;
  }

  /** Remove all stored skills. */
  clear(): void {
    this._skills.clear();
    this._nameIndex.clear();
  }

  // ── Merge logic ──────────────────────────────────────────────────

  private _merge(existing: Skill, incoming: Skill): Skill {
    // Merge steps (order-preserving union)
    const seenSteps = new Set<string>();
    const mergedSteps: string[] = [];
    for (const step of [...existing.steps, ...incoming.steps]) {
      if (!seenSteps.has(step)) {
        seenSteps.add(step);
        mergedSteps.push(step);
      }
    }

    // Applicability: use the longer one
    const applicability =
      incoming.applicability.length > existing.applicability.length
        ? incoming.applicability
        : existing.applicability;

    // Confidence: weighted average
    const total = existing.source_triplets + incoming.source_triplets;
    let confidence: number;
    if (total > 0) {
      confidence = Math.round(
        ((existing.confidence * existing.source_triplets +
          incoming.confidence * incoming.source_triplets) /
          total) *
          100,
      ) / 100;
    } else {
      confidence = Math.max(existing.confidence, incoming.confidence);
    }

    // Source triplets: sum
    const sourceTriplets = existing.source_triplets + incoming.source_triplets;

    return {
      name: existing.name,
      steps: mergedSteps,
      applicability,
      confidence,
      compression_ratio: sourceTriplets / 1.0,
      source_triplets: sourceTriplets,
      created_at: Math.min(existing.created_at, incoming.created_at),
      source: "merged",
    };
  }
}
