"""Tests for Skill + SkillExtractor (F1 · v4.11.0)."""

import json
import time
from unittest.mock import MagicMock

import pytest

from claw_mem.extraction.openie_extractor import Triplet
from claw_mem.extraction.skill_extractor import Skill, SkillExtractor


# ── helpers ───────────────────────────────────────────────────────────

class _MockLLM:
    """Returns a preset JSON response."""

    def __init__(self, response: str = ""):
        self._response = response
        self.calls: list = []

    def generate(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        self.calls.append((prompt, system, max_tokens))
        return self._response

    def health_check(self) -> bool:
        return True


class _FailingLLM:
    """Always raises an exception."""

    def generate(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        raise RuntimeError("LLM unavailable")

    def health_check(self) -> bool:
        return False


def _make_triplets(*pairs) -> list:
    """Helper: create triplets from (subject, predicate, object) tuples."""
    return [
        Triplet(subject=s, predicate=p, object=o, confidence=0.8, source="rule")
        for s, p, o in pairs
    ]


# ── Skill dataclass ───────────────────────────────────────────────────

class TestSkill:
    def test_basic_skill(self):
        s = Skill(
            name="资源管理",
            steps=["识别资源", "分配优先级"],
            applicability="当需要管理资源时",
            confidence=0.85,
            compression_ratio=3.0,
            source_triplets=3,
            source="rule",
        )
        assert s.name == "资源管理"
        assert len(s.steps) == 2
        assert s.confidence == 0.85
        assert s.compression_ratio == 3.0
        assert s.source_triplets == 3
        assert s.source == "rule"

    def test_default_values(self):
        s = Skill(name="test")
        assert s.steps == []
        assert s.applicability == ""
        assert s.confidence == 0.5
        assert s.compression_ratio == 1.0
        assert s.source_triplets == 0
        assert s.source == "rule"

    def test_created_at_default(self):
        s = Skill(name="test")
        assert s.created_at == 0.0

    def test_repr(self):
        s = Skill(name="管理能力", confidence=0.85, compression_ratio=3.0, source="llm")
        r = repr(s)
        assert "管理能力" in r
        assert "0.85" in r
        assert "3.0x" in r
        assert "llm" in r


# ── SkillExtractor - rule mode ────────────────────────────────────────

class TestSkillExtractorRule:
    def test_empty_triplets(self):
        e = SkillExtractor(mode="rule")
        assert e.extract([]) == []

    def test_single_triplet_no_skill(self):
        """A single triplet does not meet MIN_GROUP_SIZE=2 threshold."""
        triplets = _make_triplets(("Alice", "manages", "team"))
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert skills == []

    def test_two_same_pattern_becomes_skill(self):
        triplets = _make_triplets(
            ("张三", "负责", "电商项目"),
            ("张三", "负责", "数据分析"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert len(skills) == 1
        assert skills[0].source == "rule"
        assert skills[0].source_triplets == 2
        assert skills[0].compression_ratio == 2.0

    def test_confidence_scales_with_group_size(self):
        triplets = _make_triplets(
            ("张三", "负责", "项目A"),
            ("张三", "负责", "项目B"),
        )
        e = SkillExtractor(mode="rule")
        s1 = e.extract(triplets)[0]

        triplets2 = _make_triplets(
            ("张三", "负责", "A"),
            ("张三", "负责", "B"),
            ("张三", "负责", "C"),
            ("张三", "负责", "D"),
            ("张三", "负责", "E"),
        )
        s2 = e.extract(triplets2)[0]

        assert s2.confidence > s1.confidence

    def test_knowledge_predicate_template(self):
        triplets = _make_triplets(
            ("Alice", "manages", "team"),
            ("Alice", "manages", "project"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert len(skills) >= 1

    def test_multiple_groups(self):
        triplets = _make_triplets(
            ("张三", "负责", "项目A"),
            ("张三", "负责", "项目B"),
            ("李四", "开发", "后端"),
            ("李四", "开发", "前端"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert len(skills) == 2

    def test_group_by_subject_predicate(self):
        """Different subjects with same predicate form different groups."""
        triplets = _make_triplets(
            ("张三", "负责", "A"),
            ("李四", "负责", "B"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        # Both are single triplets, so no skills
        assert skills == []

    def test_mixed_english_chinese(self):
        triplets = _make_triplets(
            ("Alice", "has", "book"),
            ("Alice", "has", "pen"),
            ("张三", "负责", "项目A"),
            ("张三", "负责", "项目B"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert len(skills) == 2

    def test_generic_template_for_unknown_predicate(self):
        triplets = _make_triplets(
            ("X", "custom_rel", "A"),
            ("X", "custom_rel", "B"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert len(skills) == 1
        assert skills[0].source == "rule"
        assert skills[0].source_triplets == 2

    def test_mode_property(self):
        e = SkillExtractor(mode="rule")
        assert e.mode == "rule"


# ── SkillExtractor - LLM mode ─────────────────────────────────────────

class TestSkillExtractorLLM:
    def test_llm_extraction_success(self):
        response = json.dumps([
            {
                "name": "Resource Management",
                "steps": ["Step 1", "Step 2"],
                "applicability": "When managing resources",
                "confidence": 0.9,
            }
        ])
        llm = _MockLLM(response=response)
        e = SkillExtractor(llm_provider=llm, mode="llm")
        triplets = _make_triplets(
            ("Alice", "manages", "team"),
            ("Alice", "manages", "project"),
        )
        skills = e.extract(triplets)
        assert len(skills) == 1
        assert skills[0].name == "Resource Management"
        assert skills[0].source == "llm"
        assert skills[0].confidence == 0.9
        assert skills[0].source_triplets == 2

    def test_llm_with_markdown_fences(self):
        response = '```json\n[{"name":"Test","steps":["Do"],"applicability":"Always","confidence":0.8}]\n```'
        llm = _MockLLM(response=response)
        e = SkillExtractor(llm_provider=llm, mode="llm")
        triplets = _make_triplets(
            ("X", "test", "Y"),
            ("X", "test", "Z"),
        )
        skills = e.extract(triplets)
        assert len(skills) == 1
        assert skills[0].name == "Test"

    def test_llm_no_provider(self):
        e = SkillExtractor(llm_provider=None, mode="llm")
        triplets = _make_triplets(
            ("A", "B", "C"),
            ("A", "B", "D"),
        )
        skills = e.extract(triplets)
        assert skills == []

    def test_llm_handles_exception_gracefully(self):
        llm = _FailingLLM()
        e = SkillExtractor(llm_provider=llm, mode="llm")
        triplets = _make_triplets(
            ("A", "B", "C"),
            ("A", "B", "D"),
        )
        skills = e.extract(triplets)
        assert skills == []

    def test_llm_empty_response(self):
        llm = _MockLLM(response="")
        e = SkillExtractor(llm_provider=llm, mode="llm")
        triplets = _make_triplets(
            ("A", "B", "C"),
            ("A", "B", "D"),
        )
        skills = e.extract(triplets)
        assert skills == []

    def test_llm_invalid_json(self):
        llm = _MockLLM(response="not json at all")
        e = SkillExtractor(llm_provider=llm, mode="llm")
        triplets = _make_triplets(
            ("A", "B", "C"),
            ("A", "B", "D"),
        )
        skills = e.extract(triplets)
        assert skills == []


# ── SkillExtractor - auto mode ────────────────────────────────────────

class TestSkillExtractorAuto:
    def test_auto_uses_llm_when_available(self):
        response = json.dumps([
            {
                "name": "Test Skill",
                "steps": ["Step 1"],
                "applicability": "Always",
                "confidence": 0.9,
            }
        ])
        llm = _MockLLM(response=response)
        e = SkillExtractor(llm_provider=llm, mode="auto")
        triplets = _make_triplets(
            ("A", "B", "C"),
            ("A", "B", "D"),
        )
        skills = e.extract(triplets)
        assert len(skills) == 1
        assert skills[0].source == "llm"

    def test_auto_falls_back_to_rule_when_llm_fails(self):
        llm = _FailingLLM()
        e = SkillExtractor(llm_provider=llm, mode="auto")
        triplets = _make_triplets(
            ("张三", "负责", "项目A"),
            ("张三", "负责", "项目B"),
        )
        skills = e.extract(triplets)
        assert len(skills) >= 1
        assert all(s.source == "rule" for s in skills)

    def test_auto_falls_back_when_llm_returns_empty(self):
        llm = _MockLLM(response="")
        e = SkillExtractor(llm_provider=llm, mode="auto")
        triplets = _make_triplets(
            ("张三", "负责", "A"),
            ("张三", "负责", "B"),
        )
        skills = e.extract(triplets)
        assert len(skills) >= 1
        assert all(s.source == "rule" for s in skills)

    def test_auto_no_llm_uses_rule(self):
        e = SkillExtractor(llm_provider=None, mode="auto")
        triplets = _make_triplets(
            ("张三", "负责", "项目A"),
            ("张三", "负责", "项目B"),
        )
        skills = e.extract(triplets)
        assert len(skills) >= 1
        assert all(s.source == "rule" for s in skills)

    def test_invalid_mode_defaults_to_auto(self):
        e = SkillExtractor(mode="invalid")
        assert e.mode == "auto"


# ── SkillExtractor - compression ratio ───────────────────────────────

class TestCompressionRatio:
    def test_ratio_equals_source_triplets(self):
        triplets = _make_triplets(
            ("A", "B", "C1"),
            ("A", "B", "C2"),
            ("A", "B", "C3"),
        )
        e = SkillExtractor(mode="rule")
        skills = e.extract(triplets)
        assert len(skills) == 1
        assert skills[0].compression_ratio == 3.0
        assert skills[0].source_triplets == 3

    def test_ratio_for_single_llm_skill(self):
        response = json.dumps([
            {"name": "T", "steps": ["S"], "applicability": "A", "confidence": 0.8}
        ])
        llm = _MockLLM(response=response)
        e = SkillExtractor(llm_provider=llm, mode="llm")
        triplets = _make_triplets(
            ("A", "B", "C1"),
            ("A", "B", "C2"),
        )
        skills = e.extract(triplets)
        assert skills[0].compression_ratio == 2.0


# ── SkillExtractor - parse_skill_json edge cases ──────────────────────

class TestParseSkillJson:
    def test_plain_json_array(self):
        raw = '[{"name":"S","steps":[],"applicability":"","confidence":0.5}]'
        result = SkillExtractor._parse_skill_json(raw)
        assert len(result) == 1
        assert result[0]["name"] == "S"

    def test_empty_string(self):
        assert SkillExtractor._parse_skill_json("") == []
        assert SkillExtractor._parse_skill_json("   ") == []

    def test_non_list_json(self):
        assert SkillExtractor._parse_skill_json('{"name":"S"}') == []

    def test_broken_json_with_array(self):
        raw = 'some text [{"name":"S","steps":[]}] trailing'
        result = SkillExtractor._parse_skill_json(raw)
        assert len(result) == 1
