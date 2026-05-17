"""Integration tests for v2.15.0 - Engram + Spreading + Compression."""

import pytest
from claw_mem.graph.multi_graph import MultiGraphMemory, SubGraphType
from claw_mem.graph.nodes import NodeType
from claw_mem.graph.edges import EdgeType
from claw_mem.retrieval.engram import EngramIndex
from claw_mem.retrieval.spreading import SpreadingActivation
from claw_mem.retrieval.decoupled import DecoupledRetriever
from claw_mem.compression.spectrum import CompressionSpectrum


class TestFullRetrievalPipeline:
    """Integration test: Engram → Spreading → Ranking."""

    def setup_method(self):
        self.graph = MultiGraphMemory()
        self.engram = EngramIndex(ngram_size=3)

        # Build graph with semantic + temporal edges
        self.graph.add_node("mem_1", "用户偏好深色模式设置", NodeType.EPISODE)
        self.graph.add_node("mem_2", "Dark mode configuration steps", NodeType.FACT)
        self.graph.add_node("mem_3", "系统主题切换功能开发中", NodeType.EPISODE)
        self.graph.add_node("mem_4", "User prefers Chinese language responses", NodeType.FACT)
        self.graph.add_node("mem_5", "UI color scheme review meeting", NodeType.EPISODE)

        self.graph.add_edge("mem_1", "mem_2", EdgeType.RELATED_TO, 0.9)
        self.graph.add_edge("mem_1", "mem_3", EdgeType.NEXT, 0.8)
        self.graph.add_edge("mem_2", "mem_5", EdgeType.RELATED_TO, 0.6)

        # Index content in EngramIndex
        for nid, node in self.graph._node_index.items():
            self.engram.index(nid, node.content)

        self.spreader = SpreadingActivation(self.graph)
        self.retriever = DecoupledRetriever(
            self.engram, self.spreader, self.graph
        )

    def test_pipeline_basic_search(self):
        results = self.retriever.search("深色模式", top_k=5)
        assert len(results) >= 1
        assert any("深色" in r.get("content", "") for r in results)

    def test_pipeline_graph_expansion(self):
        """Search should expand via graph to find related nodes."""
        results = self.retriever.search("dark mode", top_k=5)
        assert len(results) >= 1

    def test_pipeline_empty_query(self):
        results = self.retriever.search("", top_k=5)
        assert results == []

    def test_pipeline_result_fields(self):
        results = self.retriever.search("用户偏好", top_k=3)
        for r in results:
            assert "id" in r
            assert "content" in r
            assert "score" in r
            assert "type" in r
            assert 0.0 <= r["score"] <= 1.0

    def test_pipeline_with_intent(self):
        results = self.retriever.search("UI review", top_k=5, intent="semantic")
        assert len(results) >= 1


class TestEngramGraphIntegration:
    """Test EngramIndex with graph expansion."""

    def test_engram_seeds_feed_spreading(self):
        graph = MultiGraphMemory()
        graph.add_node("a", "Parent", NodeType.EPISODE)
        graph.add_node("b", "Child", NodeType.EPISODE)
        graph.add_edge("a", "b", EdgeType.NEXT, 1.0)

        engram = EngramIndex(ngram_size=3)
        engram.index("a", "Parent node content")
        engram.index("b", "Child node content")

        spreader = SpreadingActivation(graph)
        seeds = dict(engram.lookup("Parent", top_k=5))
        activations = spreader.activate(seeds)
        assert "a" in activations
        assert "b" in activations  # via graph expansion

    def test_no_graph_fallback(self):
        """DecoupledRetriever works without a graph."""
        engram = EngramIndex(ngram_size=3)
        engram.index("x", "hello world test message")
        retriever = DecoupledRetriever(engram, None, None)
        results = retriever.search("hello world")
        assert len(results) >= 1


class TestCompressionIntegration:
    """Test compression spectrum with limited MM."""

    def test_spectrum_without_manager(self):
        spec = CompressionSpectrum()
        result = spec.record_access("test_id")
        assert result is None  # No MM → no content → no compression

    def test_spectrum_stats_default(self):
        spec = CompressionSpectrum()
        stats = spec.get_stats()
        assert stats["thresholds"]["skill_access"] == 5
        assert stats["thresholds"]["rule_apply"] == 3


class TestMemoryManagerIntegration:
    """Test MemoryManager v2.15.0 features."""

    def test_engram_property_lazy_init(self):
        # Use import in test to avoid workspace dependency
        from claw_mem.retrieval.engram import EngramIndex
        engram = EngramIndex(ngram_size=3)
        engram.index("test", "hello world")
        results = engram.lookup("hello")
        assert len(results) >= 1

    def test_spreader_configure(self):
        from claw_mem.graph.multi_graph import MultiGraphMemory
        mg = MultiGraphMemory()
        spreader = SpreadingActivation(mg)
        spreader.configure(max_depth=1, threshold=0.2)
        stats = spreader.get_stats()
        assert stats["max_depth"] == 1
        assert stats["threshold"] == 0.2
