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
claw-mem Skill Extraction (L2 | v4.11.0)

Abstracts OpenIE triplets into reusable operational patterns (skills).
Implements arXiv:2604.15877 Experience Compression Spectrum Level 2.

Supports three extraction modes:
  - "llm":  LLM-powered pattern abstraction
  - "rule": Frequency-based clustering (no LLM needed)
  - "auto": Try LLM first, fall back to rule (default)
"""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List

_LLM_SYSTEM_PROMPT = (
    "You are a skill extraction engine. Given a group of related knowledge "
    "triplets (all sharing the same subject-predicate pattern), abstract "
    "them into a reusable skill.\n\n"
    "Output a JSON array of skill objects. Each skill must have:\n"
    '  - "name": short skill name (3-8 words)\n'
    '  - "steps": list of actionable step descriptions (2-5 steps)\n'
    '  - "applicability": when to apply this skill (1 sentence)\n'
    '  - "confidence": float 0-1 indicating extraction confidence\n\n'
    "Example input triplets:\n"
    "  (Alice, manages, team), (Alice, manages, project), "
    "(Alice, manages, budget)\n\n"
    "Example output:\n"
    '[{"name":"Resource Management",'
    '"steps":["Identify resources","Assign priorities","Track progress",'
    '"Adjust allocations"],'
    '"applicability":"When managing teams, projects, or budgets",'
    '"confidence":0.85}]\n\n'
    "Only output valid JSON. Do not include markdown fences or commentary."
)


@dataclass
class Skill:
    """A reusable operational pattern abstracted from knowledge triplets.

    Attributes:
        name: Skill name.
        steps: Actionable step descriptions.
        applicability: Description of when this skill applies.
        confidence: Extraction confidence (0.0-1.0).
        compression_ratio: Source triplet count / 1
            (how many triplets this skill compresses).
        source_triplets: Number of source triplets used to generate this skill.
        created_at: Unix timestamp when created.
        source: Extraction source ("llm" or "rule").
    """

    name: str
    steps: List[str] = field(default_factory=list)
    applicability: str = ""
    confidence: float = 0.5
    compression_ratio: float = 1.0
    source_triplets: int = 0
    created_at: float = 0.0
    source: str = "rule"

    def __repr__(self) -> str:
        return (
            f"Skill({self.name!r}, steps={len(self.steps)},"
            f" c={self.confidence:.2f}, ratio={self.compression_ratio:.1f}x,"
            f" src={self.source})"
        )


# ── Rule-mode templates ──────────────────────────────────────────────

_RULE_SKILL_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "管理": {
        "name": "管理能力",
        "steps": ["明确管理目标", "制定管理计划", "执行并监督", "评估结果"],
        "applicability": "当需要管理、监督或协调资源时",
    },
    "负责": {
        "name": "责任制工作",
        "steps": ["确认责任范围", "规划执行路径", "推进交付", "汇报进展"],
        "applicability": "当需要明确责任分工和推进任务时",
    },
    "开发": {
        "name": "软件开发",
        "steps": ["理解需求", "设计方案", "编码实现", "测试验证"],
        "applicability": "当涉及软件开发或技术实现时",
    },
    "拥有": {
        "name": "资源持有",
        "steps": ["确认资源所有权", "管理资源生命周期", "评估资源价值"],
        "applicability": "当涉及资源所有权或资产管理时",
    },
    "is": {
        "name": "Identity Classification",
        "steps": [
            "Identify the entity",
            "Determine its category",
            "Apply categorization rules",
        ],
        "applicability": "When classifying or categorizing entities",
    },
    "has": {
        "name": "Possession Pattern",
        "steps": [
            "Identify the owner",
            "Catalog possessions",
            "Track changes over time",
        ],
        "applicability": "When tracking ownership or possession relationships",
    },
    "likes": {
        "name": "Preference Understanding",
        "steps": [
            "Identify the subject",
            "Note the preference",
            "Apply in recommendations",
        ],
        "applicability": "When understanding user preferences or likes",
    },
    "works_at": {
        "name": "Employment Relationship",
        "steps": ["Identify employee", "Note the organization", "Track role changes"],
        "applicability": "When managing employment or organizational relationships",
    },
}

_GENERIC_RULE_TEMPLATE = {
    "name": "通用模式",
    "steps": ["分析输入信息", "识别关键模式", "应用模式规则", "总结输出"],
    "applicability": "当出现重复模式时",
}


class SkillExtractor:
    """Extract reusable skills from knowledge triplets (L2 compression).

    Modes:
        "llm":  Uses LLMProvider to abstract triplets into skills.
        "rule": Uses frequency-based clustering without external dependencies.
        "auto": Tries LLM first, falls back to rule on failure (default).

    Usage::

        from claw_mem.extraction import Triplet, SkillExtractor
        extractor = SkillExtractor()
        triplets = [Triplet("Alice", "manages", "team", 0.9),
                     Triplet("Alice", "manages", "project", 0.85)]
        skills = extractor.extract(triplets)
    """

    _MIN_GROUP_SIZE = 2

    def __init__(self, llm_provider=None, mode: str = "auto"):
        self._llm = llm_provider
        self._mode = mode if mode in ("llm", "rule", "auto") else "auto"

    @property
    def mode(self) -> str:
        """Current extraction mode."""
        return self._mode

    # ── public API ─────────────────────────────────────────────────

    def extract(self, triplets: List) -> List[Skill]:
        """Extract skills from a list of triplets.

        Args:
            triplets: List of Triplet objects (from OpenIEExtractor).

        Returns:
            List of Skill objects. Empty list if input is empty or no
            groups meet the minimum size threshold.
        """
        if not triplets:
            return []

        # 1. Group by (subject, predicate)
        groups = self._group_triplets(triplets)

        # 2. Filter: only groups with >= MIN_GROUP_SIZE triplets
        valid_groups = {
            k: v for k, v in groups.items() if len(v) >= self._MIN_GROUP_SIZE
        }

        if not valid_groups:
            return []

        # 3. Extract skills based on mode
        if self._mode == "llm":
            skills = self._extract_llm(valid_groups)
        elif self._mode == "rule":
            skills = self._extract_rule(valid_groups)
        else:  # auto
            skills = self._extract_auto(valid_groups)

        # 4. Calculate compression ratios
        for skill in skills:
            if skill.source_triplets > 0:
                skill.compression_ratio = skill.source_triplets / 1.0

        return skills

    # ── grouping ───────────────────────────────────────────────────

    @staticmethod
    def _group_triplets(triplets: List) -> Dict[str, List]:
        """Group triplets by (subject, predicate) key."""
        groups: Dict[str, List] = defaultdict(list)
        for t in triplets:
            key = f"{t.subject}|{t.predicate}"
            groups[key].append(t)
        return dict(groups)

    # ── rule mode ──────────────────────────────────────────────────

    def _extract_rule(self, groups: Dict[str, List]) -> List[Skill]:
        """Frequency-clustering based skill extraction (no LLM needed)."""
        skills: List[Skill] = []

        for key, group in groups.items():
            subject, predicate = key.split("|", 1)
            count = len(group)

            # Look up template for this predicate
            if predicate in _RULE_SKILL_TEMPLATES:
                template = _RULE_SKILL_TEMPLATES[predicate]
            else:
                template = dict(_GENERIC_RULE_TEMPLATE)
                template["name"] = f"{subject}-{predicate} 模式"

            # Confidence scales with group size (saturates at ~0.9)
            confidence = min(0.5 + 0.1 * (count - 2), 0.9)
            # Round to 2 decimal places
            confidence = round(confidence, 2)

            skill = Skill(
                name=template["name"],
                steps=list(template["steps"]),
                applicability=template["applicability"],
                confidence=confidence,
                source_triplets=count,
                created_at=time.time(),
                source="rule",
            )
            skills.append(skill)

        return skills

    # ── LLM mode ───────────────────────────────────────────────────

    def _extract_llm(self, groups: Dict[str, List]) -> List[Skill]:
        """LLM-powered skill abstraction."""
        if self._llm is None:
            return []

        all_skills: List[Skill] = []

        for key, group in groups.items():
            subject, predicate = key.split("|", 1)
            count = len(group)

            # Build prompt with the group's triplets
            prompt_lines = [f"Group: {subject} -{predicate}-> ... ({count} instances)"]
            for t in group:
                prompt_lines.append(f"  ({t.subject}, {t.predicate}, {t.object})")
            prompt = "\n".join(prompt_lines)

            try:
                raw = self._llm.generate(prompt, _LLM_SYSTEM_PROMPT, max_tokens=512)
                parsed = self._parse_skill_json(raw)
                for item in parsed:
                    skill = Skill(
                        name=item.get("name", f"{subject}-{predicate}"),
                        steps=item.get("steps", []),
                        applicability=item.get("applicability", ""),
                        confidence=float(item.get("confidence", 0.7)),
                        source_triplets=count,
                        created_at=time.time(),
                        source="llm",
                    )
                    all_skills.append(skill)
            except Exception:
                continue

        return all_skills

    @staticmethod
    def _parse_skill_json(raw: str) -> List[Dict[str, Any]]:
        """Parse LLM response, handling markdown fences and edge cases."""
        if not raw or not raw.strip():
            return []

        text = raw.strip()

        # Remove markdown code fences if present
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()

        # Try direct parse
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            pass

        # Try to find JSON array in the text
        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if array_match:
            try:
                result = json.loads(array_match.group(0))
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass

        return []

    # ── auto mode ──────────────────────────────────────────────────

    def _extract_auto(self, groups: Dict[str, List]) -> List[Skill]:
        """Try LLM first, fall back to rule on any failure."""
        if self._llm is not None:
            try:
                skills = self._extract_llm(groups)
                if skills:
                    return skills
            except Exception:
                pass

        return self._extract_rule(groups)
