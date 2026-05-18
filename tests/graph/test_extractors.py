# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for graph extractors"""

import pytest
from claw_mem.graph.extractors import (
    BaseExtractor,
    LLMExtractor,
    DummyExtractor,
    KeywordExtractor,
)


class TestLLMExtractor:
    """Test LLM extractor"""

    def test_extract_facts_without_llm(self):
        """Test extractor without LLM"""
        extractor = LLMExtractor(llm_client=None)

        text = "User decided to use Python for development. System has been deployed."

        facts = extractor.extract_facts(text)

        assert len(facts) > 0
        assert isinstance(facts, list)
        assert all(isinstance(f, str) for f in facts)

    def test_extract_concepts_without_llm(self):
        """Test concept extraction without LLM"""
        extractor = LLMExtractor(llm_client=None)

        text = "User decided to use Python for development. System has been deployed."

        concepts = extractor.extract_concepts(text)

        assert len(concepts) > 0
        assert isinstance(concepts, list)

    def test_extract_facts_empty_text(self):
        """Test empty text"""
        extractor = LLMExtractor(llm_client=None)

        facts = extractor.extract_facts("")

        assert facts == []

    def test_extract_concepts_empty_text(self):
        """Test empty text"""
        extractor = LLMExtractor(llm_client=None)

        concepts = extractor.extract_concepts("")

        assert concepts == []

    def test_extract_facts_chinese(self):
        """Test Chinese fact extraction"""
        extractor = LLMExtractor(llm_client=None)

        text = "今天的天气非常好，适合出去散步。"

        facts = extractor.extract_facts(text)

        assert len(facts) > 0

    def test_extract_concepts_chinese(self):
        """Test Chinese concept extraction"""
        extractor = LLMExtractor(llm_client=None)

        text = "Python 是一种编程语言.JavaScript 用于网页开发."

        concepts = extractor.extract_concepts(text)

        assert len(concepts) > 0

    def test_generate_reflection_without_llm(self):
        """Test reflection generation without LLM"""
        from claw_mem.graph.nodes import EpisodeNode

        extractor = LLMExtractor(llm_client=None)

        nodes = [
            EpisodeNode(id="1", content="User says: Hello"),
            EpisodeNode(id="2", content="Agent says: Hello"),
        ]

        reflection = extractor.generate_reflection(nodes)

        assert isinstance(reflection, str)
        assert len(reflection) > 0


class TestDummyExtractor:
    """Test dummy extractor"""

    def test_extract_facts(self):
        """Test returns empty list"""
        extractor = DummyExtractor()

        facts = extractor.extract_facts("any text")

        assert facts == []

    def test_extract_concepts(self):
        """Test returns empty list"""
        extractor = DummyExtractor()

        concepts = extractor.extract_concepts("any text")

        assert concepts == []


class TestKeywordExtractor:
    """Test keyword extractor"""

    def test_extract_facts(self):
        """Test fact extraction"""
        extractor = KeywordExtractor()

        text = "User decided to use Python for development. System has been deployed."

        facts = extractor.extract_facts(text)

        assert len(facts) > 0

    def test_extract_concepts(self):
        """Test concept extraction"""
        extractor = KeywordExtractor()

        text = "Python 是一种编程语言.JavaScript 用于网页开发."

        concepts = extractor.extract_concepts(text)

        assert len(concepts) > 0
        assert "Python" in concepts or "编程" in concepts or "语言" in concepts
