// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * claw-mem graph module - Concept-Mediated Knowledge Graph
 *
 * Four-node, five-edge graph structure based on the GAAMA paper.
 */

// Nodes
export {
  NodeType,
  Node,
  EpisodeNode,
  FactNode,
  ReflectionNode,
  ConceptNode,
  createNode,
} from "./nodes";
export type { NodeDict, AnyNode } from "./nodes";

// Edges
export {
  EdgeType,
  Edge,
  NextEdge,
  DerivedFromEdge,
  SynthesizedFromEdge,
  RelatedToEdge,
  HasConceptEdge,
  createEdge,
  isEdgeDirected,
} from "./edges";
export type { EdgeDict, AnyEdge } from "./edges";

// Storage
export {
  GraphStorage,
  InMemoryGraphStorage,
  FileGraphStorage,
} from "./storage";

// Core
export {
  ConceptMediatedGraph,
  RetrievalResult,
  Embedder,
  DummyEmbedder,
} from "./concept_graph";

// Extractors
export {
  BaseExtractor,
  LLMExtractor,
  DummyExtractor,
  KeywordExtractor,
} from "./extractors";
export type { LLMClient } from "./extractors";

// v2.14.0: MultiGraph + DualLayer
export {
  SubGraphType,
  SubGraph,
  MultiGraphMemory,
  EDGE_TO_SUBGRAPH,
  SUBGRAPH_EXPANSION_WEIGHT,
} from "./multi_graph";
export type { GraphEdgeRecord } from "./multi_graph";

export {
  DualLayerMemory,
} from "./dual_layer";
export type { Event, Topic } from "./dual_layer";

// v4.10.0: Graph reasoning
export {
  GraphReasoner,
} from "./graph_reasoner";
export type { PathResult, Triplet } from "./graph_reasoner";
