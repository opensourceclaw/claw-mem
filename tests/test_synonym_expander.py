# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
"""Tests for retrieval/synonym_expander.py (v2.9.0)"""

import pytest
from claw_mem.retrieval.synonym_expander import (
    SynonymExpander,
    get_synonym_expander,
    BUILTIN_SYNONYMS,
)


class TestSynonymExpander:
    def test_expand_ai_to_chinese(self):
        expander = SynonymExpander()
        result = expander.expand("AI technology")
        assert "人工智能" in result or "machine learning" in result.lower()

    def test_expand_chinese_to_english(self):
        expander = SynonymExpander()
        result = expander.expand("人工智能搜索")
        assert "ai" in result.lower() or "machine learning" in result.lower()

    def test_expand_memory_synonyms(self):
        expander = SynonymExpander()
        result = expander.expand("memory system")
        assert "记忆" in result or "storage" in result.lower()

    def test_expand_error_synonyms(self):
        expander = SynonymExpander()
        result = expander.expand("error in code")
        assert "错误" in result or "bug" in result.lower()

    def test_expand_deploy_synonyms(self):
        expander = SynonymExpander()
        result = expander.expand("deploy to production")
        assert "部署" in result or "发布" in result or "release" in result.lower()

    def test_expand_data_synonyms(self):
        expander = SynonymExpander()
        result = expander.expand("data processing")
        assert "数据" in result or "information" in result.lower()

    def test_expand_no_match(self):
        expander = SynonymExpander()
        result = expander.expand("xyzzy unique term")
        assert result == "xyzzy unique term"

    def test_expand_empty_query(self):
        expander = SynonymExpander()
        result = expander.expand("")
        assert result == ""

    def test_expand_disabled(self):
        expander = SynonymExpander(enabled=False)
        result = expander.expand("AI search")
        assert result == "AI search"

    def test_expand_max_expansions(self):
        expander = SynonymExpander(max_expansions=1)
        result = expander.expand("AI search")
        # Should only add at most 1 expansion term
        extra = result.replace("AI search", "").strip()
        assert len(extra.split()) <= 1

    def test_custom_synonyms(self):
        expander = SynonymExpander(custom_synonyms={
            "foobar": ["baz", "qux"]
        })
        result = expander.expand("foobar test")
        assert "baz" in result or "qux" in result

    def test_custom_synonyms_extend_existing(self):
        expander = SynonymExpander(custom_synonyms={
            "ai": ["custom_ai_term"]
        })
        syns = expander.get_synonyms("ai")
        assert "custom_ai_term" in syns

    def test_add_synonyms_new_keyword(self):
        expander = SynonymExpander()
        expander.add_synonyms("newterm", ["syn1", "syn2"])
        result = expander.expand("newterm test")
        assert "syn1" in result or "syn2" in result

    def test_add_synonyms_existing_keyword(self):
        expander = SynonymExpander()
        expander.add_synonyms("ai", ["smart_system"])
        result = expander.expand("AI test")
        assert "smart_system" in result.lower()

    def test_get_synonyms(self):
        expander = SynonymExpander()
        syns = expander.get_synonyms("ai")
        assert "人工智能" in syns or "machine learning" in syns

    def test_get_synonyms_unknown(self):
        expander = SynonymExpander()
        syns = expander.get_synonyms("nonexistent_term_xyz")
        assert syns == []

    def test_get_synonyms_case_insensitive(self):
        expander = SynonymExpander()
        syns1 = expander.get_synonyms("AI")
        syns2 = expander.get_synonyms("ai")
        assert syns1 == syns2

    def test_global_instance(self):
        e1 = get_synonym_expander()
        e2 = get_synonym_expander()
        assert e1 is e2
