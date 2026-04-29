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
    """测试 LLM 提取器"""

    def test_extract_facts_without_llm(self):
        """测试无 LLM 时的提取器"""
        extractor = LLMExtractor(llm_client=None)

        text = "用户决定使用 Python 开发项目.系统已完成部署."

        facts = extractor.extract_facts(text)

        assert len(facts) > 0
        assert isinstance(facts, list)
        assert all(isinstance(f, str) for f in facts)

    def test_extract_concepts_without_llm(self):
        """测试无 LLM 时提取概念"""
        extractor = LLMExtractor(llm_client=None)

        text = "用户决定使用 Python 开发项目.系统已完成部署."

        concepts = extractor.extract_concepts(text)

        assert len(concepts) > 0
        assert isinstance(concepts, list)

    def test_extract_facts_empty_text(self):
        """测试空文本"""
        extractor = LLMExtractor(llm_client=None)

        facts = extractor.extract_facts("")

        assert facts == []

    def test_extract_concepts_empty_text(self):
        """测试空文本"""
        extractor = LLMExtractor(llm_client=None)

        concepts = extractor.extract_concepts("")

        assert concepts == []

    def test_extract_facts_chinese(self):
        """测试中文事实提取"""
        extractor = LLMExtractor(llm_client=None)

        text = "今天天气很好.用户去公园散步.公园里有很多花."

        facts = extractor.extract_facts(text)

        assert len(facts) > 0

    def test_extract_concepts_chinese(self):
        """测试中文概念提取"""
        extractor = LLMExtractor(llm_client=None)

        text = "Python 是一种编程语言.JavaScript 用于网页开发."

        concepts = extractor.extract_concepts(text)

        assert len(concepts) > 0

    def test_generate_reflection_without_llm(self):
        """测试无 LLM 时生成反思"""
        from claw_mem.graph.nodes import EpisodeNode

        extractor = LLMExtractor(llm_client=None)

        nodes = [
            EpisodeNode(id="1", content="用户说:你好"),
            EpisodeNode(id="2", content="Agent 回答:你好"),
        ]

        reflection = extractor.generate_reflection(nodes)

        assert isinstance(reflection, str)
        assert len(reflection) > 0


class TestDummyExtractor:
    """测试空提取器"""

    def test_extract_facts(self):
        """测试返回空列表"""
        extractor = DummyExtractor()

        facts = extractor.extract_facts("任何文本")

        assert facts == []

    def test_extract_concepts(self):
        """测试返回空列表"""
        extractor = DummyExtractor()

        concepts = extractor.extract_concepts("任何文本")

        assert concepts == []


class TestKeywordExtractor:
    """测试关键词提取器"""

    def test_extract_facts(self):
        """测试事实提取"""
        extractor = KeywordExtractor()

        text = "用户决定使用 Python 开发项目.系统已完成部署."

        facts = extractor.extract_facts(text)

        assert len(facts) > 0

    def test_extract_concepts(self):
        """测试概念提取"""
        extractor = KeywordExtractor()

        text = "Python 是一种编程语言.JavaScript 用于网页开发."

        concepts = extractor.extract_concepts(text)

        assert len(concepts) > 0
        assert "Python" in concepts or "编程" in concepts or "语言" in concepts
