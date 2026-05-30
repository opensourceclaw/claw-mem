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
 * Graph Reasoner (v4.10.0)
 *
 * Multi-hop reasoning over knowledge triplets. Maintains an independent
 * adjacency list compatible with ConceptMediatedGraph nodes but not
 * tightly coupled.
 *
 * Supports:
 * - Path finding (BFS shortest + DFS all paths, cycle-aware)
 * - Related node discovery
 * - Node importance scoring (frequency centrality + connectivity)
 */

export interface PathResult {
  /** Ordered list of (node, predicate, node) tuples. */
  path: [string, string, string][];
  /** Number of edges in the path. */
  length: number;
  /** Aggregate confidence along the path. */
  confidence: number;
}

export interface Triplet {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
}

export class GraphReasoner {
  /** Adjacency: {node_id -> [(predicate, target_node_id, confidence)]} */
  private _graph: Map<string, [string, string, number][]> = new Map();
  /** Reverse adjacency for in-degree computation */
  private _reverse: Map<string, [string, string, number][]> = new Map();

  private static normalize(name: string): string {
    return name.trim().toLowerCase();
  }

  // ── Graph Construction ──

  /** Add a single triplet edge to the graph. */
  addTriplet(
    subj: string,
    pred: string,
    obj: string,
    confidence: number = 0.8,
  ): void {
    const s = GraphReasoner.normalize(subj);
    const o = GraphReasoner.normalize(obj);

    const sEdges = this._graph.get(s) ?? [];
    sEdges.push([pred, o, confidence]);
    this._graph.set(s, sEdges);

    const oRev = this._reverse.get(o) ?? [];
    oRev.push([pred, s, confidence]);
    this._reverse.set(o, oRev);

    // Ensure all nodes appear as keys
    if (!this._graph.has(o)) {
      this._graph.set(o, []);
    }
    if (!this._reverse.has(s)) {
      this._reverse.set(s, []);
    }
  }

  /** Batch-add triplets from a list of Triplet objects. */
  addTriplets(triplets: Triplet[]): void {
    for (const t of triplets) {
      this.addTriplet(t.subject, t.predicate, t.object, t.confidence);
    }
  }

  // ── Path Finding ──

  /**
   * Find paths from source to target.
   * Uses BFS for shortest path first, then DFS for additional paths
   * up to max_depth. Avoids cycles.
   */
  findPaths(
    source: string,
    target: string,
    maxDepth: number = 3,
  ): PathResult[] {
    const s = GraphReasoner.normalize(source);
    const t = GraphReasoner.normalize(target);

    if (!this._graph.has(s) || !this._graph.has(t)) {
      return [];
    }

    const results: PathResult[] = [];

    // BFS for shortest path
    const shortest = this.bfsShortest(s, t, maxDepth);
    if (shortest) {
      results.push(shortest);
    }

    // DFS for additional paths (skip the BFS-found path)
    const bfsKey = shortest
      ? shortest.path.map(([h, p, r]) => `${h}||${p}||${r}`).join("|")
      : null;

    const dfsPaths = this.dfsAll(s, t, maxDepth);
    for (const path of dfsPaths) {
      const pk = path.map(([h, p, r]) => `${h}||${p}||${r}`).join("|");
      if (pk !== bfsKey) {
        const length = path.length;
        const conf = this.pathConfidence(path);
        results.push({ path, length, confidence: conf });
      }
    }

    return results;
  }

  /** BFS to find the shortest path. */
  private bfsShortest(
    source: string,
    target: string,
    maxDepth: number,
  ): PathResult | null {
    type QueueItem = [string, [string, string, string, number][]];
    const queue: QueueItem[] = [[source, []]];
    const visited = new Set<string>([source]);

    while (queue.length > 0) {
      const [node, pathSoFar] = queue.shift()!;
      if (pathSoFar.length >= maxDepth) continue;

      for (const [pred, neighbor, conf] of this._graph.get(node) ?? []) {
        const newPath = [...pathSoFar, [node, pred, neighbor, conf] as [string, string, string, number]];
        if (neighbor === target) {
          const steps: [string, string, string][] = newPath.map(
            ([s, p, o]) => [s, p, o],
          );
          const totalConf = GraphReasoner.computeConfidence(newPath);
          return { path: steps, length: steps.length, confidence: totalConf };
        }
        if (!visited.has(neighbor)) {
          visited.add(neighbor);
          queue.push([neighbor, newPath]);
        }
      }
    }

    return null;
  }

  /** DFS to find all paths up to maxDepth, avoiding cycles. */
  private dfsAll(
    source: string,
    target: string,
    maxDepth: number,
  ): [string, string, string][][] {
    type StackItem = [string, [string, string, string][], Set<string>];
    const result: [string, string, string][][] = [];
    const stack: StackItem[] = [[source, [], new Set([source])]];

    while (stack.length > 0) {
      const [node, path, visited] = stack.pop()!;
      if (path.length >= maxDepth) continue;

      for (const [pred, neighbor] of this._graph.get(node) ?? []) {
        if (visited.has(neighbor)) continue;
        const newPath = [...path, [node, pred, neighbor] as [string, string, string]];
        if (neighbor === target) {
          result.push(newPath);
        } else {
          const newVisited = new Set(visited);
          newVisited.add(neighbor);
          stack.push([neighbor, newPath, newVisited]);
        }
      }
    }

    return result;
  }

  /** Compute aggregate confidence for a path using edge confidence values. */
  private pathConfidence(path: [string, string, string][]): number {
    if (path.length === 0) return 0.0;
    const confs: number[] = [];
    for (const [s, , o] of path) {
      let found = false;
      for (const [, neighbor, c] of this._graph.get(s) ?? []) {
        if (neighbor === o) {
          confs.push(c);
          found = true;
          break;
        }
      }
      if (!found) confs.push(0.5); // fallback
    }
    return GraphReasoner.computeConfidenceConfs(confs);
  }

  /** Product of edge confidences, with length penalty. */
  private static computeConfidence(
    pathWithConf: [string, string, string, number][],
  ): number {
    if (pathWithConf.length === 0) return 0.0;
    let product = 1.0;
    for (const [, , , c] of pathWithConf) {
      product *= c;
    }
    return Math.round(product * 10000) / 10000;
  }

  /** Product of confidence values with length penalty. */
  private static computeConfidenceConfs(confs: number[]): number {
    if (confs.length === 0) return 0.0;
    let product = 1.0;
    for (const c of confs) {
      product *= c;
    }
    return Math.round(product * 10000) / 10000;
  }

  // ── Related Nodes ──

  /** Find all nodes reachable from source within maxDepth hops. */
  findRelated(source: string, maxDepth: number = 2): string[] {
    const s = GraphReasoner.normalize(source);
    if (!this._graph.has(s)) return [];

    const visited = new Set<string>([s]);
    let frontier = new Set<string>([s]);
    const related: string[] = [];

    for (let depth = 0; depth < maxDepth; depth++) {
      const nextFrontier = new Set<string>();
      for (const node of frontier) {
        for (const [, neighbor] of this._graph.get(node) ?? []) {
          if (!visited.has(neighbor)) {
            visited.add(neighbor);
            related.push(neighbor);
            nextFrontier.add(neighbor);
          }
        }
      }
      frontier = nextFrontier;
      if (frontier.size === 0) break;
    }

    return related;
  }

  // ── Node Importance ──

  /** Compute normalized node importance scores (0.0-1.0). */
  nodeImportance(): Map<string, number> {
    if (this._graph.size === 0) return new Map();

    const degrees = new Map<string, number>();

    for (const node of this._graph.keys()) {
      const outD = this._graph.get(node)?.length ?? 0;
      const inD = this._reverse.get(node)?.length ?? 0;
      degrees.set(node, inD + outD);
    }

    const maxDeg = Math.max(...degrees.values(), 1);
    if (maxDeg === 0) {
      const result = new Map<string, number>();
      for (const node of this._graph.keys()) {
        result.set(node, 0.0);
      }
      return result;
    }

    const result = new Map<string, number>();
    for (const [node, d] of degrees) {
      result.set(node, Math.round((d / maxDeg) * 10000) / 10000);
    }
    return result;
  }
}
