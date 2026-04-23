# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""Tests for graph edges"""

import pytest
from claw_mem.graph.edges import (
    EdgeType,
    Edge,
    NextEdge,
    DerivedFromEdge,
    SynthesizedFromEdge,
    RelatedToEdge,
    HasConceptEdge,
    create_edge,
)


class TestEdgeType:
    """测试边类型枚举"""

    def test_edge_type_values(self):
        assert EdgeType.NEXT.value == "NEXT"
        assert EdgeType.DERIVED_FROM.value == "DERIVED_FROM"
        assert EdgeType.SYNTHESIZED_FROM.value == "SYNTHESIZED_FROM"
        assert EdgeType.RELATED_TO.value == "RELATED_TO"
        assert EdgeType.HAS_CONCEPT.value == "HAS_CONCEPT"

    def test_is_directed(self):
        assert EdgeType.NEXT.is_directed() is True
        assert EdgeType.DERIVED_FROM.is_directed() is True
        assert EdgeType.RELATED_TO.is_directed() is False


class TestEdge:
    """测试边基类"""

    def test_create_edge(self):
        edge = Edge(
            source_id="ep_1",
            target_id="ep_2",
            type=EdgeType.NEXT,
            weight=1.0
        )
        assert edge.source_id == "ep_1"
        assert edge.target_id == "ep_2"
        assert edge.type == EdgeType.NEXT
        assert edge.weight == 1.0

    def test_edge_to_dict(self):
        edge = Edge(
            source_id="ep_1",
            target_id="ep_2",
            type=EdgeType.NEXT,
            weight=1.0
        )
        data = edge.to_dict()
        assert data['source_id'] == "ep_1"
        assert data['target_id'] == "ep_2"
        assert data['type'] == "NEXT"
        assert data['weight'] == 1.0

    def test_edge_from_dict(self):
        data = {
            'source_id': 'ep_1',
            'target_id': 'ep_2',
            'type': 'NEXT',
            'weight': 1.0,
            'metadata': {'key': 'value'},
        }
        edge = Edge.from_dict(data)
        assert edge.source_id == "ep_1"
        assert edge.target_id == "ep_2"
        assert edge.type == EdgeType.NEXT


class TestNextEdge:
    """测试 NEXT 边"""

    def test_create_next_edge(self):
        edge = NextEdge("ep_1", "ep_2")
        assert edge.type == EdgeType.NEXT
        assert edge.source_id == "ep_1"
        assert edge.target_id == "ep_2"


class TestDerivedFromEdge:
    """测试 DERIVED_FROM 边"""

    def test_create_derived_from_edge(self):
        edge = DerivedFromEdge("fact_1", "ep_1")
        assert edge.type == EdgeType.DERIVED_FROM


class TestSynthesizedFromEdge:
    """测试 SYNTHESIZED_FROM 边"""

    def test_create_synthesized_from_edge(self):
        edge = SynthesizedFromEdge(
            "ref_1",
            "ep_1",
            source_node_ids=["ep_1", "fact_1"]
        )
        assert edge.type == EdgeType.SYNTHESIZED_FROM
        assert len(edge.source_node_ids) == 2


class TestRelatedToEdge:
    """测试 RELATED_TO 边"""

    def test_create_related_to_edge(self):
        edge = RelatedToEdge("ep_1", "fact_1")
        assert edge.type == EdgeType.RELATED_TO


class TestHasConceptEdge:
    """测试 HAS_CONCEPT 边"""

    def test_create_has_concept_edge(self):
        edge = HasConceptEdge("ep_1", "concept_1")
        assert edge.type == EdgeType.HAS_CONCEPT


class TestCreateEdge:
    """测试工厂函数"""

    def test_create_next(self):
        edge = create_edge(EdgeType.NEXT, "ep_1", "ep_2")
        assert isinstance(edge, NextEdge)

    def test_create_derived_from(self):
        edge = create_edge(EdgeType.DERIVED_FROM, "fact_1", "ep_1")
        assert isinstance(edge, DerivedFromEdge)

    def test_create_synthesized_from(self):
        edge = create_edge(EdgeType.SYNTHESIZED_FROM, "ref_1", "ep_1")
        assert isinstance(edge, SynthesizedFromEdge)

    def test_create_related_to(self):
        edge = create_edge(EdgeType.RELATED_TO, "ep_1", "fact_1")
        assert isinstance(edge, RelatedToEdge)

    def test_create_has_concept(self):
        edge = create_edge(EdgeType.HAS_CONCEPT, "ep_1", "concept_1")
        assert isinstance(edge, HasConceptEdge)
