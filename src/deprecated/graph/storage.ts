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
 * Graph Storage - Concept-mediated graph storage layer
 *
 * Supports:
 * - In-memory storage (InMemoryGraphStorage)
 * - File persistence (FileGraphStorage)
 */

import * as fs from "fs";
import * as path from "path";
import { Edge, EdgeDict } from "./edges.js";
import type { NodeDict } from "./nodes.js";
import { NodeType } from "./nodes.js";
import { AnyNode, Node, EpisodeNode, FactNode, ReflectionNode, ConceptNode } from "./nodes.js";

export abstract class GraphStorage {
  abstract saveNode(node: AnyNode): void;
  abstract getNode(nodeId: string): AnyNode | undefined;
  abstract deleteNode(nodeId: string): boolean;
  abstract getAllNodes(): AnyNode[];
  abstract getNodesByType(nodeType: NodeType): AnyNode[];
  abstract saveEdge(edge: Edge): void;
  abstract getEdge(sourceId: string, targetId: string): Edge | undefined;
  abstract deleteEdge(sourceId: string, targetId: string): boolean;
  abstract getAllEdges(): Edge[];
  abstract getEdgesFrom(nodeId: string): Edge[];
  abstract getEdgesTo(nodeId: string): Edge[];
  abstract getNeighbors(nodeId: string): Set<string>;
  abstract clear(): void;
}

/** Reconstruct a typed node from a NodeDict. */
function nodeFromDict(data: NodeDict): AnyNode {
  switch (data.type) {
    case NodeType.EPISODE:
      return EpisodeNode.fromDict(data);
    case NodeType.FACT:
      return FactNode.fromDict(data);
    case NodeType.REFLECTION:
      return ReflectionNode.fromDict(data);
    case NodeType.CONCEPT:
      return ConceptNode.fromDict(data);
    default:
      return Node.fromDict(data);
  }
}

export class InMemoryGraphStorage extends GraphStorage {
  protected _nodes: Map<string, AnyNode> = new Map();
  protected _edges: Map<string, Edge[]> = new Map(); // source_id -> edges
  protected _reverseEdges: Map<string, Edge[]> = new Map(); // target_id -> edges
  protected _nodeTypes: Map<NodeType, Set<string>> = new Map([
    [NodeType.EPISODE, new Set()],
    [NodeType.FACT, new Set()],
    [NodeType.REFLECTION, new Set()],
    [NodeType.CONCEPT, new Set()],
  ]);

  saveNode(node: AnyNode): void {
    this._nodes.set(node.id, node);
    const s = this._nodeTypes.get(node.type);
    if (s) {
      s.add(node.id);
    }
  }

  getNode(nodeId: string): AnyNode | undefined {
    return this._nodes.get(nodeId);
  }

  deleteNode(nodeId: string): boolean {
    const node = this._nodes.get(nodeId);
    if (!node) return false;

    this._nodes.delete(nodeId);
    this._nodeTypes.get(node.type)?.delete(nodeId);

    // Delete outgoing edges
    const outgoing = this._edges.get(nodeId);
    if (outgoing) {
      for (const edge of outgoing) {
        const rev = this._reverseEdges.get(edge.target_id);
        if (rev) {
          this._reverseEdges.set(
            edge.target_id,
            rev.filter((e) => e.source_id !== nodeId),
          );
        }
      }
      this._edges.delete(nodeId);
    }

    // Delete incoming edges
    const incoming = this._reverseEdges.get(nodeId);
    if (incoming) {
      for (const edge of incoming) {
        const fwd = this._edges.get(edge.source_id);
        if (fwd) {
          this._edges.set(
            edge.source_id,
            fwd.filter((e) => e.target_id !== nodeId),
          );
        }
      }
      this._reverseEdges.delete(nodeId);
    }

    return true;
  }

  getAllNodes(): AnyNode[] {
    return Array.from(this._nodes.values());
  }

  getNodesByType(nodeType: NodeType): AnyNode[] {
    const ids = this._nodeTypes.get(nodeType);
    if (!ids) return [];
    const result: AnyNode[] = [];
    for (const id of ids) {
      const n = this._nodes.get(id);
      if (n) result.push(n);
    }
    return result;
  }

  saveEdge(edge: Edge): void {
    if (!this._edges.has(edge.source_id)) {
      this._edges.set(edge.source_id, []);
    }
    this._edges.get(edge.source_id)!.push(edge);

    if (!this._reverseEdges.has(edge.target_id)) {
      this._reverseEdges.set(edge.target_id, []);
    }
    this._reverseEdges.get(edge.target_id)!.push(edge);
  }

  getEdge(sourceId: string, targetId: string): Edge | undefined {
    const edges = this._edges.get(sourceId);
    if (!edges) return undefined;
    return edges.find((e) => e.target_id === targetId);
  }

  deleteEdge(sourceId: string, targetId: string): boolean {
    const edges = this._edges.get(sourceId);
    if (!edges) return false;
    const idx = edges.findIndex((e) => e.target_id === targetId);
    if (idx === -1) return false;
    edges.splice(idx, 1);

    const rev = this._reverseEdges.get(targetId);
    if (rev) {
      this._reverseEdges.set(
        targetId,
        rev.filter((e) => e.source_id !== sourceId),
      );
    }
    return true;
  }

  getAllEdges(): Edge[] {
    const result: Edge[] = [];
    for (const edges of this._edges.values()) {
      result.push(...edges);
    }
    return result;
  }

  getEdgesFrom(nodeId: string): Edge[] {
    return this._edges.get(nodeId) ?? [];
  }

  getEdgesTo(nodeId: string): Edge[] {
    return this._reverseEdges.get(nodeId) ?? [];
  }

  getNeighbors(nodeId: string): Set<string> {
    const neighbors = new Set<string>();
    for (const edge of this._edges.get(nodeId) ?? []) {
      neighbors.add(edge.target_id);
    }
    for (const edge of this._reverseEdges.get(nodeId) ?? []) {
      neighbors.add(edge.source_id);
    }
    return neighbors;
  }

  getStats(): Record<string, number> {
    return {
      total_nodes: this._nodes.size,
      total_edges: this.getAllEdges().length,
      episodes: this._nodeTypes.get(NodeType.EPISODE)?.size ?? 0,
      facts: this._nodeTypes.get(NodeType.FACT)?.size ?? 0,
      reflections: this._nodeTypes.get(NodeType.REFLECTION)?.size ?? 0,
      concepts: this._nodeTypes.get(NodeType.CONCEPT)?.size ?? 0,
    };
  }

  clear(): void {
    this._nodes.clear();
    this._edges.clear();
    this._reverseEdges.clear();
    for (const s of this._nodeTypes.values()) {
      s.clear();
    }
  }
}

export class FileGraphStorage extends InMemoryGraphStorage {
  filePath: string;

  constructor(filePath: string = "graph.json") {
    super();
    this.filePath = filePath;
    this.load();
  }

  private load(): void {
    if (!fs.existsSync(this.filePath)) return;

    try {
      const raw = fs.readFileSync(this.filePath, "utf-8");
      const data = JSON.parse(raw) as { nodes?: NodeDict[]; edges?: EdgeDict[] };

      for (const nd of data.nodes ?? []) {
        const node = nodeFromDict(nd);
        this._nodes.set(node.id, node);
        this._nodeTypes.get(node.type)?.add(node.id);
      }

      for (const ed of data.edges ?? []) {
        const edge = Edge.fromDict(ed);
        if (!this._edges.has(edge.source_id)) {
          this._edges.set(edge.source_id, []);
        }
        this._edges.get(edge.source_id)!.push(edge);
        if (!this._reverseEdges.has(edge.target_id)) {
          this._reverseEdges.set(edge.target_id, []);
        }
        this._reverseEdges.get(edge.target_id)!.push(edge);
      }
    } catch (e) {
      console.error(`Failed to load graph from ${this.filePath}:`, e);
    }
  }

  save(): void {
    const data = {
      nodes: Array.from(this._nodes.values()).map((n) => n.toDict()),
      edges: this.getAllEdges().map((e) => e.toDict()),
      saved_at: new Date().toISOString(),
    };

    const dir = path.dirname(this.filePath);
    if (dir && !fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    fs.writeFileSync(this.filePath, JSON.stringify(data, null, 2), "utf-8");
  }

  saveNode(node: AnyNode): void {
    super.saveNode(node);
    this.save();
  }

  saveEdge(edge: Edge): void {
    super.saveEdge(edge);
    this.save();
  }

  deleteNode(nodeId: string): boolean {
    const result = super.deleteNode(nodeId);
    if (result) this.save();
    return result;
  }
}
