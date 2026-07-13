import { describe, it, expect } from "vitest";

import {
  NodeType,
  Node,
  EpisodeNode,
  FactNode,
  ConceptNode,
  ReflectionNode,
  createNode,
  EdgeType,
  Edge,
  NextEdge,
  DerivedFromEdge,
  RelatedToEdge,
  HasConceptEdge,
  SynthesizedFromEdge,
  createEdge,
  ConceptMediatedGraph,
  DummyEmbedder,
  DummyExtractor,
  InMemoryGraphStorage,
  FileGraphStorage,
  DualLayerMemory,
  MultiGraphMemory,
  SubGraph,
  SubGraphType,
  GraphReasoner,
} from "../../src/deprecated/graph";

// ---------------------------------------------------------------------------
// 1. Node creation and serialization
// ---------------------------------------------------------------------------
describe("Node operations", () => {
  it("creates an EpisodeNode with expected defaults", () => {
    const ep = new EpisodeNode("ep_1", "Hello, world!", 0, "user");
    expect(ep.id).toBe("ep_1");
    expect(ep.content).toBe("Hello, world!");
    expect(ep.type).toBe(NodeType.EPISODE);
    expect(ep.speaker).toBe("user");
    expect(ep.sequence_id).toBe(0);
    expect(ep.created_at).toBeInstanceOf(Date);
  });

  it("serializes and deserializes a FactNode round-trip", () => {
    const fact = new FactNode("f_1", "Earth orbits the Sun", 0.95, "ep_42", true);
    const dict = fact.toDict();
    const restored = FactNode.fromDict(dict);
    expect(restored.id).toBe("f_1");
    expect(restored.content).toBe("Earth orbits the Sun");
    expect(restored.confidence).toBe(0.95);
    expect(restored.source_episode).toBe("ep_42");
    expect(restored.verified).toBe(true);
    expect(restored.type).toBe(NodeType.FACT);
  });

  it("factory createNode builds correct node types", () => {
    const ep = createNode(NodeType.EPISODE, "test", { speaker: "alice" });
    expect(ep.type).toBe(NodeType.EPISODE);
    expect((ep as EpisodeNode).speaker).toBe("alice");

    const fact = createNode(NodeType.FACT, "a fact", { confidence: 0.8 });
    expect(fact.type).toBe(NodeType.FACT);
    expect((fact as FactNode).confidence).toBe(0.8);

    const refl = createNode(NodeType.REFLECTION, "summary", { importance: 0.9 });
    expect(refl.type).toBe(NodeType.REFLECTION);
    expect((refl as ReflectionNode).importance).toBe(0.9);

    const conc = createNode(NodeType.CONCEPT, "physics", { category: "science" });
    expect(conc.type).toBe(NodeType.CONCEPT);
    expect((conc as ConceptNode).category).toBe("science");
  });
});

// ---------------------------------------------------------------------------
// 2. Edge creation and serialization
// ---------------------------------------------------------------------------
describe("Edge operations", () => {
  it("creates edges with correct types", () => {
    const next = new NextEdge("ep_1", "ep_2");
    expect(next.type).toBe(EdgeType.NEXT);
    expect(next.source_id).toBe("ep_1");
    expect(next.target_id).toBe("ep_2");

    const derived = new DerivedFromEdge("f_1", "ep_1");
    expect(derived.type).toBe(EdgeType.DERIVED_FROM);

    const related = new RelatedToEdge("a", "b");
    expect(related.type).toBe(EdgeType.RELATED_TO);

    const hasConc = new HasConceptEdge("ep_1", "c_1");
    expect(hasConc.type).toBe(EdgeType.HAS_CONCEPT);

    const synth = new SynthesizedFromEdge("r_1", "ep_1", ["ep_1", "f_1"]);
    expect(synth.type).toBe(EdgeType.SYNTHESIZED_FROM);
    expect(synth.source_node_ids).toEqual(["ep_1", "f_1"]);
  });

  it("edge factory creates correct types", () => {
    const e1 = createEdge(EdgeType.NEXT, "a", "b");
    expect(e1.type).toBe(EdgeType.NEXT);
    expect(e1).toBeInstanceOf(NextEdge);

    const e2 = createEdge(EdgeType.RELATED_TO, "x", "y", { weight: 0.5 });
    expect(e2.type).toBe(EdgeType.RELATED_TO);
    expect(e2.weight).toBe(0.5);
  });

  it("serializes and deserializes an Edge", () => {
    const edge = new Edge("src", "tgt", EdgeType.NEXT, 0.8);
    const dict = edge.toDict();
    const restored = Edge.fromDict(dict);
    expect(restored.source_id).toBe("src");
    expect(restored.target_id).toBe("tgt");
    expect(restored.type).toBe(EdgeType.NEXT);
    expect(restored.weight).toBe(0.8);
  });
});

// ---------------------------------------------------------------------------
// 3. InMemoryGraphStorage CRUD
// ---------------------------------------------------------------------------
describe("InMemoryGraphStorage CRUD", () => {
  it("saves, retrieves, and deletes nodes", () => {
    const store = new InMemoryGraphStorage();
    const ep = new EpisodeNode("e1", "content", 0, "user");
    store.saveNode(ep);
    expect(store.getNode("e1")?.id).toBe("e1");
    expect(store.getAllNodes()).toHaveLength(1);

    store.deleteNode("e1");
    expect(store.getNode("e1")).toBeUndefined();
    expect(store.getAllNodes()).toHaveLength(0);
  });

  it("saves, retrieves, and deletes edges", () => {
    const store = new InMemoryGraphStorage();
    store.saveNode(new EpisodeNode("e1", "first"));
    store.saveNode(new EpisodeNode("e2", "second"));
    const edge = new NextEdge("e1", "e2");
    store.saveEdge(edge);
    expect(store.getEdge("e1", "e2")).toBeDefined();
    expect(store.getAllEdges()).toHaveLength(1);
    expect(store.getEdgesFrom("e1")).toHaveLength(1);
    expect(store.getEdgesTo("e2")).toHaveLength(1);

    store.deleteEdge("e1", "e2");
    expect(store.getEdge("e1", "e2")).toBeUndefined();
  });

  it("tracks node types correctly", () => {
    const store = new InMemoryGraphStorage();
    store.saveNode(new EpisodeNode("e1", "ep"));
    store.saveNode(new FactNode("f1", "fact"));
    store.saveNode(new ConceptNode("c1", "concept"));
    store.saveNode(new ReflectionNode("r1", "refl"));

    expect(store.getNodesByType(NodeType.EPISODE)).toHaveLength(1);
    expect(store.getNodesByType(NodeType.FACT)).toHaveLength(1);
    expect(store.getNodesByType(NodeType.CONCEPT)).toHaveLength(1);
    expect(store.getNodesByType(NodeType.REFLECTION)).toHaveLength(1);
  });

  it("getNeighbors returns both incoming and outgoing", () => {
    const store = new InMemoryGraphStorage();
    store.saveNode(new EpisodeNode("e1", "a"));
    store.saveNode(new EpisodeNode("e2", "b"));
    store.saveNode(new EpisodeNode("e3", "c"));

    store.saveEdge(new NextEdge("e1", "e2"));
    store.saveEdge(new NextEdge("e2", "e3"));
    store.saveEdge(new DerivedFromEdge("f1", "e2"));

    const neighbors = store.getNeighbors("e2");
    expect(neighbors.has("e1")).toBe(true); // incoming
    expect(neighbors.has("e3")).toBe(true); // outgoing
    expect(neighbors.has("f1")).toBe(true); // incoming
  });
});

// ---------------------------------------------------------------------------
// 4. ConceptMediatedGraph (core graph engine)
// ---------------------------------------------------------------------------
describe("ConceptMediatedGraph", () => {
  it("adds conversation and creates episode nodes with NEXT edges", () => {
    const graph = new ConceptMediatedGraph();
    const ids = graph.addConversation([
      { speaker: "user", content: "Hello" },
      { speaker: "agent", content: "Hi there!" },
    ]);
    expect(ids).toHaveLength(2);
    expect(graph.getNode(ids[0])).toBeDefined();
    expect(graph.getNode(ids[1])).toBeDefined();
    // Should have NEXT edge between them
    const neighbors = graph.getNeighbors(ids[0]);
    expect(neighbors.some((n) => n.id === ids[1])).toBe(true);

    const stats = graph.getStats();
    expect((stats as any).total_nodes).toBeGreaterThanOrEqual(2);
  });

  it("retrieves results through hybrid retrieval", () => {
    const embedder = new DummyEmbedder(16);
    const graph = new ConceptMediatedGraph(undefined, embedder);

    graph.addEpisode("The quick brown fox jumps over the lazy dog");
    graph.addEpisode("Python is a great programming language for data science");
    graph.addEpisode("Machine learning models require large amounts of data");

    const results = graph.retrieve("data science", 5, 1.0); // pure semantic
    expect(results.length).toBeGreaterThan(0);
    expect(results[0]).toHaveProperty("node");
    expect(results[0]).toHaveProperty("score");
    expect(results[0]).toHaveProperty("type");
  });

  it("adds facts, concepts, and reflections", () => {
    const graph = new ConceptMediatedGraph();
    const epId = graph.addEpisode("Some episode content");

    const factId = graph.addFact("A key fact", epId, 0.9);
    expect(factId).toBeTruthy();
    const fact = graph.getNode(factId) as FactNode;
    expect(fact.confidence).toBe(0.9);

    const conceptId = graph.addConcept("machine learning", "topic");
    expect(conceptId).toBeTruthy();
    // Adding same concept again should return same ID
    const conceptId2 = graph.addConcept("machine learning", "topic");
    expect(conceptId2).toBe(conceptId);

    const reflId = graph.addReflection("A reflection", [epId, factId], "insight");
    expect(reflId).toBeTruthy();
    const refl = graph.getNode(reflId) as ReflectionNode;
    expect(refl.summary_type).toBe("insight");
    expect(refl.source_node_ids).toEqual([epId, factId]);
  });
});

// ---------------------------------------------------------------------------
// 5. MultiGraphMemory (four subgraph index)
// ---------------------------------------------------------------------------
describe("MultiGraphMemory", () => {
  it("registers nodes and routes edges to correct subgraphs", () => {
    const mg = new MultiGraphMemory();
    mg.addNode("n1", "Episode 1", NodeType.EPISODE, { speaker: "user" });
    mg.addNode("n2", "Episode 2", NodeType.EPISODE, { speaker: "agent" });
    mg.addNode("n3", "A concept", NodeType.CONCEPT, { category: "topic" });

    mg.addEdge("n1", "n2", EdgeType.NEXT);
    mg.addEdge("n1", "n3", EdgeType.HAS_CONCEPT);
    mg.addEdge("n2", "n3", EdgeType.RELATED_TO);

    expect(mg.hasEdge("n1", "n2")).toBe(true);
    expect(mg.hasEdge("n1", "n3")).toBe(true);
    expect(mg.hasEdge("n2", "n3")).toBe(true);
    expect(mg.nodeCount()).toBe(3);

    const stats = mg.getStats() as any;
    expect(stats.total_nodes).toBe(3);
    expect(stats.subgraphs.temporal.edges).toBe(1);   // NEXT
    expect(stats.subgraphs.entity.edges).toBe(1);      // HAS_CONCEPT
    expect(stats.subgraphs.semantic.edges).toBe(1);     // RELATED_TO
  });

  it("multiGraphSearch expands from seed nodes across subgraphs", () => {
    const mg = new MultiGraphMemory();
    // Build: n1 ->(NEXT) n2 ->(DERIVED_FROM) n3 ->(HAS_CONCEPT) n4
    mg.addNode("n1", "a", NodeType.EPISODE);
    mg.addNode("n2", "b", NodeType.EPISODE);
    mg.addNode("n3", "c", NodeType.FACT);
    mg.addNode("n4", "d", NodeType.CONCEPT);

    mg.addEdge("n1", "n2", EdgeType.NEXT, 1.0);
    mg.addEdge("n3", "n2", EdgeType.DERIVED_FROM, 0.9);
    mg.addEdge("n3", "n4", EdgeType.HAS_CONCEPT, 0.8);

    const results = mg.multiGraphSearch(["n1"], 5);
    expect(results.length).toBeGreaterThan(1);
    // n1 (seed) should be at the top
    expect(results[0][0]).toBe("n1");
  });
});

// ---------------------------------------------------------------------------
// 6. GraphReasoner (path finding)
// ---------------------------------------------------------------------------
describe("GraphReasoner", () => {
  it("finds paths between nodes using triplets", () => {
    const gr = new GraphReasoner();
    gr.addTriplet("Alice", "works_at", "AcmeCorp");
    gr.addTriplet("AcmeCorp", "located_in", "New York");
    gr.addTriplet("New York", "is_a", "City");

    const paths = gr.findPaths("Alice", "City", 4);
    expect(paths.length).toBeGreaterThanOrEqual(1);
    const shortest = paths[0];
    expect(shortest.path.length).toBe(3);
    expect(shortest.confidence).toBeGreaterThan(0);
    expect(shortest.path[0][0]).toBe("alice");
    expect(shortest.path[2][2]).toBe("city");
  });

  it("finds related nodes up to max depth", () => {
    const gr = new GraphReasoner();
    gr.addTriplet("A", "rel", "B");
    gr.addTriplet("B", "rel", "C");
    gr.addTriplet("C", "rel", "D");

    const related = gr.findRelated("A", 2);
    expect(related).toContain("b");
    expect(related).toContain("c");
    expect(related).not.toContain("d"); // depth=2 only reaches C
  });

  it("computes node importance scores", () => {
    const gr = new GraphReasoner();
    gr.addTriplet("X", "leads", "Y");
    gr.addTriplet("Y", "reports", "Z");
    gr.addTriplet("X", "mentors", "Z");

    const importance = gr.nodeImportance();
    expect(importance.size).toBe(3);
    // X has out-degree 2 -> highest importance
    const xScore = importance.get("x")!;
    const zScore = importance.get("z")!;
    expect(xScore).toBeGreaterThanOrEqual(zScore);
  });
});
