# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for concept graph"""

import pytest
from claw_mem.graph.concept_graph import (
    ConceptMediatedGraph,
    RetrievalResult,
    DummyEmbedder,
)
from claw_mem.graph.nodes import NodeType


class TestConceptMediatedGraph:
    """测试概念介导图谱"""

    def setup_method(self):
        self.graph = ConceptMediatedGraph(embedder=DummyEmbedder())

    def test_add_single_episode(self):
        node_id = self.graph.add_episode(
            content="用户说：你好",
            speaker="user"
        )
        assert node_id is not None
        node = self.graph.get_node(node_id)
        assert node is not None
        assert node.content == "用户说：你好"

    def test_add_conversation(self):
        turns = [
            {"speaker": "user", "content": "我想学习 Python"},
            {"speaker": "agent", "content": "推荐从基础语法开始"}
        ]
        episode_ids = self.graph.add_conversation(turns)
        assert len(episode_ids) == 2

    def test_add_fact(self):
        ep_id = self.graph.add_episode("Test episode")
        fact_id = self.graph.add_fact(
            content="Python 是一种编程语言",
            source_episode_id=ep_id,
            confidence=0.9
        )
        assert fact_id is not None
        fact = self.graph.get_node(fact_id)
        assert fact.type == NodeType.FACT

    def test_add_concept(self):
        concept_id = self.graph.add_concept(
            content="Python",
            category="topic"
        )
        assert concept_id is not None
        concept = self.graph.get_node(concept_id)
        assert concept.type == NodeType.CONCEPT
        assert concept.frequency == 1

    def test_add_concept_increments_frequency(self):
        self.graph.add_concept("Python")
        self.graph.add_concept("Python")
        # 查找概念
        from claw_mem.graph.nodes import ConceptNode
        for node in self.graph.storage.get_nodes_by_type(NodeType.CONCEPT):
            if isinstance(node, ConceptNode) and node.content == "Python":
                assert node.frequency == 2

    def test_add_reflection(self):
        ep_id = self.graph.add_episode("Test episode")
        ref_id = self.graph.add_reflection(
            content="用户对编程感兴趣",
            source_node_ids=[ep_id],
            summary_type="insight"
        )
        assert ref_id is not None
        reflection = self.graph.get_node(ref_id)
        assert reflection.type == NodeType.REFLECTION

    def test_get_neighbors(self):
        ep_id = self.graph.add_episode("Test episode")
        fact_id = self.graph.add_fact(
            content="Test fact",
            source_episode_id=ep_id
        )
        neighbors = self.graph.get_neighbors(fact_id)
        neighbor_ids = [n.id for n in neighbors]
        assert ep_id in neighbor_ids

    def test_get_stats(self):
        self.graph.add_episode("Test 1")
        self.graph.add_episode("Test 2")
        stats = self.graph.get_stats()
        assert stats['total_nodes'] >= 2


class TestRetrieve:
    """测试检索功能"""

    def setup_method(self):
        self.graph = ConceptMediatedGraph(embedder=DummyEmbedder())

    def test_retrieve_empty_graph(self):
        results = self.graph.retrieve("test query")
        assert len(results) == 0

    def test_retrieve_with_results(self):
        self.graph.add_episode("Python 是一种编程语言")
        self.graph.add_episode("JavaScript 用于网页开发")

        results = self.graph.retrieve("Python", k=5)
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)

    def test_retrieve_with_alpha(self):
        self.graph.add_episode("Python 编程")
        self.graph.add_episode("JavaScript 开发")

        # 纯语义检索
        results_semantic = self.graph.retrieve("Python", alpha=1.0)
        # 纯 PPR
        results_ppr = self.graph.retrieve("Python", alpha=0.0)
        # 混合
        results_hybrid = self.graph.retrieve("Python", alpha=0.5)

        assert len(results_semantic) > 0
        assert len(results_ppr) > 0
        assert len(results_hybrid) > 0

    def test_retrieve_with_type_filter(self):
        self.graph.add_episode("Test episode")
        self.graph.add_concept("Test concept")

        results = self.graph.retrieve(
            "Test",
            node_types=[NodeType.EPISODE]
        )
        assert all(r.type == "episode" for r in results)

    def test_retrieve_limit_k(self):
        for i in range(20):
            self.graph.add_episode(f"内容 {i}")

        results = self.graph.retrieve("内容", k=5)
        assert len(results) == 5


class TestDummyEmbedder:
    """测试虚拟嵌入器"""

    def test_embed(self):
        embedder = DummyEmbedder(dimension=128)
        vec1 = embedder.embed("hello")
        vec2 = embedder.embed("hello")

        assert len(vec1) == 128
        assert len(vec2) == 128
        # 相同文本应生成相同向量
        assert vec1 == vec2

    def test_embed_normalized(self):
        import numpy as np
        embedder = DummyEmbedder()
        vec = embedder.embed("test")
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 0.001
