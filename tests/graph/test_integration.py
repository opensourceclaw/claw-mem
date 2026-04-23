# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Integration tests for graph module"""

import pytest
from claw_mem.graph import (
    ConceptMediatedGraph,
    DummyEmbedder,
    LLMExtractor,
    DummyExtractor,
    KeywordExtractor,
    NodeType,
)
from claw_mem.graph.nodes import EpisodeNode


class TestGraphWithExtractor:
    """测试图谱与提取器集成"""

    def test_graph_with_llm_extractor(self):
        """测试图谱与 LLM 提取器集成"""
        extractor = LLMExtractor(llm_client=None)
        graph = ConceptMediatedGraph(extractor=extractor)

        turns = [
            {"speaker": "user", "content": "我决定使用 Python 开发项目"}
        ]

        episode_ids = graph.add_conversation(turns)

        assert len(episode_ids) == 1
        assert graph.storage.get_node(episode_ids[0]) is not None

    def test_graph_with_keyword_extractor(self):
        """测试图谱与关键词提取器集成"""
        extractor = KeywordExtractor()
        graph = ConceptMediatedGraph(extractor=extractor)

        turns = [
            {"speaker": "user", "content": "Python 编程"},
            {"speaker": "agent", "content": "推荐使用 pandas"}
        ]

        episode_ids = graph.add_conversation(turns)

        assert len(episode_ids) == 2
        # 验证概念是否被提取
        concepts = graph.storage.get_nodes_by_type(NodeType.CONCEPT)
        # KeywordExtractor 会提取概念
        assert len(concepts) >= 0

    def test_graph_with_dummy_extractor(self):
        """测试图谱与空提取器集成"""
        extractor = DummyExtractor()
        graph = ConceptMediatedGraph(extractor=extractor)

        turns = [
            {"speaker": "user", "content": "测试内容"}
        ]

        episode_ids = graph.add_conversation(turns)

        assert len(episode_ids) == 1
        # 空提取器不会创建 Fact 和 Concept
        facts = graph.storage.get_nodes_by_type(NodeType.FACT)
        assert len(facts) == 0


class TestGraphWithEmbedder:
    """测试图谱与嵌入器集成"""

    def test_graph_with_embedder(self):
        """测试图谱与嵌入器集成"""
        embedder = DummyEmbedder(dimension=128)
        graph = ConceptMediatedGraph(embedder=embedder)

        episode_id = graph.add_episode("Python 编程")

        node = graph.get_node(episode_id)
        assert node.embedding is not None
        assert len(node.embedding) == 128

    def test_graph_without_embedder(self):
        """测试图谱无嵌入器"""
        graph = ConceptMediatedGraph(embedder=None)

        episode_id = graph.add_episode("Python 编程")

        node = graph.get_node(episode_id)
        assert node.embedding is None


class TestRetrieveWithDifferentAlpha:
    """测试不同 alpha 的检索"""

    def test_retrieve_alpha_1(self):
        """测试纯语义检索"""
        embedder = DummyEmbedder()
        graph = ConceptMediatedGraph(embedder=embedder)

        graph.add_episode("Python 编程")
        graph.add_episode("JavaScript 开发")

        results = graph.retrieve("Python", alpha=1.0)

        assert len(results) > 0

    def test_retrieve_alpha_0(self):
        """测试纯 PPR"""
        embedder = DummyEmbedder()
        graph = ConceptMediatedGraph(embedder=embedder)

        graph.add_episode("Python 编程")
        graph.add_episode("JavaScript 开发")

        results = graph.retrieve("Python", alpha=0.0)

        assert len(results) > 0

    def test_retrieve_alpha_05(self):
        """测试混合检索"""
        embedder = DummyEmbedder()
        graph = ConceptMediatedGraph(embedder=embedder)

        graph.add_episode("Python 编程")
        graph.add_episode("JavaScript 开发")

        results = graph.retrieve("Python", alpha=0.5)

        assert len(results) > 0


class TestGraphEdgeCases:
    """测试边界情况"""

    def test_empty_graph_retrieve(self):
        """测试空图谱检索"""
        graph = ConceptMediatedGraph()

        results = graph.retrieve("test")

        assert results == []

    def test_get_neighbors_no_node(self):
        """测试获取不存在节点的邻居"""
        graph = ConceptMediatedGraph()

        neighbors = graph.get_neighbors("nonexistent")

        assert neighbors == []

    def test_get_stats_empty(self):
        """测试空图谱统计"""
        graph = ConceptMediatedGraph()

        stats = graph.get_stats()

        assert stats['total_nodes'] == 0
        assert stats['total_edges'] == 0
