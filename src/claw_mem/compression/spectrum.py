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
CompressionSpectrum - Four-tier memory compression (v2.15.0).

Tiered abstraction:
  L0 Episodes → L1 Skills → L2 Rules → L3 Principles

Trigger-based (not continuous): activated by access/apply/verify counts.
Rule-based extraction (no LLM dependency in MVP).
Default: disabled (enable_compression=False).
"""

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SkillEntry:
    skill_id: str
    title: str
    description: str = ""
    steps: List[str] = field(default_factory=list)
    source_episodes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    apply_count: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0


@dataclass
class RuleEntry:
    rule_id: str
    condition: str
    action: str
    confidence: float = 0.7
    source_skills: List[str] = field(default_factory=list)
    validation_count: int = 0
    created_at: float = 0.0


@dataclass
class PrincipleEntry:
    principle_id: str
    content: str
    confidence: float = 0.5
    source_rules: List[str] = field(default_factory=list)
    created_at: float = 0.0


@dataclass
class CompressedMemory:
    memory_id: str
    level: int
    content: str
    source_ids: List[str] = field(default_factory=list)
    created_at: float = 0.0
    metadata: Dict = field(default_factory=dict)


class CompressionSpectrum:
    """Four-tier compression spectrum (Episodes→Skills→Rules→Principles).

    Complements existing MemoryCompressorV2 and F5CompressorV2.
    """

    def __init__(self, memory_manager=None,
                 access_threshold: int = 5,
                 apply_threshold: int = 3,
                 verify_threshold: int = 2):
        self._mm = memory_manager
        self._skills: Dict[str, SkillEntry] = {}
        self._rules: Dict[str, RuleEntry] = {}
        self._principles: Dict[str, PrincipleEntry] = {}
        self._episode_access: Dict[str, int] = {}

        self._skill_access_threshold = access_threshold
        self._rule_apply_threshold = apply_threshold
        self._principle_verify_threshold = verify_threshold

    # ── Trigger ──────────────────────────────────────────────

    def record_access(self, memory_id: str) -> Optional[CompressedMemory]:
        self._episode_access[memory_id] = (
            self._episode_access.get(memory_id, 0) + 1
        )
        count = self._episode_access[memory_id]
        if count >= self._skill_access_threshold:
            return self._compress_to_skill(memory_id)
        return None

    def record_apply(self, skill_id: str) -> Optional[CompressedMemory]:
        skill = self._skills.get(skill_id)
        if skill is None:
            return None
        skill.apply_count += 1
        if skill.apply_count >= self._rule_apply_threshold:
            return self._compress_to_rule(skill_id)
        return None

    def record_verify(self, rule_id: str) -> Optional[CompressedMemory]:
        rule = self._rules.get(rule_id)
        if rule is None:
            return None
        rule.validation_count += 1
        if rule.validation_count >= self._principle_verify_threshold:
            return self._compress_to_principle(rule_id)
        return None

    # ── Compression ──────────────────────────────────────────

    def _compress_to_skill(self, episode_id: str) -> Optional[CompressedMemory]:
        content = self._get_episode_content(episode_id)
        if not content:
            return None

        steps = self._extract_steps(content)
        if len(steps) < 2:
            return None

        title = content.split('\n')[0].strip()[:80]
        tags = self._extract_tags(content)

        skill_id = f"skill_{uuid.uuid4().hex[:12]}"
        skill = SkillEntry(
            skill_id=skill_id, title=title,
            description=content[:200], steps=steps,
            source_episodes=[episode_id], tags=tags,
            apply_count=0, created_at=time.time(),
            updated_at=time.time(),
        )
        self._skills[skill_id] = skill

        body = "[Skill] " + title + "\n" + "\n".join(
            f"  {i+1}. {s}" for i, s in enumerate(steps)
        )
        # Sync to Engram
        self._sync_to_engram(skill_id, body)

        return CompressedMemory(
            memory_id=skill_id, level=1, content=body,
            source_ids=[episode_id], created_at=time.time(),
            metadata={"type": "skill", "tags": tags},
        )

    def _compress_to_rule(self, skill_id: str) -> Optional[CompressedMemory]:
        skill = self._skills.get(skill_id)
        if skill is None:
            return None

        condition = f"User needs {skill.title}"
        action = " → ".join(skill.steps[:3])

        rule_id = f"rule_{uuid.uuid4().hex[:12]}"
        rule = RuleEntry(
            rule_id=rule_id, condition=condition, action=action,
            confidence=0.7, source_skills=[skill_id],
            validation_count=0, created_at=time.time(),
        )
        self._rules[rule_id] = rule

        rule_body = f"[Rule] IF {condition} THEN {action}"
        self._sync_to_engram(rule_id, rule_body)

        return CompressedMemory(
            memory_id=rule_id, level=2,
            content=f"[Rule] IF {condition} THEN {action}",
            source_ids=[skill_id], created_at=time.time(),
            metadata={"type": "rule", "confidence": 0.7},
        )

    def _compress_to_principle(self, rule_id: str) -> Optional[CompressedMemory]:
        rule = self._rules.get(rule_id)
        if rule is None:
            return None

        content = f"Prioritize: {rule.action[:100]}"
        principle_id = f"prin_{uuid.uuid4().hex[:12]}"
        principle = PrincipleEntry(
            principle_id=principle_id, content=content,
            confidence=rule.confidence, source_rules=[rule_id],
            created_at=time.time(),
        )
        self._principles[principle_id] = principle

        principle_body = f"[Principle] {content}"
        self._sync_to_engram(principle_id, principle_body)

        return CompressedMemory(
            memory_id=principle_id, level=3,
            content=principle_body,
            source_ids=[rule_id], created_at=time.time(),
            metadata={"type": "principle", "confidence": rule.confidence},
        )

    # ── Engram Sync ──────────────────────────────────────────

    def _sync_to_engram(self, memory_id: str, content: str) -> None:
        """Sync compressed memory to Engram index (non-blocking)."""
        if self._mm and hasattr(self._mm, 'engram') and self._mm.engram:
            try:
                self._mm.engram.index(memory_id, content)
            except Exception:
                pass

    # ── Runtime config ───────────────────────────────────────

    def configure_thresholds(self, access: int = None,
                             apply: int = None,
                             verify: int = None) -> None:
        """Runtime threshold configuration."""
        if access is not None:
            self._skill_access_threshold = access
        if apply is not None:
            self._rule_apply_threshold = apply
        if verify is not None:
            self._principle_verify_threshold = verify

    # ── Query ────────────────────────────────────────────────

    def get_compressed(self, memory_id: str = None,
                       level: int = None) -> List[CompressedMemory]:
        results: List[CompressedMemory] = []
        for skill in self._skills.values():
            if memory_id and memory_id not in skill.source_episodes:
                continue
            results.append(CompressedMemory(
                memory_id=skill.skill_id, level=1,
                content=f"[Skill] {skill.title}",
                source_ids=skill.source_episodes,
                created_at=skill.created_at,
                metadata={"type": "skill"},
            ))
        return results

    # ── Helpers ──────────────────────────────────────────────

    def _get_episode_content(self, memory_id: str) -> Optional[str]:
        if self._mm is None:
            return None
        try:
            r = self._mm.get(memory_id)
            return r.get("content") if r else None
        except Exception:
            return None

    def _extract_steps(self, content: str) -> List[str]:
        patterns = [
            r'(?:install|pip install|npm install|brew install)\s+\S+',
            r'(?:配置|设置|修改|创建|使用|运行|启动|停止|删除)\s+\S+',
            r'(?:create|configure|set up|run|start|stop|delete)\s+\S+',
        ]
        steps = []
        for p in patterns:
            steps.extend(re.findall(p, content, re.IGNORECASE))
        seen = set()
        unique = []
        for s in steps:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique.append(s)
        return unique[:10]

    def _extract_tags(self, content: str) -> List[str]:
        keywords = [
            'python', 'javascript', 'typescript', 'go', 'rust',
            'redis', 'postgresql', 'mysql', 'mongodb',
            'docker', 'kubernetes', 'aws', 'api', 'rest',
        ]
        lower = content.lower()
        return [k for k in keywords if k in lower][:5]

    # ── Stats ────────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "skills": len(self._skills),
            "rules": len(self._rules),
            "principles": len(self._principles),
            "total_episodes_tracked": len(self._episode_access),
            "thresholds": {
                "skill_access": self._skill_access_threshold,
                "rule_apply": self._rule_apply_threshold,
                "principle_verify": self._principle_verify_threshold,
            },
            "enabled": True,
        }
