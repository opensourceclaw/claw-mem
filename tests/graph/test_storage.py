# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for graph storage"""

import pytest
import tempfile
import os
from claw_mem.graph.storage import (
    InMemoryGraphStorage,
    FileGraphStorage,
)
from claw_mem.graph.nodes import (
    NodeType,
    EpisodeNode,
    FactNode,
    ConceptNode,
)
from claw_mem.graph.edges import (
    EdgeType,
    Edge,
)


class TestInMemoryGraphStorage:
    """测试内存图谱存储"""

    def setup_method(self):
        self.storage = InMemoryGraphStorage()

    def test_save_node(self):
        node = EpisodeNode(id="ep_1", content="Test")
        self.storage.save_node(node)
        assert self.storage.get_node("ep_1") is not None

    def test_get_node_not_found(self):
        assert self.storage.get_node("nonexistent") is None

    def test_delete_node(self):
        node = EpisodeNode(id="ep_1", content="Test")
        self.storage.save_node(node)
        assert self.storage.delete_node("ep_1") is True
        assert self.storage.get_node("ep_1") is None

    def test_delete_node_not_found(self):
        assert self.storage.delete_node("nonexistent") is False

    def test_get_all_nodes(self):
        node1 = EpisodeNode(id="ep_1", content="Test 1")
        node2 = FactNode(id="fact_1", content="Test 2")
        self.storage.save_node(node1)
        self.storage.save_node(node2)
        nodes = self.storage.get_all_nodes()
        assert len(nodes) == 2

    def test_get_nodes_by_type(self):
        node1 = EpisodeNode(id="ep_1", content="Test 1")
        node2 = FactNode(id="fact_1", content="Test 2")
        self.storage.save_node(node1)
        self.storage.save_node(node2)
        episodes = self.storage.get_nodes_by_type(NodeType.EPISODE)
        assert len(episodes) == 1

    def test_save_edge(self):
        edge = Edge("ep_1", "ep_2", EdgeType.NEXT)
        self.storage.save_edge(edge)
        edges = self.storage.get_edges_from("ep_1")
        assert len(edges) == 1

    def test_get_edges_from(self):
        edge = Edge("ep_1", "ep_2", EdgeType.NEXT)
        self.storage.save_edge(edge)
        edges = self.storage.get_edges_from("ep_1")
        assert edges[0].target_id == "ep_2"

    def test_get_edges_to(self):
        edge = Edge("ep_1", "ep_2", EdgeType.NEXT)
        self.storage.save_edge(edge)
        edges = self.storage.get_edges_to("ep_2")
        assert edges[0].source_id == "ep_1"

    def test_get_neighbors(self):
        edge1 = Edge("ep_1", "ep_2", EdgeType.NEXT)
        edge2 = Edge("ep_1", "ep_3", EdgeType.NEXT)
        self.storage.save_edge(edge1)
        self.storage.save_edge(edge2)
        neighbors = self.storage.get_neighbors("ep_1")
        assert "ep_2" in neighbors
        assert "ep_3" in neighbors

    def test_get_stats(self):
        ep = EpisodeNode(id="ep_1", content="Test")
        fact = FactNode(id="fact_1", content="Test")
        self.storage.save_node(ep)
        self.storage.save_node(fact)
        stats = self.storage.get_stats()
        assert stats['total_nodes'] == 2
        assert stats['episodes'] == 1
        assert stats['facts'] == 1

    def test_clear(self):
        node = EpisodeNode(id="ep_1", content="Test")
        self.storage.save_node(node)
        self.storage.clear()
        assert len(self.storage.get_all_nodes()) == 0


class TestFileGraphStorage:
    """测试文件图谱存储"""

    def setup_method(self):
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        self.temp_file.close()
        self.storage = FileGraphStorage(self.temp_file.name)

    def teardown_method(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_save_and_load(self):
        node = EpisodeNode(id="ep_1", content="Test content")
        self.storage.save_node(node)

        # 重新加载
        storage2 = FileGraphStorage(self.temp_file.name)
        loaded = storage2.get_node("ep_1")
        assert loaded is not None
        assert loaded.content == "Test content"

    def test_save_edge(self):
        node1 = EpisodeNode(id="ep_1", content="Test 1")
        node2 = EpisodeNode(id="ep_2", content="Test 2")
        self.storage.save_node(node1)
        self.storage.save_node(node2)

        edge = Edge("ep_1", "ep_2", EdgeType.NEXT)
        self.storage.save_edge(edge)

        # 重新加载
        storage2 = FileGraphStorage(self.temp_file.name)
        edges = storage2.get_edges_from("ep_1")
        assert len(edges) == 1
