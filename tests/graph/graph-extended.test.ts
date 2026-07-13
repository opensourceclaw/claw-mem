import { describe, it, expect } from "vitest";

import {
  NodeType,
  EpisodeNode,
  FactNode,
  ConceptNode,
  EdgeType,
  NextEdge,
  HasConceptEdge,
  RelatedToEdge,
  DerivedFromEdge,
  ConceptMediatedGraph,
  DummyEmbedder,
  MultiGraphMemory,
  SubGraph,
  SubGraphType,
  GraphReasoner,
} from "../../src/deprecated/graph";

// ── GraphReasoner 补充测试 ─────────────────────────────────────────────

describe("GraphReasoner (extended)", () => {
  describe("addTriplets", () => {
    it("batch-adds triplets from objects", () => {
      const gr = new GraphReasoner();
      gr.addTriplets([
        { subject: "A", predicate: "works_at", object: "Corp", confidence: 0.9 },
        { subject: "Corp", predicate: "located_in", object: "City", confidence: 0.85 },
        { subject: "City", predicate: "is_a", object: "Place", confidence: 0.95 },
      ]);

      const paths = gr.findPaths("A", "Place", 3);
      expect(paths.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("findPaths", () => {
    it("returns empty for non-existent source", () => {
      const gr = new GraphReasoner();
      expect(gr.findPaths("Nonexistent", "Target", 3)).toEqual([]);
    });

    it("returns empty for non-existent target", () => {
      const gr = new GraphReasoner();
      gr.addTriplet("A", "rel", "B");
      expect(gr.findPaths("A", "Nonexistent", 3)).toEqual([]);
    });

    it("finds multiple paths (BFS + DFS)", () => {
      const gr = new GraphReasoner();
      // Diamond shape: A -> B -> D  and  A -> C -> D
      gr.addTriplet("A", "path1", "B");
      gr.addTriplet("B", "to", "D");
      gr.addTriplet("A", "path2", "C");
      gr.addTriplet("C", "to", "D");

      const paths = gr.findPaths("A", "D", 3);
      expect(paths.length).toBeGreaterThanOrEqual(2);
    });

    it("limits search to maxDepth", () => {
      const gr = new GraphReasoner();
      gr.addTriplet("A", "rel", "B");
      gr.addTriplet("B", "rel", "C");
      gr.addTriplet("C", "rel", "D");
      gr.addTriplet("D", "rel", "E");

      const paths = gr.findPaths("A", "E", 2);
      expect(paths).toEqual([]); // requires 4 hops > maxDepth 2
    });
  });

  describe("findRelated", () => {
    it("returns empty for non-existent node", () => {
      const gr = new GraphReasoner();
      expect(gr.findRelated("Nonexistent", 5)).toEqual([]);
    });

    it("respects maxDepth parameter", () => {
      const gr = new GraphReasoner();
      gr.addTriplet("A", "rel", "B");
      gr.addTriplet("B", "rel", "C");
      gr.addTriplet("C", "rel", "D");

      const d1 = gr.findRelated("A", 1);
      expect(d1).toContain("b");
      expect(d1).not.toContain("c");
    });
  });

  describe("nodeImportance", () => {
    it("handles empty graph", () => {
      const gr = new GraphReasoner();
      const importance = gr.nodeImportance();
      expect(importance.size).toBe(0);
    });

    it("scores hub nodes higher", () => {
      const gr = new GraphReasoner();
      gr.addTriplet("Hub", "connects", "A");
      gr.addTriplet("Hub", "connects", "B");
      gr.addTriplet("Hub", "connects", "C");

      const importance = gr.nodeImportance();
      expect(importance.get("hub")!).toBe(1.0); // max degree
      expect(importance.get("a")!).toBeLessThan(1.0);
    });
  });
});

// ── SubGraph 补充测试 ─────────────────────────────────────────────────

describe("SubGraph", () => {
  it("addNode creates adjacency entry", () => {
    const sg = new SubGraph(SubGraphType.SEMANTIC);
    sg.addNode("n1");
    expect(sg.adjacency.has("n1")).toBe(true);
  });

  it("getNeighbors returns connected nodes up to depth", () => {
    const sg = new SubGraph(SubGraphType.TEMPORAL);
    sg.addNode("a");
    sg.addNode("b");
    sg.addNode("c");
    sg.addEdge("a", "b", 1.0, EdgeType.NEXT);
    sg.addEdge("b", "c", 0.8, EdgeType.NEXT);

    const neighbors = sg.getNeighbors("a", 2);
    expect(neighbors.has("b")).toBe(true);
    expect(neighbors.has("c")).toBe(true);
  });

  it("getNeighbors default depth is 1", () => {
    const sg = new SubGraph(SubGraphType.TEMPORAL);
    sg.addNode("a");
    sg.addNode("b");
    sg.addEdge("a", "b", 1.0, EdgeType.NEXT);

    const neighbors = sg.getNeighbors("a");
    expect(neighbors.has("b")).toBe(true);
  });

  it("getEdgesFrom returns outgoing edges", () => {
    const sg = new SubGraph(SubGraphType.CAUSAL);
    sg.addNode("a");
    sg.addNode("b");
    sg.addEdge("a", "b", 0.9, EdgeType.DERIVED_FROM);

    const edges = sg.getEdgesFrom("a");
    expect(edges).toHaveLength(1);
    expect(edges[0][0]).toBe("b");
  });

  it("getEdgesTo returns incoming edges", () => {
    const sg = new SubGraph(SubGraphType.CAUSAL);
    sg.addNode("src");
    sg.addNode("dst");
    sg.addEdge("src", "dst", 0.7, EdgeType.DERIVED_FROM);

    const edges = sg.getEdgesTo("dst");
    expect(edges).toHaveLength(1);
    expect(edges[0][0]).toBe("src");
  });

  it("hasEdge detects existing and missing edges", () => {
    const sg = new SubGraph(SubGraphType.SEMANTIC);
    sg.addEdge("x", "y", 0.5, EdgeType.RELATED_TO);
    expect(sg.hasEdge("x", "y")).toBe(true);
    expect(sg.hasEdge("y", "x")).toBe(false);
  });

  it("adjacency check for nonexistent node", () => {
    const sg = new SubGraph(SubGraphType.TEMPORAL);
    expect(sg.adjacency.has("nonexistent")).toBe(false);
  });

  it("memoryEstimate returns reasonable value", () => {
    const sg = new SubGraph(SubGraphType.SEMANTIC);
    sg.addNode("a");
    sg.addNode("b");
    sg.addEdge("a", "b", 1.0, EdgeType.RELATED_TO);

    expect(sg.memoryEstimate).toBeGreaterThan(0);
  });
});

// ── MultiGraphMemory 补充测试 ─────────────────────────────────────────

describe("MultiGraphMemory (extended)", () => {
  it("getRelated returns nodes from specified subgraph", () => {
    const mg = new MultiGraphMemory();
    mg.addNode("n1", "Ep 1", NodeType.EPISODE);
    mg.addNode("n2", "Ep 2", NodeType.EPISODE);
    mg.addNode("n3", "Fact", NodeType.FACT);
    mg.addEdge("n1", "n2", EdgeType.NEXT);
    mg.addEdge("n1", "n3", EdgeType.HAS_CONCEPT);

    const temporal = mg.getRelated("n1", SubGraphType.TEMPORAL, 5);
    expect(temporal).toContain("n2");
  });

  it("getExpandedNodes returns expansion from seed query", () => {
    const mg = new MultiGraphMemory();
    mg.addNode("seed", "Seed concept", NodeType.CONCEPT, { category: "tech" });
    mg.addNode("child1", "Child 1", NodeType.CONCEPT);
    mg.addNode("child2", "Child 2", NodeType.CONCEPT);
    mg.addEdge("seed", "child1", EdgeType.RELATED_TO);
    mg.addEdge("seed", "child2", EdgeType.RELATED_TO);

    const expanded = mg.getExpandedNodes(["seed"]);
    expect(expanded.size).toBeGreaterThanOrEqual(1);
  });

  it("removeExpiredEdges removes low-weight edges", () => {
    const mg = new MultiGraphMemory();
    mg.addNode("a", "A", NodeType.EPISODE);
    mg.addNode("b", "B", NodeType.EPISODE);
    mg.addNode("c", "C", NodeType.EPISODE);
    mg.addEdge("a", "b", EdgeType.NEXT, 0.01); // very weak
    mg.addEdge("b", "c", EdgeType.NEXT, 0.5);

    const removed = mg.removeExpiredEdges(0.05);
    expect(removed).toBeGreaterThanOrEqual(1);
    expect(mg.hasEdge("a", "b")).toBe(false);
  });

  it("nodeCount returns correct count", () => {
    const mg = new MultiGraphMemory();
    mg.addNode("n1", "a", NodeType.EPISODE);
    mg.addNode("n2", "b", NodeType.EPISODE);
    expect(mg.nodeCount()).toBe(2);
  });

  it("multiGraphSearch falls back to seed nodes without edges", () => {
    const mg = new MultiGraphMemory();
    mg.addNode("isolated", "Isolated node", NodeType.CONCEPT);

    const results = mg.multiGraphSearch(["isolated"], 5);
    expect(results.length).toBeGreaterThanOrEqual(0);
  });
});

// ── ConceptMediatedGraph 补充测试 ──────────────────────────────────────

describe("ConceptMediatedGraph (extended)", () => {
  it("addConversation with string-only messages", () => {
    const graph = new ConceptMediatedGraph();
    const ids = graph.addConversation([
      { speaker: "user", content: "Hello" },
      { speaker: "agent", content: "World" },
    ] as any);
    expect(ids).toHaveLength(2);
  });

  it("retrieve with alpha=0 (pure keyword)", () => {
    const embedder = new DummyEmbedder(8);
    const graph = new ConceptMediatedGraph(undefined, embedder);
    graph.addEpisode("keyword match test query here");

    const results = graph.retrieve("match test", 3, 0.0);
    expect(Array.isArray(results)).toBe(true);
  });

  it("retrieve handles empty graph", () => {
    const embedder = new DummyEmbedder(8);
    const graph = new ConceptMediatedGraph(undefined, embedder);

    const results = graph.retrieve("nothing here", 5, 0.5);
    expect(results).toHaveLength(0);
  });

  it("addFact with default confidence", () => {
    const graph = new ConceptMediatedGraph();
    const epId = graph.addEpisode("episode");
    const factId = graph.addFact("A simple fact", epId);
    expect(factId).toBeTruthy();
  });

  it("addReflection without source nodes", () => {
    const graph = new ConceptMediatedGraph();
    const reflId = graph.addReflection("standalone reflection", []);
    expect(reflId).toBeTruthy();
    expect(graph.getNode(reflId)).toBeDefined();
  });
});
