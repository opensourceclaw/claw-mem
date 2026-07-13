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
 * Concept-Mediated Graph - Concept-mediated knowledge graph
 *
 * Based on GAAMA paper implementation of four-node five-edge graph structure.
 *
 * Core features:
 * 1. Add conversations (auto-build graph)
 * 2. Extract facts and concepts
 * 3. Generate reflections
 * 4. Hybrid retrieval
 */

import { EdgeType, createEdge } from "../deprecated/graph/edges.js";
import type { Edge } from "../deprecated/graph/edges.js";
import { BaseExtractor, DummyExtractor } from "../deprecated/graph/extractors.js";
import { NodeType } from "../deprecated/graph/nodes.js";
import type { AnyNode } from "../deprecated/graph/nodes.js";
import { EpisodeNode, FactNode, ConceptNode, ReflectionNode } from "../deprecated/graph/nodes.js";
import { GraphStorage, InMemoryGraphStorage } from "../deprecated/graph/storage.js";

export interface RetrievalResult {
  node: AnyNode;
  score: number;
  type: string;
}

export abstract class Embedder {
  abstract embed(text: string): number[];

  call(text: string): number[] {
    return this.embed(text);
  }
}

/**
 * Dummy embedder (for testing). Uses a simple hash-based pseudo-random vector.
 * Replaces numpy's np.random.randn(dim) with Math.random() * 2 - 1 uniform approximation.
 */
export class DummyEmbedder extends Embedder {
  dimension: number;

  constructor(dimension: number = 384) {
    super();
    this.dimension = dimension;
  }

  embed(text: string): number[] {
    // Simple hash-based seed
    let seed = 0;
    for (let i = 0; i < text.length; i++) {
      seed = ((seed << 5) - seed + text.charCodeAt(i)) | 0;
    }
    // Pseudo-random generator seeded by hash
    const s = Math.abs(seed % 2147483647) || 1;
    const vec: number[] = [];
    let state = s;
    for (let i = 0; i < this.dimension; i++) {
      state = (state * 16807) % 2147483647;
      vec.push((state / 2147483647) * 2 - 1);
    }
    // Normalize
    const norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0));
    return vec.map((v) => v / (norm || 1));
  }
}

function cosineSimilarity(a: number[], b: number[]): number {
  const dot = a.reduce((sum, v, i) => sum + v * (b[i] || 0), 0);
  const normA = Math.sqrt(a.reduce((sum, v) => sum + v * v, 0));
  const normB = Math.sqrt(b.reduce((sum, v) => sum + v * v, 0));
  return dot / (normA * normB || 1);
}

import { randomUUID } from 'crypto';

function generateId(): string {
  // Use crypto.randomUUID for secure ID generation
  return randomUUID();
}

export class ConceptMediatedGraph {
  storage: GraphStorage;
  embedder: Embedder | null;
  extractor: BaseExtractor;

  constructor(
    storage?: GraphStorage,
    embedder?: Embedder | null,
    extractor?: BaseExtractor,
  ) {
    this.storage = storage ?? new InMemoryGraphStorage();
    this.embedder = embedder ?? null;
    this.extractor = extractor ?? new DummyExtractor();
  }

  /**
   * Add conversation turns, auto-build graph.
   *
   * Flow:
   * 1. Create Episode nodes
   * 2. Extract Fact nodes (if extractor available)
   * 3. Extract Concept nodes (if extractor available)
   * 4. Establish edge relationships
   */
  addConversation(
    turns: { speaker?: string; content: string; timestamp?: Date }[],
    sessionId?: string,
  ): string[] {
    const episodeIds: string[] = [];
    sessionId = sessionId ?? generateId();

    // Step 1: Create Episode nodes
    for (let i = 0; i < turns.length; i++) {
      const turn = turns[i];
      const episode = new EpisodeNode(
        generateId(),
        turn.content,
        i,
        turn.speaker ?? "unknown",
        turn.timestamp ?? null,
        sessionId,
      );

      // Compute embedding
      if (this.embedder) {
        try {
          episode.embedding = this.embedder.embed(episode.content);
        } catch {
          // ignore
        }
      }

      this.storage.saveNode(episode);
      episodeIds.push(episode.id);

      // Create NEXT edge
      if (i > 0) {
        const edge = createEdge(EdgeType.NEXT, episodeIds[i - 1], episode.id);
        this.storage.saveEdge(edge);
      }
    }

    // Step 2: Extract Fact nodes
    const facts = this.extractFacts(turns);
    for (const factContent of facts) {
      const fact = new FactNode(
        generateId(),
        factContent,
        0.8,
        episodeIds[0] ?? null,
      );

      if (this.embedder) {
        try {
          fact.embedding = this.embedder.embed(fact.content);
        } catch {
          // ignore
        }
      }

      this.storage.saveNode(fact);

      // Create DERIVED_FROM edges
      for (const epId of episodeIds) {
        const edge = createEdge(EdgeType.DERIVED_FROM, fact.id, epId);
        this.storage.saveEdge(edge);
      }
    }

    // Step 3: Extract Concept nodes
    const concepts = this.extractConcepts(turns);
    for (const conceptContent of concepts) {
      const existing = this.findConcept(conceptContent);
      let concept: ConceptNode;
      if (existing) {
        existing.frequency += 1;
        concept = existing;
      } else {
        concept = new ConceptNode(generateId(), conceptContent);
        if (this.embedder) {
          try {
            concept.embedding = this.embedder.embed(concept.content);
          } catch {
            // ignore
          }
        }
        this.storage.saveNode(concept);
      }

      // Create HAS_CONCEPT edges
      for (const epId of episodeIds) {
        const edge = createEdge(EdgeType.HAS_CONCEPT, epId, concept.id);
        this.storage.saveEdge(edge);
      }
    }

    return episodeIds;
  }

  /** Add a single episode */
  addEpisode(
    content: string,
    speaker: string = "unknown",
    metadata?: Record<string, unknown>,
  ): string {
    const id = generateId();
    const episode = new EpisodeNode(id, content, 0, speaker, null, null, null, metadata ?? {});

    if (this.embedder) {
      try {
        episode.embedding = this.embedder.embed(episode.content);
      } catch {
        // ignore
      }
    }

    this.storage.saveNode(episode);
    return episode.id;
  }

  /** Add fact node */
  addFact(
    content: string,
    sourceEpisodeId?: string | null,
    confidence: number = 1.0,
  ): string {
    const id = generateId();
    const fact = new FactNode(id, content, confidence, sourceEpisodeId ?? null);

    if (this.embedder) {
      try {
        fact.embedding = this.embedder.embed(fact.content);
      } catch {
        // ignore
      }
    }

    this.storage.saveNode(fact);

    if (sourceEpisodeId) {
      const edge = createEdge(EdgeType.DERIVED_FROM, fact.id, sourceEpisodeId);
      this.storage.saveEdge(edge);
    }

    return fact.id;
  }

  /** Add concept node */
  addConcept(content: string, category: string = "general"): string {
    const existing = this.findConcept(content);
    if (existing) {
      existing.frequency += 1;
      return existing.id;
    }

    const id = generateId();
    const concept = new ConceptNode(id, content, category);

    if (this.embedder) {
      try {
        concept.embedding = this.embedder.embed(concept.content);
      } catch {
        // ignore
      }
    }

    this.storage.saveNode(concept);
    return concept.id;
  }

  /** Add reflection node */
  addReflection(
    content: string,
    sourceNodeIds: string[],
    summaryType: string = "general",
  ): string {
    const id = generateId();
    const reflection = new ReflectionNode(
      id,
      content,
      summaryType,
      sourceNodeIds,
    );

    if (this.embedder) {
      try {
        reflection.embedding = this.embedder.embed(reflection.content);
      } catch {
        // ignore
      }
    }

    this.storage.saveNode(reflection);

    // Create source edges
    for (const sourceId of sourceNodeIds) {
      const edge = createEdge(EdgeType.SYNTHESIZED_FROM, reflection.id, sourceId);
      this.storage.saveEdge(edge);
    }

    return reflection.id;
  }

  /**
   * Hybrid retrieval.
   *
   * @param query Query text
   * @param k Number of results
   * @param alpha Semantic retrieval weight (0-1). 1=pure semantic, 0=pure PPR, 0.5=hybrid
   * @param nodeTypes Filter by node types (optional)
   */
  retrieve(
    query: string,
    k: number = 10,
    alpha: number = 0.5,
    nodeTypes?: NodeType[],
  ): RetrievalResult[] {
    // Compute query embedding
    let queryEmbedding: number[] | null = null;
    if (alpha > 0 && this.embedder) {
      try {
        queryEmbedding = this.embedder.embed(query);
      } catch {
        // ignore
      }
    }

    // Get all nodes
    let allNodes = this.storage.getAllNodes();
    if (nodeTypes) {
      const typeSet = new Set(nodeTypes);
      allNodes = allNodes.filter((n) => typeSet.has(n.type));
    }

    // Semantic scores
    const semanticScores = new Map<string, number>();
    if (queryEmbedding) {
      for (const node of allNodes) {
        if (node.embedding) {
          const score = cosineSimilarity(queryEmbedding, node.embedding);
          semanticScores.set(node.id, score);
        }
      }
    }

    // PPR scores (simplified: based on node degree)
    const pprScores = new Map<string, number>();
    if (alpha < 1) {
      const degreeDict = this.computePprScores(allNodes);
      const maxDegree =
        degreeDict.size > 0 ? Math.max(...degreeDict.values(), 1) : 1;
      for (const [nodeId, degree] of degreeDict) {
        pprScores.set(nodeId, degree / maxDegree);
      }
    }

    // Hybrid scores
    const finalScores = new Map<string, number>();
    for (const node of allNodes) {
      const semantic = semanticScores.get(node.id) ?? 0;
      const ppr = pprScores.get(node.id) ?? 0;
      finalScores.set(node.id, alpha * semantic + (1 - alpha) * ppr);
    }

    // Sort and return
    const sorted = Array.from(finalScores.entries()).sort(
      (a, b) => b[1] - a[1],
    );

    const results: RetrievalResult[] = [];
    for (const [nodeId, score] of sorted.slice(0, k)) {
      const node = this.storage.getNode(nodeId);
      if (node) {
        results.push({ node, score, type: node.type });
      }
    }

    return results;
  }

  /** Get a single node by ID */
  getNode(nodeId: string): AnyNode | undefined {
    return this.storage.getNode(nodeId);
  }

  /** Get neighbor nodes */
  getNeighbors(nodeId: string): AnyNode[] {
    const neighborIds = this.storage.getNeighbors(nodeId);
    const result: AnyNode[] = [];
    for (const nid of neighborIds) {
      const n = this.storage.getNode(nid);
      if (n) result.push(n);
    }
    return result;
  }

  /** Get statistics */
  getStats(): Record<string, unknown> {
    const s = this.storage as any;
    if (typeof s.getStats === "function") {
      return s.getStats();
    }
    return {
      total_nodes: this.storage.getAllNodes().length,
      total_edges: this.storage.getAllEdges().length,
    };
  }

  // ── Internal helpers ──

  private extractFacts(turns: { content: string }[]): string[] {
    if (!this.extractor) return [];
    try {
      const text = turns.map((t) => t.content).join("\n");
      return this.extractor.extractFacts(text);
    } catch {
      return [];
    }
  }

  private extractConcepts(turns: { content: string }[]): string[] {
    if (!this.extractor) return [];
    try {
      const text = turns.map((t) => t.content).join("\n");
      return this.extractor.extractConcepts(text);
    } catch {
      return [];
    }
  }

  private findConcept(content: string): ConceptNode | undefined {
    const concepts = this.storage.getNodesByType(NodeType.CONCEPT);
    for (const node of concepts) {
      if (node instanceof ConceptNode && node.content === content) {
        return node;
      }
    }
    return undefined;
  }

  private computePprScores(nodes: AnyNode[]): Map<string, number> {
    const scores = new Map<string, number>();
    for (const node of nodes) {
      const neighbors = this.storage.getNeighbors(node.id);
      let score = neighbors.size;
      if (node.type === NodeType.CONCEPT && node instanceof ConceptNode) {
        score *= 1 + node.frequency * 0.1;
      }
      scores.set(node.id, score);
    }
    return scores;
  }
}
