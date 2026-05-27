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

"""Tests for QueryReconstructor (F1, v4.8.0)."""

import pytest
from claw_mem.retrieval.query_reconstructor import QueryReconstructor, _clean_line


# ── Mock LLMProvider ──────────────────────────────────────────────────

class _MockLLM:
    """Mock LLM that returns canned responses based on prompt content."""

    def __init__(self, step_back: str = "", variants: str = ""):
        self.step_back = step_back
        self.variants = variants
        self.calls: list = []

    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        self.calls.append({"prompt": prompt, "system": system})
        if "broader search query" in prompt or "broader" in prompt:
            return self.step_back
        if "different ways to phrase" in prompt or "semantically equivalent" in prompt:
            return self.variants
        return ""


class _FailingLLM:
    """Mock LLM that always returns empty string (simulates offline)."""

    def generate(self, prompt: str, system: str = "", max_tokens: int = 256) -> str:
        return ""


# ── Constructor tests ──────────────────────────────────────────────────

class TestQueryReconstructorInit:
    def test_default_constructor(self):
        qr = QueryReconstructor()
        assert qr._llm is None
        assert qr._enable_cache is True
        assert qr._cache == {}

    def test_with_llm_provider(self):
        llm = _MockLLM()
        qr = QueryReconstructor(llm_provider=llm)
        assert qr._llm is llm

    def test_disable_cache(self):
        qr = QueryReconstructor(enable_cache=False)
        assert qr._enable_cache is False


# ── LLM-based reconstruction ───────────────────────────────────────────

class TestLLMReconstruction:
    def test_reconstruct_with_llm(self):
        llm = _MockLLM(
            step_back="JWT token authentication issues",
            variants="JWT 身份验证问题\nJWT 认证错误修复",
        )
        qr = QueryReconstructor(llm_provider=llm)
        results = qr.reconstruct("上次那个 JWT token 的问题怎么解决的")
        assert results[0] == "上次那个 JWT token 的问题怎么解决的"
        assert "JWT token authentication issues" in results
        assert "JWT 身份验证问题" in results
        assert "JWT 认证错误修复" in results

    def test_reconstruct_deduplicates_same_case(self):
        """Variants that match the original query (case-insensitive) are skipped."""
        llm = _MockLLM(
            step_back="JWT issues",
            variants="JWT issues\nAnother variant",
        )
        qr = QueryReconstructor(llm_provider=llm)
        results = qr.reconstruct("jwt issues")
        # "JWT issues" should appear only once
        count = sum(1 for r in results if r.lower() == "jwt issues")
        assert count == 1, f"Expected 1 occurrence, got {count}: {results}"
        assert "Another variant" in results

    def test_reconstruct_deduplicates_across_phases(self):
        """If step-back equals a variant, deduplicate."""
        llm = _MockLLM(
            step_back="general query",
            variants="general query\nanother one",
        )
        qr = QueryReconstructor(llm_provider=llm)
        results = qr.reconstruct("specific query")
        count = sum(1 for r in results if r.lower() == "general query")
        assert count == 1, f"Expected 1 occurrence, got {count}: {results}"


# ── Rule-based fallback ────────────────────────────────────────────────

class TestRuleFallback:
    def test_rule_step_back_strips_stopwords_zh(self):
        qr = QueryReconstructor()  # No LLM → rule only
        results = qr.reconstruct("上次那个 JWT token 的问题怎么解决的")
        assert len(results) >= 1  # At minimum the original query
        # May or may not produce step-back; ensure no crash

    def test_rule_step_back_strips_stopwords_en(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("this is the recent database connection issue")
        assert len(results) >= 1

    def test_failing_llm_falls_back_to_rules(self):
        qr = QueryReconstructor(llm_provider=_FailingLLM())
        results = qr.reconstruct("how to fix the memory leak bug")
        assert len(results) >= 1
        assert results[0] == "how to fix the memory leak bug"

    def test_rule_variants_with_synonyms(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("AI search performance")
        assert len(results) >= 1
        assert results[0] == "AI search performance"

    def test_rule_variants_no_synonyms_no_crash(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("xyzabc123")
        assert len(results) >= 1
        assert results[0] == "xyzabc123"

    def test_rule_step_back_no_op_when_no_stopwords(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("JWT token authentication")
        assert results[0] == "JWT token authentication"


# ── Cache behaviour ────────────────────────────────────────────────────

class TestCache:
    def test_cache_enabled_returns_cached(self):
        llm = _MockLLM(step_back="step", variants="var1\nvar2")
        qr = QueryReconstructor(llm_provider=llm, enable_cache=True)
        first = qr.reconstruct("test query")
        call_count = len(llm.calls)
        second = qr.reconstruct("test query")
        # Should return from cache without additional LLM calls
        assert first == second
        assert len(llm.calls) == call_count

    def test_cache_disabled_calls_llm_again(self):
        llm = _MockLLM(step_back="step", variants="var1\nvar2")
        qr = QueryReconstructor(llm_provider=llm, enable_cache=False)
        qr.reconstruct("test query")
        count1 = len(llm.calls)
        qr.reconstruct("test query")
        count2 = len(llm.calls)
        assert count2 > count1

    def test_clear_cache(self):
        llm = _MockLLM(step_back="step", variants="var1")
        qr = QueryReconstructor(llm_provider=llm, enable_cache=True)
        qr.reconstruct("test query")
        qr.clear_cache()
        assert qr._cache == {}


# ── Edge cases ─────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_empty_query(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("")
        assert results == []

    def test_whitespace_query(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("   ")
        assert results == ["   "]

    def test_single_char_query(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("a")
        assert len(results) >= 1

    def test_results_always_include_original(self):
        qr = QueryReconstructor()
        results = qr.reconstruct("some query")
        assert results[0] == "some query"

    def test_llm_throws_exception_falls_back(self):
        class ThrowingLLM:
            def generate(self, *args, **kwargs):
                raise RuntimeError("simulated failure")
        qr = QueryReconstructor(llm_provider=ThrowingLLM())
        results = qr.reconstruct("how to fix database connection")
        assert len(results) >= 1
        assert results[0] == "how to fix database connection"


# ── Tokenization utility ───────────────────────────────────────────────

def test_clean_line_removes_numbering():
    assert _clean_line("1. hello") == "hello"
    assert _clean_line("2) world") == "world"
    assert _clean_line("3、测试") == "测试"
    assert _clean_line("hello") == "hello"
    assert _clean_line("") == ""
    assert _clean_line("   spaced   ") == "spaced"
