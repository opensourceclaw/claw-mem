# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
claw-mem Skill Store (v4.11.0)

In-memory storage for extracted skills. Follows the lazy-load pattern:
no persistence by default. Can be extended with file persistence in
future versions.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional

from .skill_extractor import Skill


class SkillStore:
    """In-memory store for Skill objects.

    Stores skills keyed by a generated ID and indexed by name for
    fast lookup and deduplication (automatic merge on same-name skills).

    Usage::

        store = SkillStore()
        sid = store.store(skill)
        found = store.get(sid)
        results = store.search("management")
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}  # id -> Skill
        self._name_index: Dict[str, str] = {}  # name (lower) -> id

    # ── CRUD ───────────────────────────────────────────────────────

    def store(self, skill: Skill) -> str:
        """Store a skill. If a skill with the same name exists, merge them.

        Args:
            skill: Skill object to store.

        Returns:
            skill_id: Unique skill identifier string.
        """
        name_key = skill.name.lower()

        if name_key in self._name_index:
            # Merge with existing
            existing_id = self._name_index[name_key]
            existing = self._skills[existing_id]
            merged = self._merge(existing, skill)
            self._skills[existing_id] = merged
            return existing_id

        # New skill
        skill_id = str(uuid.uuid4())[:8]
        self._skills[skill_id] = skill
        self._name_index[name_key] = skill_id
        return skill_id

    def get(self, skill_id: str) -> Optional[Skill]:
        """Retrieve a skill by ID.

        Args:
            skill_id: Skill identifier.

        Returns:
            Skill object or None if not found.
        """
        return self._skills.get(skill_id)

    def delete(self, skill_id: str) -> bool:
        """Delete a skill by ID.

        Args:
            skill_id: Skill identifier.

        Returns:
            True if deleted, False if not found.
        """
        skill = self._skills.pop(skill_id, None)
        if skill is None:
            return False

        name_key = skill.name.lower()
        if self._name_index.get(name_key) == skill_id:
            del self._name_index[name_key]

        return True

    def list_all(self) -> List[Skill]:
        """Return all stored skills.

        Returns:
            List of Skill objects.
        """
        return list(self._skills.values())

    def search(self, keyword: str) -> List[Skill]:
        """Search skills by keyword matching name and applicability.

        Args:
            keyword: Search term (case-insensitive substring match).

        Returns:
            List of matching Skill objects.
        """
        kw = keyword.lower()
        results: List[Skill] = []

        for skill in self._skills.values():
            if kw in skill.name.lower() or kw in skill.applicability.lower():
                results.append(skill)

        return results

    def count(self) -> int:
        """Return the number of stored skills."""
        return len(self._skills)

    def clear(self) -> None:
        """Remove all stored skills."""
        self._skills.clear()
        self._name_index.clear()

    # ── merge logic ────────────────────────────────────────────────

    @staticmethod
    def _merge(existing: Skill, incoming: Skill) -> Skill:
        """Merge two skills with the same name.

        Strategy:
          - steps: union (preserving order, removing duplicates)
          - applicability: use the longer/more specific one
          - confidence: weighted average by source_triplets
          - source: "merged"
          - other fields: from the more recent skill
        """
        # Merge steps (order-preserving union)
        seen_steps: set = set()
        merged_steps: List[str] = []
        for step in existing.steps + incoming.steps:
            if step not in seen_steps:
                seen_steps.add(step)
                merged_steps.append(step)

        # Applicability: use the longer one
        if len(incoming.applicability) > len(existing.applicability):
            applicability = incoming.applicability
        else:
            applicability = existing.applicability

        # Confidence: weighted average
        total = existing.source_triplets + incoming.source_triplets
        if total > 0:
            confidence = round(
                (existing.confidence * existing.source_triplets
                 + incoming.confidence * incoming.source_triplets)
                / total,
                2,
            )
        else:
            confidence = max(existing.confidence, incoming.confidence)

        # Source triplets: sum
        source_triplets = existing.source_triplets + incoming.source_triplets

        return Skill(
            name=existing.name,
            steps=merged_steps,
            applicability=applicability,
            confidence=confidence,
            compression_ratio=source_triplets / 1.0,
            source_triplets=source_triplets,
            created_at=min(existing.created_at, incoming.created_at),
            source="merged",
        )
