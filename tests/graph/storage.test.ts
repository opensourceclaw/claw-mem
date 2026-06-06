import { describe, it, expect, beforeEach, afterAll } from "vitest";
import { InMemoryGraphStorage, FileGraphStorage, GraphStorage } from "../../src/graph/storage";
import { EpisodeNode, FactNode, ConceptNode, ReflectionNode } from "../../src/graph/nodes";
import { Edge, EdgeType } from "../../src/graph/edges";

const createEdge = (sourceId: string, targetId: string, weight = 1.0) => 
  new Edge(sourceId, targetId, EdgeType.RELATED_TO, weight);

describe("InMemoryGraphStorage", () => {
  let storage: InMemoryGraphStorage;

  beforeEach(() => {
    storage = new InMemoryGraphStorage();
  });

  describe("saveNode / getNode", () => {
    it("saves and retrieves a node", () => {
      const node = new EpisodeNode("ep1", "Test content", 1);
      storage.saveNode(node);
      
      const retrieved = storage.getNode("ep1");
      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe("ep1");
    });

    it("returns undefined for non-existent node", () => {
      const result = storage.getNode("nonexistent");
      expect(result).toBeUndefined();
    });

    it("overwrites existing node", () => {
      const node1 = new EpisodeNode("ep1", "Original", 1);
      const node2 = new EpisodeNode("ep1", "Updated", 2);
      
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      const retrieved = storage.getNode("ep1");
      expect(retrieved?.content).toBe("Updated");
    });
  });

  describe("deleteNode", () => {
    it("deletes a node", () => {
      const node = new EpisodeNode("ep1", "Test", 1);
      storage.saveNode(node);
      
      const result = storage.deleteNode("ep1");
      expect(result).toBe(true);
      expect(storage.getNode("ep1")).toBeUndefined();
    });

    it("returns false for non-existent node", () => {
      const result = storage.deleteNode("nonexistent");
      expect(result).toBe(false);
    });

    it("cleans up edges when deleting node", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      storage.deleteNode("ep1");
      
      const edges = storage.getEdgesTo("ep2");
      expect(edges.length).toBe(0);
    });
  });

  describe("getAllNodes", () => {
    it("returns all nodes", () => {
      storage.saveNode(new EpisodeNode("ep1", "Test 1", 1));
      storage.saveNode(new FactNode("f1", "Test fact", 0.9));
      
      const all = storage.getAllNodes();
      expect(all.length).toBe(2);
    });

    it("returns empty array when empty", () => {
      const all = storage.getAllNodes();
      expect(all).toEqual([]);
    });
  });

  describe("getNodesByType", () => {
    it("filters nodes by type", () => {
      storage.saveNode(new EpisodeNode("ep1", "Episode", 1));
      storage.saveNode(new FactNode("f1", "Fact", 0.9));
      storage.saveNode(new ConceptNode("c1", "Concept", "category", 1));
      
      const episodes = storage.getNodesByType("episode" as any);
      expect(episodes.length).toBe(1);
      
      const facts = storage.getNodesByType("fact" as any);
      expect(facts.length).toBe(1);
    });

    it("returns empty array for unknown type", () => {
      const result = storage.getNodesByType("unknown" as any);
      expect(result).toEqual([]);
    });
  });

  describe("saveEdge / getEdge", () => {
    it("saves and retrieves edge", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      storage.saveEdge(createEdge("ep1", "ep2", 0.8));
      
      const retrieved = storage.getEdge("ep1", "ep2");
      expect(retrieved).toBeDefined();
      expect(retrieved?.target_id).toBe("ep2");
    });

    it("returns undefined for non-existent edge", () => {
      const result = storage.getEdge("ep1", "ep2");
      expect(result).toBeUndefined();
    });

    it("adds multiple edges from same source", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      const node3 = new EpisodeNode("ep3", "Test 3", 3);
      storage.saveNode(node1);
      storage.saveNode(node2);
      storage.saveNode(node3);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      storage.saveEdge(createEdge("ep1", "ep3"));
      
      const edges = storage.getEdgesFrom("ep1");
      expect(edges.length).toBe(2);
    });
  });

  describe("deleteEdge", () => {
    it("deletes an edge", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      const result = storage.deleteEdge("ep1", "ep2");
      expect(result).toBe(true);
      expect(storage.getEdge("ep1", "ep2")).toBeUndefined();
    });

    it("returns false for non-existent edge", () => {
      const result = storage.deleteEdge("ep1", "ep2");
      expect(result).toBe(false);
    });
  });

  describe("getAllEdges", () => {
    it("returns all edges", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      const all = storage.getAllEdges();
      expect(all.length).toBe(1);
    });
  });

  describe("getEdgesFrom / getEdgesTo", () => {
    it("returns outgoing edges", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      const edges = storage.getEdgesFrom("ep1");
      expect(edges.length).toBe(1);
    });

    it("returns incoming edges", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      storage.saveNode(node1);
      storage.saveNode(node2);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      const edges = storage.getEdgesTo("ep2");
      expect(edges.length).toBe(1);
    });

    it("returns empty for unknown node", () => {
      const edges = storage.getEdgesFrom("nonexistent");
      expect(edges).toEqual([]);
    });
  });

  describe("getNeighbors", () => {
    it("returns all neighbors (incoming and outgoing)", () => {
      const node1 = new EpisodeNode("ep1", "Test 1", 1);
      const node2 = new EpisodeNode("ep2", "Test 2", 2);
      const node3 = new EpisodeNode("ep3", "Test 3", 3);
      storage.saveNode(node1);
      storage.saveNode(node2);
      storage.saveNode(node3);
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      storage.saveEdge(createEdge("ep3", "ep1"));
      
      const neighbors = storage.getNeighbors("ep1");
      expect(neighbors.has("ep2")).toBe(true);
      expect(neighbors.has("ep3")).toBe(true);
    });
  });

  describe("getStats", () => {
    it("returns statistics", () => {
      storage.saveNode(new EpisodeNode("ep1", "Test 1", 1));
      storage.saveNode(new EpisodeNode("ep2", "Test 2", 2));
      storage.saveNode(new FactNode("f1", "Fact", 0.9));
      storage.saveNode(new ConceptNode("c1", "Concept", "cat", 1));
      
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      const stats = storage.getStats();
      expect(stats.total_nodes).toBe(4);
      expect(stats.episodes).toBe(2);
      expect(stats.facts).toBe(1);
      expect(stats.concepts).toBe(1);
      expect(stats.total_edges).toBe(1);
    });
  });

  describe("clear", () => {
    it("clears all nodes and edges", () => {
      storage.saveNode(new EpisodeNode("ep1", "Test", 1));
      storage.saveNode(new FactNode("f1", "Fact", 0.9));
      storage.saveEdge(createEdge("ep1", "ep2"));
      
      storage.clear();
      
      expect(storage.getAllNodes().length).toBe(0);
      expect(storage.getAllEdges().length).toBe(0);
    });
  });
});

describe("FileGraphStorage", () => {
  const testPath = "/tmp/test_graph_storage.json";
  
  afterAll(() => {
    try {
      require("fs").unlinkSync(testPath);
    } catch {}
  });

  it("extends InMemoryGraphStorage", () => {
    const storage = new FileGraphStorage(testPath);
    expect(storage).toBeInstanceOf(InMemoryGraphStorage);
  });

  it("loads from file on construction", () => {
    const fs = require("fs");
    const testData = {
      nodes: [
        { id: "ep1", type: "episode", content: "Test episode", data: {} }
      ],
      edges: [],
      saved_at: new Date().toISOString()
    };
    fs.writeFileSync(testPath, JSON.stringify(testData));
    
    const storage = new FileGraphStorage(testPath);
    const node = storage.getNode("ep1");
    expect(node).toBeDefined();
  });

  it("saves to file on saveNode", () => {
    const storage = new FileGraphStorage(testPath);
    const node = new EpisodeNode("ep_test", "Test content", 1);
    storage.saveNode(node);
    
    const fs = require("fs");
    expect(fs.existsSync(testPath)).toBe(true);
    
    const content = fs.readFileSync(testPath, "utf-8");
    const data = JSON.parse(content);
    expect(data.nodes.some((n: any) => n.id === "ep_test")).toBe(true);
  });

  it("saves to file on saveEdge", () => {
    const storage = new FileGraphStorage(testPath);
    const node1 = new EpisodeNode("ep1", "Test 1", 1);
    const node2 = new EpisodeNode("ep2", "Test 2", 2);
    storage.saveNode(node1);
    storage.saveNode(node2);
    storage.saveEdge(createEdge("ep1", "ep2"));
    
    const fs = require("fs");
    const content = fs.readFileSync(testPath, "utf-8");
    const data = JSON.parse(content);
    expect(data.edges.length).toBe(1);
  });

  it("saves to file on deleteNode", () => {
    const storage = new FileGraphStorage(testPath);
    const node = new EpisodeNode("ep_del", "Test", 1);
    storage.saveNode(node);
    storage.deleteNode("ep_del");
    
    const fs = require("fs");
    const content = fs.readFileSync(testPath, "utf-8");
    const data = JSON.parse(content);
    expect(data.nodes.some((n: any) => n.id === "ep_del")).toBe(false);
  });
});