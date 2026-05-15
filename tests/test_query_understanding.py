"""Tests for QueryUnderstanding module (P0-1 Stage 1)"""

import pytest
from claw_mem.retrieval.query_understanding import (
    QueryUnderstanding,
    QueryIntent,
    ExpandedQuery,
)


class TestQueryIntent:
    def test_enum_values(self):
        assert QueryIntent.FACT.value == "fact"
        assert QueryIntent.RECENT.value == "recent"
        assert QueryIntent.PREFERENCE.value == "preference"
        assert QueryIntent.PROCEDURE.value == "procedure"
        assert QueryIntent.GENERAL.value == "general"


class TestExpandedQuery:
    def test_default_creation(self):
        eq = ExpandedQuery(
            original="test query",
            expanded_text="test query expansion",
            intent=QueryIntent.FACT,
            entities=["test"],
        )
        assert eq.original == "test query"
        assert eq.expanded_text == "test query expansion"
        assert eq.intent == QueryIntent.FACT
        assert eq.entities == ["test"]
        assert eq.confidence == 0.0
        assert eq.tokens == []

    def test_to_dict(self):
        eq = ExpandedQuery(
            original="test",
            expanded_text="test expanded",
            intent=QueryIntent.GENERAL,
            entities=["entity1"],
            confidence=0.5,
            tokens=["test"],
        )
        d = eq.to_dict()
        assert d["original"] == "test"
        assert d["intent"] == "general"
        assert d["entities"] == ["entity1"]
        assert d["confidence"] == 0.5


class TestQueryUnderstanding:
    @pytest.fixture
    def qu(self):
        return QueryUnderstanding()

    def test_fact_intent_english(self, qu):
        expanded = qu.understand("what is the memory system?")
        assert expanded.intent == QueryIntent.FACT
        assert expanded.confidence > 0

    def test_fact_intent_chinese(self, qu):
        expanded = qu.understand("什么是内存系统？")
        assert expanded.intent == QueryIntent.FACT

    def test_preference_intent(self, qu):
        expanded = qu.understand("what is my preferred AI framework?")
        assert expanded.intent == QueryIntent.PREFERENCE

    def test_preference_chinese(self, qu):
        expanded = qu.understand("我最喜欢的编程语言是什么？")
        assert expanded.intent == QueryIntent.PREFERENCE

    def test_recent_intent(self, qu):
        expanded = qu.understand("what did I do yesterday?")
        assert expanded.intent == QueryIntent.RECENT

    def test_recent_chinese(self, qu):
        expanded = qu.understand("最近做了什么？")
        assert expanded.intent == QueryIntent.RECENT

    def test_procedure_intent(self, qu):
        expanded = qu.understand("how do I set up the project?")
        assert expanded.intent == QueryIntent.PROCEDURE

    def test_procedure_chinese(self, qu):
        expanded = qu.understand("怎么配置项目？")
        assert expanded.intent == QueryIntent.PROCEDURE

    def test_general_fallback(self, qu):
        expanded = qu.understand("hello world")
        assert expanded.intent == QueryIntent.GENERAL

    def test_empty_query(self, qu):
        expanded = qu.understand("")
        assert expanded.intent == QueryIntent.GENERAL
        assert expanded.entities == []

    def test_entity_extraction(self, qu):
        expanded = qu.understand("project claw-mem version 2.15.0")
        assert "claw-mem" in expanded.entities or any("claw" in e for e in expanded.entities)

    def test_entity_extraction_version(self, qu):
        expanded = qu.understand("deploy version 3.0.0 of the library")
        assert any("3.0.0" in e for e in expanded.entities)

    def test_synonym_expansion(self, qu):
        expanded = qu.understand("AI search performance")
        assert len(expanded.expanded_text) >= len(expanded.original)

    def test_expand_query_separate(self, qu):
        result = qu.expand_query("memory performance")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_classify_intent_separate(self, qu):
        intent, conf = qu.classify_intent("how to deploy?")
        assert isinstance(intent, QueryIntent)
        assert 0.0 <= conf <= 1.0

    def test_extract_entities_separate(self, qu):
        entities = qu.extract_entities("claw-mem project version 2.14.0")
        assert isinstance(entities, list)
        assert len(entities) > 0

    def test_get_statistics(self, qu):
        qu.understand("test query")
        stats = qu.get_statistics()
        assert stats["queries_processed"] >= 1

    def test_context_inference(self, qu):
        context = {"recent_messages": ["应该怎么配置？"]}
        expanded = qu.understand("project setup", context=context)
        # Should have some intent from context
        assert expanded.intent != QueryIntent.GENERAL or expanded.confidence > 0

    def test_context_preference_inference(self, qu):
        context = {"recent_messages": ["我喜欢用 Python", "选择什么好呢"]}
        expanded = qu.understand("test", context=context)
        assert expanded.intent in (QueryIntent.PREFERENCE, QueryIntent.FACT, QueryIntent.GENERAL)


class TestQueryUnderstandingEdgeCases:
    @pytest.fixture
    def qu(self):
        return QueryUnderstanding()

    def test_very_long_query(self, qu):
        long_query = "performance " * 50
        expanded = qu.understand(long_query)
        assert isinstance(expanded.intent, QueryIntent)

    def test_special_characters(self, qu):
        expanded = qu.understand("test @#$%^&* query!")
        assert isinstance(expanded.intent, QueryIntent)

    def test_unicode_only(self, qu):
        expanded = qu.understand("你好世界")
        assert isinstance(expanded.intent, QueryIntent)

    def test_mixed_language(self, qu):
        expanded = qu.understand("how to 配置 the AI model？")
        assert isinstance(expanded.intent, QueryIntent)

    def test_single_word_query(self, qu):
        expanded = qu.understand("test")
        assert isinstance(expanded.intent, QueryIntent)
