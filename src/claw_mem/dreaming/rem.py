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
Dreaming Engine — REM Phase (Pattern Extractor | v4.12.0)

Builds triplets from scored candidates, runs SkillExtractor,
and groups results into topic summaries by tag.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .deep import ScoredCandidate


@dataclass
class REMResult:
    """Result of the REM pattern extraction phase.

    Attributes:
        triplets: List of extracted (s, p, o) dicts.
        skills: List of extracted Skill objects.
        topic_summaries: Dict mapping topic tag to summary string.
        extracted_count: Total number of triplets extracted.
        skills_count: Total number of skills extracted.
    """

    triplets: List[Dict[str, str]] = field(default_factory=list)
    skills: List[Any] = field(default_factory=list)
    topic_summaries: Dict[str, str] = field(default_factory=dict)
    extracted_count: int = 0
    skills_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "extracted_count": self.extracted_count,
            "skills_count": self.skills_count,
            "topic_summaries": self.topic_summaries,
            "triplets": self.triplets,
        }


class PatternExtractor:
    """Extract patterns from scored dreaming candidates.

    Reuses SkillExtractor from claw_mem.extraction.skill_extractor for
    skill pattern abstraction. Groups candidates by tags and generates
    topic summaries.
    """

    def __init__(self, llm_provider: Any = None):
        self._llm = llm_provider

    def extract(self, candidates: List[ScoredCandidate]) -> REMResult:
        """Run pattern extraction on scored candidates.

        Args:
            candidates: Filtered ScoredCandidate list from deep phase.

        Returns:
            REMResult with triplets, skills, and topic summaries.
        """
        result = REMResult()

        # 1. Build triplets from candidate content
        triplets = self._build_triplets(candidates)
        result.triplets = triplets
        result.extracted_count = len(triplets)

        # 2. Run SkillExtractor
        skills = self._extract_skills(triplets)
        result.skills = skills
        result.skills_count = len(skills)

        # 3. Build topic summaries by tag
        result.topic_summaries = self._build_topic_summaries(candidates)

        return result

    # ── triplet construction ───────────────────────────────────────

    def _build_triplets(self, candidates: List[ScoredCandidate]) -> List[Dict[str, str]]:
        """Build simple (subject, predicate, object) triplets from candidates.

        Uses a simple heuristic: the first noun phrase is the subject,
        the middle portion implies the predicate, and remaining content
        becomes the object.
        """
        triplets: List[Dict[str, str]] = []
        for c in candidates:
            content = c.signal.content
            if not content:
                continue
            # Simple split heuristic
            parts = content.split(":", 1) if ":" in content else content.split("：", 1)
            if len(parts) == 2:
                subject = parts[0].strip()[:50]
                obj = parts[1].strip()[:100]
            else:
                words = content.split()
                if len(words) >= 3:
                    subject = " ".join(words[:2])[:50]
                    obj = " ".join(words[2:])[:100]
                else:
                    subject = content[:50]
                    obj = ""

            triplets.append({
                "s": subject,
                "p": "relates_to",
                "o": obj,
            })

        return triplets

    def _extract_skills(self, triplets: List[Dict[str, str]]) -> List[Any]:
        """Run SkillExtractor on the constructed triplets.

        Converts simple dict triplets to Triplet objects expected by
        SkillExtractor.
        """
        if not triplets:
            return []

        try:
            from claw_mem.extraction.openie_extractor import Triplet
            from claw_mem.extraction.skill_extractor import SkillExtractor

            # Convert dict triplets to Triplet objects
            triplet_objs = [
                Triplet(subject=t["s"], predicate=t["p"], object=t["o"], confidence=0.7)
                for t in triplets
            ]

            extractor = SkillExtractor(llm_provider=self._llm, mode="rule")
            return extractor.extract(triplet_objs)
        except Exception:
            return []

    # ── topic summaries ────────────────────────────────────────────

    def _build_topic_summaries(self, candidates: List[ScoredCandidate]) -> Dict[str, str]:
        """Group candidates by tags and build concise topic summaries."""
        topic_groups: Dict[str, List[str]] = defaultdict(list)

        for c in candidates:
            tags = c.signal.tags if c.signal.tags else ["general"]
            for tag in tags:
                topic_groups[tag].append(c.signal.content)

        summaries: Dict[str, str] = {}
        for tag, contents in topic_groups.items():
            if len(contents) == 1:
                summaries[tag] = contents[0][:100]
            else:
                # Concatenate first few items
                preview = " | ".join(c[:60] for c in contents[:5])
                suffix = f" ... (+{len(contents) - 5} more)" if len(contents) > 5 else ""
                summaries[tag] = f"[{len(contents)} items] {preview}{suffix}"

        return summaries
