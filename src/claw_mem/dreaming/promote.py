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
Dreaming Engine — Promote Phase (Promoter | v4.12.0)

Persists scored candidates and extracted patterns into long-term storage:
  - episodic memories → SemanticStorage
  - semantic → SemanticStorage.update() reinforcement
  - procedural → ProceduralStorage
  - skills → SkillStore
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .deep import ScoredCandidate
    from .rem import REMResult


@dataclass
class PromotionResult:
    """Result of the promote phase.

    Attributes:
        episodic_promoted: Count of episodic → semantic promotions.
        semantic_reinforced: Count of semantic memory reinforcements.
        procedural_promoted: Count of procedural entries written.
        skill_stored: Count of skills stored via SkillStore.
        dry_run: If True, no actual writes occurred.
    """

    episodic_promoted: int = 0
    semantic_reinforced: int = 0
    procedural_promoted: int = 0
    skill_stored: int = 0
    dry_run: bool = False

    @property
    def total(self) -> int:
        return (
            self.episodic_promoted
            + self.semantic_reinforced
            + self.procedural_promoted
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episodic_promoted": self.episodic_promoted,
            "semantic_reinforced": self.semantic_reinforced,
            "procedural_promoted": self.procedural_promoted,
            "skill_stored": self.skill_stored,
            "total": self.total,
            "dry_run": self.dry_run,
        }


class Promoter:
    """Persist dreaming pipeline results into long-term storage.

    Routes candidates to the appropriate storage based on memory type
    and persists extracted skills via SkillStore.
    """

    def __init__(self, memory_manager: Any, dry_run: bool = False):
        self._mm = memory_manager
        self._dry_run = dry_run

    def promote(
        self, candidates: List[ScoredCandidate], rem_result: REMResult
    ) -> PromotionResult:
        """Promote candidates and REM results to long-term storage.

        Args:
            candidates: Filtered ScoredCandidate list.
            rem_result: Pattern extraction results.

        Returns:
            PromotionResult with counts per storage type.
        """
        result = PromotionResult(dry_run=self._dry_run)

        # ── 1. Promote candidates based on memory type ──────────────
        for c in candidates:
            mtype = c.signal.memory_type

            if mtype == "episodic" or mtype == "":
                self._promote_to_semantic(c, result)
            elif mtype == "semantic":
                self._reinforce_semantic(c, result)
            elif mtype == "procedural":
                self._promote_to_procedural(c, result)

        # ── 2. Store extracted skills ──────────────────────────────
        if rem_result.skills:
            result.skill_stored = self._store_skills(rem_result.skills)

        return result

    # ── internal promotion methods ─────────────────────────────────

    def _promote_to_semantic(self, c: ScoredCandidate, result: PromotionResult) -> None:
        """Promote an episodic memory to semantic storage."""
        if self._dry_run:
            result.episodic_promoted += 1
            return

        try:
            self._mm.semantic.store({
                "content": f"[dreaming] {c.signal.content}",
                "tags": c.signal.tags + ["dreaming", f"score_{c.composite:.2f}"],
                "metadata": {
                    "source": "dreaming_engine",
                    "composite_score": c.composite,
                    "frequency_score": c.frequency_score,
                    "conceptual_richness": c.conceptual_richness_score,
                },
                "timestamp": datetime.now().isoformat(),
            })
            result.episodic_promoted += 1
        except Exception:
            pass

    def _reinforce_semantic(self, c: ScoredCandidate, result: PromotionResult) -> None:
        """Reinforce an existing semantic memory."""
        if self._dry_run:
            result.semantic_reinforced += 1
            return

        try:
            existing = self._mm.semantic.get_all()
            for mem in existing:
                if c.signal.content in mem.get("content", ""):
                    mid = mem.get("id")
                    if mid:
                        reinforced = f"[reinforced:{c.composite:.2f}] {mem['content']}"
                        self._mm.semantic.update(mid, reinforced)
                        result.semantic_reinforced += 1
                        break
        except Exception:
            pass

    def _promote_to_procedural(self, c: ScoredCandidate, result: PromotionResult) -> None:
        """Persist a procedural entry."""
        if self._dry_run:
            result.procedural_promoted += 1
            return

        try:
            self._mm.procedural.store({
                "content": c.signal.content,
                "tags": c.signal.tags + ["dreaming_procedural"],
                "metadata": {"source": "dreaming_engine", "composite_score": c.composite},
                "timestamp": datetime.now().isoformat(),
            })
            result.procedural_promoted += 1
        except Exception:
            pass

    def _store_skills(self, skills: List[Any]) -> int:
        """Store extracted skills via SkillStore."""
        if self._dry_run or not skills:
            return 0

        count = 0
        try:
            store = self._mm.skill_store
            for skill in skills:
                store.store(skill)
                count += 1
        except Exception:
            pass

        return count
