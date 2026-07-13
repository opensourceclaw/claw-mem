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
} from "./nodes.js";
export type { NodeDict, AnyNode } from "./nodes.js";

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
} from "./edges.js";
export type { EdgeDict, AnyEdge } from "./edges.js";

// Storage
export {
  GraphStorage,
  InMemoryGraphStorage,
  FileGraphStorage,
} from "./storage.js";

// Core
export {
  ConceptMediatedGraph,
  RetrievalResult,
  Embedder,
  DummyEmbedder,
} from "../../graph/concept_graph.js";

// Extractors
export {
  BaseExtractor,
  LLMExtractor,
  DummyExtractor,
  KeywordExtractor,
} from "./extractors.js";
export type { LLMClient } from "./extractors.js";

// v2.14.0: MultiGraph + DualLayer
export {
  SubGraphType,
  SubGraph,
  MultiGraphMemory,
  EDGE_TO_SUBGRAPH,
  SUBGRAPH_EXPANSION_WEIGHT,
} from "./multi_graph.js";
export type { GraphEdgeRecord } from "./multi_graph.js";

export {
  DualLayerMemory,
} from "./dual_layer.js";
export type { Event, Topic } from "./dual_layer.js";

// v4.10.0: Graph reasoning
export {
  GraphReasoner,
} from "./graph_reasoner.js";
export type { PathResult, Triplet } from "./graph_reasoner.js";
