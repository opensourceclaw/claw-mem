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
 * MultiGraphMemory - Four orthogonal subgraph index layer.
 *
 * Organizes memory nodes into four independent graph views:
 *   - SEMANTIC: Similarity-based relationships
 *   - TEMPORAL: Time-based event sequences
 *   - CAUSAL: Cause-effect derivations
 *   - ENTITY: Entity co-occurrence
 *
 * Built on top of existing graph module's Node/Edge primitives.
 */

import { EdgeType } from "./edges.js";
import { NodeType, createNode, EpisodeNode, FactNode, ReflectionNode, ConceptNode, Node } from "./nodes.js";
import type { AnyNode, NodeDict } from "./nodes.js";

export enum SubGraphType {
  SEMANTIC = "semantic",
  TEMPORAL = "temporal",
  CAUSAL = "causal",
  ENTITY = "entity",
}

export interface GraphEdgeRecord {
  source_id: string;
  target_id: string;
  weight: number;
  edge_type: string;
  created_at: number;
}

export class SubGraph {
  name: SubGraphType;
  adjacency: Map<string, [string, number][]> = new Map();
  reverseAdjacency: Map<string, [string, number][]> = new Map();
  edgeWeights: Map<string, number> = new Map(); // "source||target" -> weight
  nodes: Set<string> = new Set();
  edgeCount: number = 0;

  constructor(name: SubGraphType) {
    this.name = name;
  }

  /** Register a node into this subgraph (idempotent). */
  addNode(nodeId: string): void {
    if (!this.nodes.has(nodeId)) {
      this.nodes.add(nodeId);
      if (!this.adjacency.has(nodeId)) {
        this.adjacency.set(nodeId, []);
      }
      if (!this.reverseAdjacency.has(nodeId)) {
        this.reverseAdjacency.set(nodeId, []);
      }
    }
  }

  /** Add an edge to this subgraph. */
  addEdge(
    source: string,
    target: string,
    weight: number = 1.0,
    directed: boolean = true,
  ): void {
    this.addNode(source);
    this.addNode(target);

    this.adjacency.get(source)!.push([target, weight]);
    if (directed) {
      this.reverseAdjacency.get(target)!.push([source, weight]);
    } else {
      this.adjacency.get(target)!.push([source, weight]);
      this.edgeWeights.set(`${target}||${source}`, weight);
    }
    this.edgeWeights.set(`${source}||${target}`, weight);
    this.edgeCount++;
  }

  /** BFS traversal to find neighbors up to max_depth. */
  getNeighbors(nodeId: string, maxDepth: number = 1): Map<string, number> {
    if (!this.nodes.has(nodeId)) return new Map();

    const visited = new Map<string, number>();
    let queue: [string, number][] = [[nodeId, 1.0]];

    for (let depth = 0; depth <= maxDepth && queue.length > 0; depth++) {
      const nextQueue: [string, number][] = [];
      for (const [current, pathWeight] of queue) {
        for (const [neighbor, weight] of this.adjacency.get(current) ?? []) {
          if (neighbor === nodeId) continue;
          const newWeight = pathWeight * weight;
          const existing = visited.get(neighbor);
          if (existing === undefined || newWeight > existing) {
            visited.set(neighbor, newWeight);
            nextQueue.push([neighbor, newWeight]);
          }
        }
      }
      queue = nextQueue;
    }

    return visited;
  }

  /** Get all outgoing edges from a node. */
  getEdgesFrom(nodeId: string): [string, number][] {
    return this.adjacency.get(nodeId) ?? [];
  }

  /** Get all incoming edges to a node. */
  getEdgesTo(nodeId: string): [string, number][] {
    return this.reverseAdjacency.get(nodeId) ?? [];
  }

  /** Check if an edge exists in O(1). */
  hasEdge(source: string, target: string): boolean {
    return this.edgeWeights.has(`${source}||${target}`);
  }

  /** Update edge weight. Returns true if edge existed. */
  updateWeight(source: string, target: string, weight: number): boolean {
    const key = `${source}||${target}`;
    if (!this.edgeWeights.has(key)) return false;

    this.edgeWeights.set(key, weight);

    // Update in adjacency
    const adj = this.adjacency.get(source);
    if (adj) {
      const idx = adj.findIndex(([n]) => n === target);
      if (idx !== -1) adj[idx] = [target, weight];
    }

    // Update in reverse adjacency
    const rev = this.reverseAdjacency.get(target);
    if (rev) {
      const idx = rev.findIndex(([n]) => n === source);
      if (idx !== -1) rev[idx] = [source, weight];
    }

    return true;
  }

  /** Serialize to JSON-compatible dictionary. */
  toDict(): Record<string, unknown> {
    const edges: Record<string, unknown>[] = [];
    for (const [key, w] of this.edgeWeights) {
      const [s, t] = key.split("||");
      edges.push({
        s,
        t,
        w: Math.round(w * 10000) / 10000,
        e: this.name,
        c: 0.0,
      });
    }
    return {
      name: this.name,
      edge_count: this.edgeCount,
      node_count: this.nodes.size,
      edges,
    };
  }

  /** Deserialize from dictionary. */
  static fromDict(d: Record<string, any>): SubGraph {
    const g = new SubGraph(d.name as SubGraphType);
    for (const e of (d.edges ?? []) as Record<string, any>[]) {
      const directed = g.name !== SubGraphType.SEMANTIC;
      g.addEdge(e.s, e.t, e.w ?? 1.0, directed);
    }
    return g;
  }

  /** Estimated memory footprint in bytes. */
  get memoryEstimate(): number {
    return this.nodes.size * 100 + this.edgeCount * 80;
  }
}

// ── Edge type -> Subgraph routing ──

export const EDGE_TO_SUBGRAPH: Record<EdgeType, SubGraphType> = {
  [EdgeType.NEXT]: SubGraphType.TEMPORAL,
  [EdgeType.DERIVED_FROM]: SubGraphType.CAUSAL,
  [EdgeType.SYNTHESIZED_FROM]: SubGraphType.CAUSAL,
  [EdgeType.RELATED_TO]: SubGraphType.SEMANTIC,
  [EdgeType.HAS_CONCEPT]: SubGraphType.ENTITY,
};

// Expansion weights for multi-graph search
export const SUBGRAPH_EXPANSION_WEIGHT: Record<SubGraphType, number> = {
  [SubGraphType.SEMANTIC]: 0.8,
  [SubGraphType.TEMPORAL]: 0.6,
  [SubGraphType.CAUSAL]: 0.5,
  [SubGraphType.ENTITY]: 0.3,
};

export class MultiGraphMemory {
  private _graphs: Map<SubGraphType, SubGraph>;
  private _nodeIndex: Map<string, AnyNode> = new Map();

  constructor() {
    this._graphs = new Map([
      [SubGraphType.SEMANTIC, new SubGraph(SubGraphType.SEMANTIC)],
      [SubGraphType.TEMPORAL, new SubGraph(SubGraphType.TEMPORAL)],
      [SubGraphType.CAUSAL, new SubGraph(SubGraphType.CAUSAL)],
      [SubGraphType.ENTITY, new SubGraph(SubGraphType.ENTITY)],
    ]);
  }

  // ── Node management ──

  /** Register a memory node in the graph (idempotent). */
  addNode(
    memoryId: string,
    content: string,
    nodeType: NodeType,
    metadata?: Record<string, unknown>,
  ): void {
    if (this._nodeIndex.has(memoryId)) return;
    const node = createNode(nodeType, content, {
      id: memoryId,
      ...(metadata ?? {}),
    });
    this._nodeIndex.set(memoryId, node);
    for (const g of this._graphs.values()) {
      g.addNode(memoryId);
    }
  }

  /** Get a node by ID. */
  getNode(memoryId: string): AnyNode | undefined {
    return this._nodeIndex.get(memoryId);
  }

  /** Total number of registered nodes. */
  nodeCount(): number {
    return this._nodeIndex.size;
  }

  // ── Edge management (with auto-routing) ──

  /** Add an edge, automatically routed to the correct subgraph. */
  addEdge(
    sourceId: string,
    targetId: string,
    edgeType: EdgeType,
    weight: number = 1.0,
  ): void {
    const subgraph = EDGE_TO_SUBGRAPH[edgeType];
    if (!subgraph) {
      throw new Error(`Unknown edge type: ${edgeType}`);
    }
    const directed = edgeType !== EdgeType.RELATED_TO;
    this._graphs.get(subgraph)!.addEdge(sourceId, targetId, weight, directed);
  }

  /** Check if any edge exists between two nodes (in any subgraph). */
  hasEdge(sourceId: string, targetId: string): boolean {
    for (const g of this._graphs.values()) {
      if (g.hasEdge(sourceId, targetId)) return true;
    }
    return false;
  }

  // ── Retrieval ──

  /** Get related node IDs from a specific subgraph. */
  getRelated(memoryId: string, subgraph: SubGraphType, limit: number = 10): string[] {
    const neighbors = this._graphs.get(subgraph)!.getNeighbors(memoryId);
    const sorted = Array.from(neighbors.entries()).sort((a, b) => b[1] - a[1]);
    return sorted.slice(0, limit).map(([nid]) => nid);
  }

  /**
   * Expand from seed nodes through specified subgraphs.
   */
  getExpandedNodes(
    nodeIds: string[],
    subgraphs?: SubGraphType[],
    maxDepth: number = 1,
    maxExpansion: number = 50,
  ): Map<string, number> {
    if (!subgraphs) {
      subgraphs = Object.values(SubGraphType);
    }

    const allNodes = new Map<string, number>();
    for (const nid of nodeIds) {
      allNodes.set(nid, 1.0);
    }

    for (const sgType of subgraphs) {
      const sg = this._graphs.get(sgType)!;
      for (const seed of nodeIds) {
        const neighbors = sg.getNeighbors(seed, maxDepth);
        for (const [nid, weight] of neighbors) {
          const existing = allNodes.get(nid);
          if (existing === undefined) {
            allNodes.set(nid, weight);
          } else {
            allNodes.set(nid, existing + weight);
          }
        }
      }
    }

    const sorted = Array.from(allNodes.entries()).sort((a, b) => b[1] - a[1]);
    return new Map(sorted.slice(0, maxExpansion));
  }

  /**
   * Multi-subgraph joint retrieval.
   */
  multiGraphSearch(semNodes: string[], k: number = 10): [string, number][] {
    const candidates = new Map<string, number>();

    // Phase 1: seed nodes
    for (const nid of semNodes) {
      candidates.set(nid, 1.0);
    }

    // Phase 2: multi-subgraph expansion
    for (const [sgType, ew] of Object.entries(SUBGRAPH_EXPANSION_WEIGHT)) {
      const sg = this._graphs.get(sgType as SubGraphType)!;
      const neighbors = new Map<string, number>();

      for (const seed of semNodes) {
        const more = sg.getNeighbors(seed, 1);
        for (const [nid, w] of more) {
          const existing = neighbors.get(nid) ?? 0;
          neighbors.set(nid, Math.max(existing, w));
        }
      }

      for (const [nid, w] of neighbors) {
        const score = w * ew;
        const existing = candidates.get(nid);
        if (existing === undefined) {
          candidates.set(nid, score);
        } else {
          candidates.set(nid, existing + score);
        }
      }
    }

    return Array.from(candidates.entries()).sort((a, b) => b[1] - a[1]).slice(0, k);
  }

  // ── Decay integration ──

  /** Batch update edge weights after decay calculation. */
  applyDecay(edgeWeights: Map<string, number>): number {
    let updated = 0;
    for (const [key, weight] of edgeWeights) {
      const [s, t] = key.split("||");
      for (const g of this._graphs.values()) {
        if (g.updateWeight(s, t, weight)) {
          updated++;
        }
      }
    }
    return updated;
  }

  /** Remove edges with weight below threshold. */
  removeExpiredEdges(threshold: number = 0.05): number {
    let removed = 0;
    for (const g of this._graphs.values()) {
      const expired: [string, string][] = [];
      for (const [key, w] of g.edgeWeights) {
        if (w < threshold) {
          const [s, t] = key.split("||");
          expired.push([s, t]);
        }
      }
      for (const [s, t] of expired) {
        g.edgeWeights.delete(`${s}||${t}`);
        const adj = g.adjacency.get(s);
        if (adj) {
          g.adjacency.set(s, adj.filter(([n]) => n !== t));
        }
        const rev = g.reverseAdjacency.get(t);
        if (rev) {
          g.reverseAdjacency.set(t, rev.filter(([n]) => n !== s));
        }
        removed++;
      }
      g.edgeCount = g.edgeWeights.size;
    }
    return removed;
  }

  // ── Statistics ──

  /** Get per-subgraph statistics. */
  getStats(): Record<string, unknown> {
    const subgraphs: Record<string, Record<string, unknown>> = {};
    for (const [type, g] of this._graphs) {
      subgraphs[type] = {
        nodes: g.nodes.size,
        edges: g.edgeCount,
        memory_bytes: g.memoryEstimate,
      };
    }
    return {
      total_nodes: this._nodeIndex.size,
      subgraphs,
    };
  }

  // ── Persistence ──

  /** Serialize to JSON-compatible dictionary. */
  toDict(): Record<string, unknown> {
    const nodes: Record<string, unknown> = {};
    for (const [nid, node] of this._nodeIndex) {
      nodes[nid] = node.toDict();
    }
    const subgraphs: Record<string, unknown> = {};
    for (const [type, g] of this._graphs) {
      subgraphs[type] = g.toDict();
    }
    return { nodes, subgraphs };
  }

  /** Deserialize from dictionary. */
  static fromDict(d: Record<string, any>): MultiGraphMemory {
    const mg = new MultiGraphMemory();
    for (const [nid, nd] of Object.entries(d.nodes ?? {})) {
      const dict = nd as NodeDict;
      let node: AnyNode;
      switch (dict.type) {
        case NodeType.EPISODE:
          node = EpisodeNode.fromDict(dict);
          break;
        case NodeType.FACT:
          node = FactNode.fromDict(dict);
          break;
        case NodeType.REFLECTION:
          node = ReflectionNode.fromDict(dict);
          break;
        case NodeType.CONCEPT:
          node = ConceptNode.fromDict(dict);
          break;
        default:
          node = Node.fromDict(dict);
          break;
      }
      mg._nodeIndex.set(nid, node);
    }
    for (const [name, sd] of Object.entries(d.subgraphs ?? {})) {
      const sgType = name as SubGraphType;
      mg._graphs.set(sgType, SubGraph.fromDict(sd as Record<string, any>));
    }
    return mg;
  }
}
