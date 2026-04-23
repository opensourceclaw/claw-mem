# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for MemoryManager graph integration"""

import pytest
from claw_mem import MemoryManager


class TestMemoryManagerGraphIntegration:
    """测试 MemoryManager 图谱集成"""

    def test_memory_manager_without_graph(self):
        """测试默认不带图谱"""
        manager = MemoryManager(enable_gating=False)

        assert manager.graph is None
        assert manager.enable_graph is False

    def test_memory_manager_with_graph(self):
        """测试带图谱"""
        manager = MemoryManager(enable_gating=False, enable_graph=True)

        assert manager.graph is not None
        assert manager.enable_graph is True

        # 验证图谱可以正常工作
        from claw_mem.graph import NodeType
        ep_id = manager.graph.add_episode("测试内容", speaker="user")
        assert ep_id is not None

        node = manager.graph.get_node(ep_id)
        assert node is not None
        assert node.content == "测试内容"

    def test_backward_compatibility(self):
        """测试向后兼容"""
        # 不启用 graph 时，行为不变
        manager = MemoryManager(enable_gating=False)

        # 可以正常存储和检索
        manager.store("测试记忆内容", memory_type="episodic")
        results = manager.search("测试")
        assert isinstance(results, list)


class TestConceptMediatedGraphImport:
    """测试从 claw_mem 直接导入图谱类"""

    def test_import_concept_graph(self):
        """测试导入 ConceptMediatedGraph"""
        from claw_mem import ConceptMediatedGraph

        graph = ConceptMediatedGraph()
        assert graph is not None

    def test_import_node_types(self):
        """测试导入节点类型"""
        from claw_mem import NodeType, EpisodeNode, FactNode, ReflectionNode, ConceptNode

        assert NodeType.EPISODE.value == "episode"
        assert NodeType.FACT.value == "fact"
        assert NodeType.REFLECTION.value == "reflection"
        assert NodeType.CONCEPT.value == "concept"

    def test_import_embedder(self):
        """测试导入嵌入器"""
        from claw_mem import DummyEmbedder

        embedder = DummyEmbedder()
        vec = embedder.embed("test")
        assert len(vec) > 0

    def test_import_extractors(self):
        """测试导入提取器"""
        from claw_mem import LLMExtractor, KeywordExtractor

        llm_ext = LLMExtractor()
        facts = llm_ext.extract_facts("测试文本")
        assert isinstance(facts, list)

        kw_ext = KeywordExtractor()
        concepts = kw_ext.extract_concepts("测试文本")
        assert isinstance(concepts, list)
