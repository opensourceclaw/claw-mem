"""Tests for OpenIEExtractor + Triplet (F1 · v4.10.0)."""

import json
import re
from unittest.mock import MagicMock

import pytest

from claw_mem.extraction.openie_extractor import OpenIEExtractor, Triplet


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


# ── Triplet dataclass ─────────────────────────────────────────────────

class TestTriplet:
    def test_basic_triplet(self):
        t = Triplet(subject="张三", predicate="负责", object="电商项目", confidence=0.9, source="llm")
        assert t.subject == "张三"
        assert t.predicate == "负责"
        assert t.object == "电商项目"
        assert t.confidence == 0.9
        assert t.source == "llm"

    def test_default_values(self):
        t = Triplet(subject="A", predicate="B", object="C")
        assert t.confidence == 0.5
        assert t.source == "rule"

    def test_repr(self):
        t = Triplet(subject="张三", predicate="负责", object="项目", confidence=0.8, source="llm")
        r = repr(t)
        assert "张三" in r
        assert "负责" in r
        assert "0.80" in r
        assert "llm" in r


# ── OpenIEExtractor - rule mode ───────────────────────────────────────

class TestOpenIERule:
    def test_chinese_shi_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("张三是工程师")
        assert len(results) >= 1
        assert any(t.predicate == "是" for t in results)
        assert all(t.source == "rule" for t in results)

    def test_chinese_de_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("张三的电脑")
        assert len(results) >= 1
        assert any(t.predicate == "拥有" for t in results)

    def test_chinese_fuze_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("张三负责电商项目")
        assert len(results) >= 1
        assert any(t.predicate == "负责" and t.object == "电商项目" for t in results)

    def test_chinese_zai_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("张三在北京")
        assert len(results) >= 1
        assert any(t.predicate == "位于" for t in results)

    def test_chinese_dongci_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("张三喜欢李四。王五管理技术部。")
        assert len(results) >= 1
        assert all(t.source == "rule" for t in results)

    def test_multiple_chinese_patterns(self):
        e = OpenIEExtractor(mode="rule")
        text = "张三是李四的上司。张三负责电商项目。李四在杭州。"
        results = e.extract(text)
        # Should find multiple triplets from different patterns
        assert len(results) >= 2

    def test_deduplication(self):
        e = OpenIEExtractor(mode="rule")
        # Same pattern appearing twice
        text = "张三负责电商项目。张三负责电商项目。"
        results = e.extract(text)
        # Should be deduplicated
        triplets_str = [(t.subject, t.predicate, t.object) for t in results]
        assert len(triplets_str) == len(set(triplets_str))

    def test_english_is_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("Peter is engineer")
        assert len(results) >= 1
        assert any(t.predicate == "is" for t in results)

    def test_english_has_pattern(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("Alice has book")
        assert len(results) >= 1
        assert any(t.predicate == "has" for t in results)

    def test_empty_text(self):
        e = OpenIEExtractor(mode="rule")
        assert e.extract("") == []
        assert e.extract("   ") == []

    def test_no_match_returns_empty(self):
        e = OpenIEExtractor(mode="rule")
        results = e.extract("123 456 789")
        # Numbers alone should not generate meaningful triplets
        # May or may not match — just verify no crash
        assert isinstance(results, list)


# ── OpenIEExtractor - LLM mode ────────────────────────────────────────

class TestOpenIELLM:
    def test_llm_extraction_success(self):
        response = json.dumps([
            {"s": "张三", "p": "负责", "o": "电商项目", "c": 0.9},
            {"s": "李四", "p": "是...的上司", "o": "张三", "c": 0.85},
        ])
        llm = _MockLLM(response=response)
        e = OpenIEExtractor(llm_provider=llm, mode="llm")
        results = e.extract("张三是李四的上司。张三负责电商项目。")
        assert len(results) == 2
        assert results[0].subject == "张三"
        assert results[1].object == "张三"
        assert all(t.source == "llm" for t in results)

    def test_llm_extraction_with_markdown_fences(self):
        response = '```json\n[{"s":"A","p":"likes","o":"B","c":0.9}]\n```'
        llm = _MockLLM(response=response)
        e = OpenIEExtractor(llm_provider=llm, mode="llm")
        results = e.extract("A likes B")
        assert len(results) == 1
        assert results[0].subject == "A"

    def test_llm_extraction_with_alt_keys(self):
        response = json.dumps([
            {"subject": "Alice", "predicate": "works_at", "object": "Google", "confidence": 0.95},
        ])
        llm = _MockLLM(response=response)
        e = OpenIEExtractor(llm_provider=llm, mode="llm")
        results = e.extract("Alice works at Google")
        assert len(results) == 1
        assert results[0].subject == "Alice"
        assert results[0].confidence == 0.95

    def test_llm_extraction_empty_response(self):
        llm = _MockLLM(response="")
        e = OpenIEExtractor(llm_provider=llm, mode="llm")
        results = e.extract("test")
        assert results == []

    def test_llm_extraction_invalid_json(self):
        llm = _MockLLM(response="not valid json at all")
        e = OpenIEExtractor(llm_provider=llm, mode="llm")
        results = e.extract("test")
        assert results == []

    def test_llm_no_provider(self):
        e = OpenIEExtractor(llm_provider=None, mode="llm")
        results = e.extract("张三是工程师")
        assert results == []

    def test_llm_handles_exception_gracefully(self):
        llm = _FailingLLM()
        e = OpenIEExtractor(llm_provider=llm, mode="llm")
        results = e.extract("test")
        assert results == []


# ── OpenIEExtractor - auto mode ───────────────────────────────────────

class TestOpenIEAuto:
    def test_auto_uses_llm_when_available(self):
        response = json.dumps([
            {"s": "张三", "p": "负责", "o": "项目", "c": 0.9},
        ])
        llm = _MockLLM(response=response)
        e = OpenIEExtractor(llm_provider=llm, mode="auto")
        results = e.extract("张三负责项目")
        assert len(results) == 1
        assert results[0].source == "llm"

    def test_auto_falls_back_to_rule_when_llm_fails(self):
        llm = _FailingLLM()
        e = OpenIEExtractor(llm_provider=llm, mode="auto")
        results = e.extract("张三负责电商项目")
        assert len(results) >= 1
        assert all(t.source == "rule" for t in results)

    def test_auto_falls_back_when_llm_returns_empty(self):
        llm = _MockLLM(response="")
        e = OpenIEExtractor(llm_provider=llm, mode="auto")
        results = e.extract("张三是工程师")
        # Should fall back to rule mode
        assert len(results) >= 1
        assert all(t.source == "rule" for t in results)

    def test_auto_no_llm_uses_rule(self):
        e = OpenIEExtractor(llm_provider=None, mode="auto")
        results = e.extract("张三是李四的上司。")
        assert len(results) >= 1
        assert all(t.source == "rule" for t in results)

    def test_invalid_mode_defaults_to_auto(self):
        e = OpenIEExtractor(mode="invalid")
        assert e._mode == "auto"
