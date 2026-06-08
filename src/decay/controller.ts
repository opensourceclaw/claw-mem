// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * DecayController - Forgetting controller for graph edge decay.
 *
 * Manages the lifelong weight calculation, edge classification, and
 * cleanup of expired edges in the MultiGraphMemory.
 */

import { calculateWeight, type DecayConfig, DEFAULT_DECAY_CONFIG } from "./functions.js";

// ── External type stubs ────────────────────────────────────────────────

/**
 * Minimal subgraph interface for the parts we use from MultiGraphMemory.
 */
interface SubGraph {
  edgeWeights: Record<string, number>;
  adjacency: Record<string, Array<{ neighbor: string; weight: number }>>;
  reverseAdjacency: Record<string, Array<{ neighbor: string; weight: number }>>;
  edgeCount: number;
  hasEdge(s: string, t: string): boolean;
}

enum SubGraphType {
  TEMPORAL = "temporal",
  CAUSAL = "causal",
  SEMANTIC = "semantic",
  ENTITY = "entity",
}

interface NodeData {
  created_at?: number | Date;
  metadata?: Record<string, unknown>;
}

interface GraphMemory {
  _graphs: Record<string, SubGraph>;
  getNode(id: string): NodeData | null;
  applyDecay(updates: Record<string, number>): void;
}

// ── Controller ─────────────────────────────────────────────────────────

export class DecayController {
  private _lastDecayTime: number = 0;
  private _decayCount: number = 0;

  constructor(
    private _graph: GraphMemory,
    private _config: DecayConfig = DEFAULT_DECAY_CONFIG,
  ) {}

  // ── Weight computation ───────────────────────────────────────────────

  /** Calculate a single edge weight after decay. */
  calculateSingleWeight(initial: number, days: number, category: string): number {
    return calculateWeight(initial, days, category);
  }

  /** Compute decayed weight for a specific edge. */
  getDecayWeight(source: string, target: string, edgeType: string, createdAt: number): number {
    let currentWeight = 1.0;
    for (const g of Object.values(this._graph._graphs)) {
      const w = g.edgeWeights[`${source}\x00${target}`];
      if (w !== undefined) {
        currentWeight = w;
        break;
      }
    }
    const daysElapsed = (Date.now() / 1000 - createdAt) / 86400.0;
    const category = this._edgeTypeToCategory(edgeType);
    return calculateWeight(currentWeight, daysElapsed, category);
  }

  private _edgeTypeToCategory(edgeType: string): string {
    const mapping: Record<string, string> = {
      next: "temporal",
      derived_from: "causal",
      synthesized_from: "causal",
      related_to: "semantic",
      has_concept: "entity",
    };
    return mapping[edgeType] || "semantic";
  }

  /** Compute decay weights for all edges. Returns updates map keyed by "source\x00target". */
  computeAllDecays(): Record<string, number> {
    const updates: Record<string, number> = {};
    const now = Date.now() / 1000;

    const sgTypeToCategory: Record<string, string> = {
      [SubGraphType.TEMPORAL]: "temporal",
      [SubGraphType.CAUSAL]: "causal",
      [SubGraphType.SEMANTIC]: "semantic",
      [SubGraphType.ENTITY]: "entity",
    };

    for (const [sgType, subgraph] of Object.entries(this._graph._graphs)) {
      const category = sgTypeToCategory[sgType] || "semantic";

      for (const [key, weight] of Object.entries(subgraph.edgeWeights)) {
        const sep = key.indexOf("\x00");
        const s = key.slice(0, sep);
        const t = key.slice(sep + 1);

        const node = this._graph.getNode(s);
        let createdAt: number;
        if (node && node.created_at) {
          if (typeof node.created_at === "number") {
            createdAt = node.created_at;
          } else {
            createdAt = node.created_at.getTime() / 1000;
          }
        } else {
          createdAt = now;
        }
        const daysElapsed = (now - createdAt) / 86400.0;
        const newWeight = calculateWeight(weight, daysElapsed, category);
        if (newWeight < weight) {
          updates[key] = Math.max(0.0, Math.min(1.0, newWeight));
        }
      }
    }

    return updates;
  }

  // ── Edge classification ──────────────────────────────────────────────

  /** Classify all edges by strength tier. */
  classifyEdges(): Record<string, Array<{ source: string; target: string; weight: number }>> {
    const classified: Record<string, Array<{ source: string; target: string; weight: number }>> = {
      strong: [],
      medium: [],
      weak: [],
      expired: [],
    };

    for (const subgraph of Object.values(this._graph._graphs)) {
      for (const [key, weight] of Object.entries(subgraph.edgeWeights)) {
        const sep = key.indexOf("\x00");
        const s = key.slice(0, sep);
        const t = key.slice(sep + 1);
        const entry = { source: s, target: t, weight };

        if (weight > this._config.strongThreshold) {
          classified.strong.push(entry);
        } else if (weight > this._config.archiveThreshold) {
          classified.medium.push(entry);
        } else if (weight > this._config.expireThreshold) {
          classified.weak.push(entry);
        } else {
          classified.expired.push(entry);
        }
      }
    }

    return classified;
  }

  // ── Cleanup ──────────────────────────────────────────────────────────

  /** Decide whether an edge should be removed. */
  shouldRemoveEdge(source: string, target: string, weight: number): boolean {
    if (weight <= this._config.purgeThreshold) return true;
    if (weight <= this._config.expireThreshold) {
      if (this._config.protectCritical) {
        const node = this._graph.getNode(source);
        const meta = node?.metadata as Record<string, unknown> | undefined;
        if (node && meta?.critical) return false;
      }
      return true;
    }
    return false;
  }

  /** Remove expired edges from the graph. Returns list of removed (source, target) pairs. */
  cleanupExpired(): Array<{ source: string; target: string }> {
    const removed: Array<{ source: string; target: string }> = [];

    for (const subgraph of Object.values(this._graph._graphs)) {
      for (const [key, weight] of Object.entries(subgraph.edgeWeights)) {
        const sep = key.indexOf("\x00");
        const s = key.slice(0, sep);
        const t = key.slice(sep + 1);
        if (this.shouldRemoveEdge(s, t, weight)) {
          removed.push({ source: s, target: t });
        }
      }
    }

    if (removed.length > 0) {
      for (const { source: s, target: t } of removed) {
        for (const g of Object.values(this._graph._graphs)) {
          if (g.hasEdge(s, t)) {
            delete g.edgeWeights[`${s}\x00${t}`];
            g.adjacency[s] = (g.adjacency[s] || []).filter((n) => n.neighbor !== t);
            g.reverseAdjacency[t] = (g.reverseAdjacency[t] || []).filter((n) => n.neighbor !== s);
          }
        }
      }
      for (const g of Object.values(this._graph._graphs)) {
        g.edgeCount = Object.keys(g.edgeWeights).length;
      }
    }

    this._decayCount++;
    this._lastDecayTime = Date.now() / 1000;
    return removed;
  }

  // ── Stats ────────────────────────────────────────────────────────────

  getStats(): Record<string, unknown> {
    const classified = this.classifyEdges();
    const total =
      classified.strong.length +
      classified.medium.length +
      classified.weak.length +
      classified.expired.length;

    return {
      totalEdges: total,
      strongEdges: classified.strong.length,
      mediumEdges: classified.medium.length,
      weakEdges: classified.weak.length,
      expiredEdges: classified.expired.length,
      decayCount: this._decayCount,
      lastDecayTime: this._lastDecayTime,
      config: {
        purgeThreshold: this._config.purgeThreshold,
        expireThreshold: this._config.expireThreshold,
        decayIntervalHours: this._config.decayIntervalHours,
      },
    };
  }
}
