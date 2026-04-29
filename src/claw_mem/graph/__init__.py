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
claw-mem graph module - 概念介导知识图谱

基于 GAAMA 论文的四节点五边图谱结构.
"""

from .nodes import (
    NodeType,
    Node,
    EpisodeNode,
    FactNode,
    ReflectionNode,
    ConceptNode,
    create_node,
)

from .edges import (
    EdgeType,
    Edge,
    NextEdge,
    DerivedFromEdge,
    SynthesizedFromEdge,
    RelatedToEdge,
    HasConceptEdge,
    create_edge,
)

from .storage import (
    GraphStorage,
    InMemoryGraphStorage,
    FileGraphStorage,
)

from .concept_graph import (
    ConceptMediatedGraph,
    RetrievalResult,
    Embedder,
    DummyEmbedder,
    LLMExtractor as GraphLLMExtractor,
)

from .extractors import (
    BaseExtractor,
    LLMExtractor,
    DummyExtractor,
    KeywordExtractor,
)

__all__ = [
    # Nodes
    'NodeType',
    'Node',
    'EpisodeNode',
    'FactNode',
    'ReflectionNode',
    'ConceptNode',
    'create_node',
    # Edges
    'EdgeType',
    'Edge',
    'NextEdge',
    'DerivedFromEdge',
    'SynthesizedFromEdge',
    'RelatedToEdge',
    'HasConceptEdge',
    'create_edge',
    # Storage
    'GraphStorage',
    'InMemoryGraphStorage',
    'FileGraphStorage',
    # Core
    'ConceptMediatedGraph',
    'RetrievalResult',
    'Embedder',
    'DummyEmbedder',
    # Extractors
    'BaseExtractor',
    'LLMExtractor',
    'DummyExtractor',
    'KeywordExtractor',
]
