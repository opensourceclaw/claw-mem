"""Tests for ContextSwitcher (v3.0.0-rc.3)."""

import pytest
from claw_mem.cms.context_switcher import ContextSwitcher, SwitchResult, MergeResult


class TestContextSwitcher:
    def setup_method(self):
        self.cs = ContextSwitcher()

    def test_switch_preserve_important(self):
        r = self.cs.switch("s1", "s2", "preserve_important")
        assert isinstance(r, SwitchResult)
        assert r.from_session == "s1"
        assert r.strategy == "preserve_important"

    def test_switch_full_switch(self):
        r = self.cs.switch("a", "b", "full_switch")
        assert r.to_session == "b"
        assert r.preserved_memories == []

    def test_merge_contexts(self):
        r = self.cs.merge(["s1", "s2", "s3"])
        assert isinstance(r, MergeResult)
        assert r.merged_count == 3

    def test_switch_result_to_dict(self):
        r = SwitchResult("a", "b", "preserve_important", ["m1"], 1)
        d = r.to_dict()
        assert d["from_session"] == "a"
        assert d["preserved_memories"] == ["m1"]

    def test_merge_result_to_dict(self):
        r = MergeResult(["a", "b"], 2, 10)
        d = r.to_dict()
        assert d["merged_count"] == 2

    def test_active_contexts_default(self):
        assert self.cs.get_active_contexts() == []
