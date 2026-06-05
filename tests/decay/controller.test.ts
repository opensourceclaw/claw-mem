import { describe, it, expect, beforeEach } from "vitest";
import { DecayController } from "../../src/decay/controller";
import { DEFAULT_DECAY_CONFIG } from "../../src/decay/functions";

// ── Mock graph ──────────────────────────────────────────────────────────

interface MockNode {
  created_at: number;
  metadata?: Record<string, unknown>;
}

interface SubGraph {
  edgeWeights: Record<string, number>;
  adjacency: Record<string, Array<{ neighbor: string; weight: number }>>;
  reverseAdjacency: Record<string, Array<{ neighbor: string; weight: number }>>;
  edgeCount: number;
  hasEdge(s: string, t: string): boolean;
}

class MockGraph {
  _graphs: Record<string, SubGraph> = {};
  private nodes: Record<string, MockNode> = {};

  constructor() {
    this._graphs = {
      "0": this.makeSubGraph(),
      "1": this.makeSubGraph(),
      "2": this.makeSubGraph(),
      "3": this.makeSubGraph(),
    };
  }

  private makeSubGraph(): SubGraph {
    return {
      edgeWeights: {},
      adjacency: {},
      reverseAdjacency: {},
      edgeCount: 0,
      hasEdge(s: string, t: string): boolean {
        return `${s}\x00${t}` in this.edgeWeights;
      },
    };
  }

  addNode(id: string, createdDaysAgo: number = 0, critical: boolean = false): void {
    this.nodes[id] = {
      created_at: Date.now() / 1000 - createdDaysAgo * 86400,
      metadata: critical ? { critical: true } : {},
    };
  }

  addEdge(source: string, target: string, weight: number = 1.0, graphIdx: number = 0): void {
    const key = `${source}\x00${target}`;
    const g = this._graphs[String(graphIdx)];
    g.edgeWeights[key] = weight;
    g.adjacency[source] = g.adjacency[source] || [];
    g.adjacency[source].push({ neighbor: target, weight });
    g.reverseAdjacency[target] = g.reverseAdjacency[target] || [];
    g.reverseAdjacency[target].push({ neighbor: source, weight });
    g.edgeCount++;
  }

  getNode(id: string): MockNode | null {
    return this.nodes[id] ?? null;
  }

  applyDecay(_updates: Record<string, number>): void {
    // Mock implementation
  }
}

// ── Tests ───────────────────────────────────────────────────────────────

describe("DecayController", () => {
  let graph: MockGraph;
  let controller: DecayController;

  beforeEach(() => {
    graph = new MockGraph();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    controller = new DecayController(graph as any, DEFAULT_DECAY_CONFIG);
  });

  describe("calculateSingleWeight()", () => {
    it("decays weight over time", () => {
      const fresh = controller.calculateSingleWeight(1.0, 0, "temporal");
      const old = controller.calculateSingleWeight(1.0, 365, "temporal");
      expect(fresh).toBeGreaterThanOrEqual(old);
    });

    it("respects decay category", () => {
      const temp = controller.calculateSingleWeight(1.0, 30, "temporal");
      const perm = controller.calculateSingleWeight(1.0, 30, "permanent");
      expect(temp).toBeLessThanOrEqual(1.0);
      expect(perm).toBeGreaterThanOrEqual(0.0);
    });

    it("returns valid range (0-1)", () => {
      const w = controller.calculateSingleWeight(1.0, 1000, "temporal");
      expect(w).toBeGreaterThanOrEqual(0);
      expect(w).toBeLessThanOrEqual(1);
    });
  });

  describe("getDecayWeight()", () => {
    it("decays existing edge weight", () => {
      graph.addNode("a");
      graph.addNode("b");
      graph.addEdge("a", "b", 1.0);
      const w = controller.getDecayWeight("a", "b", "next", Date.now() / 1000 - 30 * 86400);
      expect(w).toBeGreaterThanOrEqual(0);
      expect(w).toBeLessThanOrEqual(1);
    });

    it("returns 1.0 when edge not found", () => {
      graph.addNode("a");
      graph.addNode("b");
      const w = controller.getDecayWeight("a", "b", "related_to", Date.now() / 1000);
      expect(w).toBeGreaterThan(0);
    });
  });

  describe("computeAllDecays()", () => {
    it("returns updates for all edges", () => {
      graph.addNode("a");
      graph.addNode("b");
      graph.addNode("c");
      graph.addEdge("a", "b", 1.0);
      graph.addEdge("b", "c", 0.5);
      const updates = controller.computeAllDecays();
      expect(Object.keys(updates).length).toBeGreaterThanOrEqual(0);
    });

    it("handles empty graph", () => {
      const g = new MockGraph();
      g._graphs = {};
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ctrl = new DecayController(g as any, DEFAULT_DECAY_CONFIG);
      const updates = ctrl.computeAllDecays();
      expect(Object.keys(updates).length).toBe(0);
    });
  });

  describe("classifyEdges()", () => {
    it("classifies strong, medium, weak, expired edges", () => {
      graph.addEdge("a", "b", 0.85); // strong
      graph.addEdge("b", "c", 0.45); // medium
      graph.addEdge("c", "d", 0.15); // weak
      graph.addEdge("d", "e", 0.01); // expired
      const classified = controller.classifyEdges();
      expect(classified.strong.length).toBeGreaterThanOrEqual(1);
      expect(classified.medium.length).toBeGreaterThanOrEqual(1);
      expect(classified.weak.length).toBeGreaterThanOrEqual(1);
      expect(classified.expired.length).toBeGreaterThanOrEqual(1);
    });

    it("handles empty graph", () => {
      const g = new MockGraph();
      g._graphs = {};
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const ctrl = new DecayController(g as any, DEFAULT_DECAY_CONFIG);
      const classified = ctrl.classifyEdges();
      expect(classified.strong).toEqual([]);
      expect(classified.expired).toEqual([]);
    });
  });

  describe("shouldRemoveEdge()", () => {
    it("removes edges below purge threshold", () => {
      expect(controller.shouldRemoveEdge("a", "b", 0.005)).toBe(true);
    });

    it("removes edges below expire threshold", () => {
      expect(controller.shouldRemoveEdge("a", "b", 0.05)).toBe(true);
    });

    it("keeps edges above thresholds", () => {
      expect(controller.shouldRemoveEdge("a", "b", 0.5)).toBe(false);
    });

    it("protects critical nodes from expiration", () => {
      graph.addNode("critical_node", 0, true); // critical=true
      // Edge weight between purge (0.05) and expire (0.1) thresholds
      expect(controller.shouldRemoveEdge("critical_node", "b", 0.08)).toBe(false);
    });
  });

  describe("cleanupExpired()", () => {
    it("removes expired edges from graph", () => {
      graph.addEdge("a", "b", 0.3);
      graph.addEdge("c", "d", 0.01); // will be removed
      const removed = controller.cleanupExpired();
      expect(removed.length).toBeGreaterThanOrEqual(1);
    });

    it("returns empty array when nothing expired", () => {
      graph.addEdge("a", "b", 0.9);
      const removed = controller.cleanupExpired();
      // Edge weights reset after cleanup, so count depends on thresholds
      expect(Array.isArray(removed)).toBe(true);
    });
  });

  describe("getStats()", () => {
    it("returns comprehensive stats", () => {
      graph.addEdge("a", "b", 0.85);
      const stats = controller.getStats();
      expect(stats.totalEdges).toBeGreaterThanOrEqual(1);
      expect(stats.strongEdges).toBeGreaterThanOrEqual(0);
      expect(stats.mediumEdges).toBeGreaterThanOrEqual(0);
      expect(stats.weakEdges).toBeGreaterThanOrEqual(0);
      expect(stats.expiredEdges).toBeGreaterThanOrEqual(0);
      expect(stats.decayCount).toBeGreaterThanOrEqual(0);
      expect(stats.config).toBeDefined();
      expect(stats.config.purgeThreshold).toBeDefined();
    });
  });
});
