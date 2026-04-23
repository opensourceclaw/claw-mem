# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for graph nodes"""

import pytest
from datetime import datetime
from claw_mem.graph.nodes import (
    NodeType,
    Node,
    EpisodeNode,
    FactNode,
    ReflectionNode,
    ConceptNode,
    create_node,
)


class TestNodeType:
    """测试节点类型枚举"""

    def test_node_type_values(self):
        assert NodeType.EPISODE.value == "episode"
        assert NodeType.FACT.value == "fact"
        assert NodeType.REFLECTION.value == "reflection"
        assert NodeType.CONCEPT.value == "concept"


class TestNode:
    """测试节点基类"""

    def test_create_node(self):
        node = Node(
            id="test_1",
            type=NodeType.EPISODE,
            content="Test content"
        )
        assert node.id == "test_1"
        assert node.type == NodeType.EPISODE
        assert node.content == "Test content"
        assert node.metadata == {}
        assert node.created_at is not None

    def test_node_to_dict(self):
        node = Node(
            id="test_1",
            type=NodeType.EPISODE,
            content="Test content"
        )
        data = node.to_dict()
        assert data['id'] == "test_1"
        assert data['type'] == "episode"
        assert data['content'] == "Test content"

    def test_node_from_dict(self):
        data = {
            'id': 'test_1',
            'type': 'episode',
            'content': 'Test content',
            'metadata': {'key': 'value'},
        }
        node = Node.from_dict(data)
        assert node.id == "test_1"
        assert node.type == NodeType.EPISODE
        assert node.content == "Test content"


class TestEpisodeNode:
    """测试情景节点"""

    def test_create_episode_node(self):
        node = EpisodeNode(
            id="ep_1",
            content="用户说：你好",
            sequence_id=0,
            speaker="user"
        )
        assert node.type == NodeType.EPISODE
        assert node.sequence_id == 0
        assert node.speaker == "user"

    def test_episode_node_with_timestamp(self):
        ts = datetime.now()
        node = EpisodeNode(
            id="ep_1",
            content="Test",
            timestamp=ts
        )
        assert node.timestamp == ts


class TestFactNode:
    """测试事实节点"""

    def test_create_fact_node(self):
        node = FactNode(
            id="fact_1",
            content="Python 是一种编程语言",
            confidence=0.9,
            source_episode="ep_1"
        )
        assert node.type == NodeType.FACT
        assert node.confidence == 0.9
        assert node.source_episode == "ep_1"


class TestReflectionNode:
    """测试反思节点"""

    def test_create_reflection_node(self):
        node = ReflectionNode(
            id="ref_1",
            content="用户对 Python 感兴趣",
            summary_type="insight",
            source_node_ids=["ep_1", "ep_2"]
        )
        assert node.type == NodeType.REFLECTION
        assert node.summary_type == "insight"
        assert len(node.source_node_ids) == 2


class TestConceptNode:
    """测试概念节点"""

    def test_create_concept_node(self):
        node = ConceptNode(
            id="concept_1",
            content="Python",
            category="topic",
            frequency=5
        )
        assert node.type == NodeType.CONCEPT
        assert node.category == "topic"
        assert node.frequency == 5


class TestCreateNode:
    """测试工厂函数"""

    def test_create_episode(self):
        node = create_node(NodeType.EPISODE, "Test content")
        assert isinstance(node, EpisodeNode)
        assert node.type == NodeType.EPISODE

    def test_create_fact(self):
        node = create_node(NodeType.FACT, "Test fact", confidence=0.8)
        assert isinstance(node, FactNode)
        assert node.confidence == 0.8

    def test_create_reflection(self):
        node = create_node(NodeType.REFLECTION, "Test reflection")
        assert isinstance(node, ReflectionNode)

    def test_create_concept(self):
        node = create_node(NodeType.CONCEPT, "Test concept")
        assert isinstance(node, ConceptNode)
