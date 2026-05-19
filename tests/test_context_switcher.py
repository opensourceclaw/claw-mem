# Copyright 2026 Peter Cheng
"""Tests for cms/context_switcher.py."""

import pytest
from claw_mem.cms.context_switcher import (
    SwitchResult, MergeResult, ContextSwitcher,
)


class TestSwitchResult:
    def test_create(self):
        sr = SwitchResult(from_session="a", to_session="b", strategy="preserve_important")
        assert sr.from_session == "a"
        assert sr.to_session == "b"
        assert sr.success is True

    def test_to_dict(self):
        sr = SwitchResult(from_session="a", to_session="b", strategy="full_switch",
                          preserved_memories=["m1"], total_memories=1)
        d = sr.to_dict()
        assert d["from_session"] == "a"
        assert "m1" in d["preserved_memories"]
        assert d["total_memories"] == 1


class TestMergeResult:
    def test_create(self):
        mr = MergeResult(session_ids=["a", "b"], merged_count=2, total_unique=5)
        assert mr.merged_count == 2
        assert mr.total_unique == 5

    def test_to_dict(self):
        mr = MergeResult(session_ids=["a"], merged_count=1, total_unique=3)
        d = mr.to_dict()
        assert d["merged_count"] == 1


class TestContextSwitcher:
    @pytest.fixture
    def switcher(self):
        return ContextSwitcher()

    def test_no_evaluator_no_error(self, switcher):
        result = switcher.switch("a", "b", strategy="preserve_important")
        assert result.success is True
        assert result.preserved_memories == []

    def test_full_switch(self, switcher):
        result = switcher.switch("a", "b", strategy="full_switch")
        assert result.success is True
        assert result.from_session == "a"
        assert result.to_session == "b"

    def test_merge_context(self, switcher):
        result = switcher.switch("a", "b", strategy="merge_context")
        assert result.success is True
        assert result.strategy == "merge_context"

    def test_merge_multiple(self, switcher):
        result = switcher.merge(["a", "b", "c"])
        assert result.merged_count == 3
        assert result.total_unique >= 0

    def test_get_active_contexts_empty(self, switcher):
        assert switcher.get_active_contexts() == []

    def test_switch_result_errors(self, switcher):
        result = switcher.switch("a", "b")
        assert result.success
        assert isinstance(result.preserved_memories, list)
