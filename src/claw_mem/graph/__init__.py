# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
claw-mem graph module - Concept-Mediated Knowledge Graph

Four-node, five-edge graph structure based on the GAAMA paper.
"""

from .concept_graph import ConceptMediatedGraph, DummyEmbedder, Embedder, RetrievalResult
from .dual_layer import DualLayerMemory, Event, Topic
from .edges import (
    DerivedFromEdge,
    Edge,
    EdgeType,
    HasConceptEdge,
    NextEdge,
    RelatedToEdge,
    SynthesizedFromEdge,
    create_edge,
)
from .extractors import BaseExtractor, DummyExtractor, KeywordExtractor, LLMExtractor
from .multi_graph import (
    EDGE_TO_SUBGRAPH,
    SUBGRAPH_EXPANSION_WEIGHT,
    GraphEdge,
    MultiGraphMemory,
    SubGraph,
    SubGraphType,
)
from .nodes import ConceptNode, EpisodeNode, FactNode, Node, NodeType, ReflectionNode, create_node
from .storage import FileGraphStorage, GraphStorage, InMemoryGraphStorage

__all__ = [
    # Nodes
    "NodeType",
    "Node",
    "EpisodeNode",
    "FactNode",
    "ReflectionNode",
    "ConceptNode",
    "create_node",
    # Edges
    "EdgeType",
    "Edge",
    "NextEdge",
    "DerivedFromEdge",
    "SynthesizedFromEdge",
    "RelatedToEdge",
    "HasConceptEdge",
    "create_edge",
    # Storage
    "GraphStorage",
    "InMemoryGraphStorage",
    "FileGraphStorage",
    # Core
    "ConceptMediatedGraph",
    "RetrievalResult",
    "Embedder",
    "DummyEmbedder",
    # Extractors
    "BaseExtractor",
    "LLMExtractor",
    "DummyExtractor",
    "KeywordExtractor",
    # v2.14.0: MultiGraph + DualLayer
    "SubGraphType",
    "SubGraph",
    "GraphEdge",
    "MultiGraphMemory",
    "EDGE_TO_SUBGRAPH",
    "SUBGRAPH_EXPANSION_WEIGHT",
    "Event",
    "Topic",
    "DualLayerMemory",
]
