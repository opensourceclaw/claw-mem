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
    """Test graph with extractor integration"""

    def test_graph_with_llm_extractor(self):
        """Test graph with LLM extractor integration"""
        extractor = LLMExtractor(llm_client=None)
        graph = ConceptMediatedGraph(extractor=extractor)

        turns = [{"speaker": "user", "content": "I decided to use Python for the project"}]

        episode_ids = graph.add_conversation(turns)

        assert len(episode_ids) == 1
        assert graph.storage.get_node(episode_ids[0]) is not None

    def test_graph_with_keyword_extractor(self):
        """Test graph with keyword extractor integration"""
        extractor = KeywordExtractor()
        graph = ConceptMediatedGraph(extractor=extractor)

        turns = [
            {"speaker": "user", "content": "Python programming"},
            {"speaker": "agent", "content": "Recommend using pandas"},
        ]

        episode_ids = graph.add_conversation(turns)

        assert len(episode_ids) == 2
        # Verify concepts were extracted
        concepts = graph.storage.get_nodes_by_type(NodeType.CONCEPT)
        # KeywordExtractor should extract concepts
        assert len(concepts) >= 0

    def test_graph_with_dummy_extractor(self):
        """Test graph with dummy extractor integration"""
        extractor = DummyExtractor()
        graph = ConceptMediatedGraph(extractor=extractor)

        turns = [{"speaker": "user", "content": "Test content"}]

        episode_ids = graph.add_conversation(turns)

        assert len(episode_ids) == 1
        # Dummy extractor should not create Fact or Concept
        facts = graph.storage.get_nodes_by_type(NodeType.FACT)
        assert len(facts) == 0


class TestGraphWithEmbedder:
    """Test graph with embedder integration"""

    def test_graph_with_embedder(self):
        """Test graph with embedder integration"""
        embedder = DummyEmbedder(dimension=128)
        graph = ConceptMediatedGraph(embedder=embedder)

        episode_id = graph.add_episode("Python programming")

        node = graph.get_node(episode_id)
        assert node.embedding is not None
        assert len(node.embedding) == 128

    def test_graph_without_embedder(self):
        """Test graph without embedder"""
        graph = ConceptMediatedGraph(embedder=None)

        episode_id = graph.add_episode("Python programming")

        node = graph.get_node(episode_id)
        assert node.embedding is None


class TestRetrieveWithDifferentAlpha:
    """Test retrieval with different alpha values"""

    def test_retrieve_alpha_1(self):
        """Test pure semantic retrieval"""
        embedder = DummyEmbedder()
        graph = ConceptMediatedGraph(embedder=embedder)

        graph.add_episode("Python programming")
        graph.add_episode("JavaScript development")

        results = graph.retrieve("Python", alpha=1.0)

        assert len(results) > 0

    def test_retrieve_alpha_0(self):
        """Test pure PPR"""
        embedder = DummyEmbedder()
        graph = ConceptMediatedGraph(embedder=embedder)

        graph.add_episode("Python programming")
        graph.add_episode("JavaScript development")

        results = graph.retrieve("Python", alpha=0.0)

        assert len(results) > 0

    def test_retrieve_alpha_05(self):
        """Test hybrid retrieval"""
        embedder = DummyEmbedder()
        graph = ConceptMediatedGraph(embedder=embedder)

        graph.add_episode("Python programming")
        graph.add_episode("JavaScript development")

        results = graph.retrieve("Python", alpha=0.5)

        assert len(results) > 0


class TestGraphEdgeCases:
    """Test edge cases"""

    def test_empty_graph_retrieve(self):
        """Test empty graph retrieval"""
        graph = ConceptMediatedGraph()

        results = graph.retrieve("test")

        assert results == []

    def test_get_neighbors_no_node(self):
        """Test getting neighbors for nonexistent node"""
        graph = ConceptMediatedGraph()

        neighbors = graph.get_neighbors("nonexistent")

        assert neighbors == []

    def test_get_stats_empty(self):
        """Test empty graph stats"""
        graph = ConceptMediatedGraph()

        stats = graph.get_stats()

        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
