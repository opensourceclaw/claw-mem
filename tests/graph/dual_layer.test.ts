import { describe, it, expect } from "vitest";
import { DualLayerMemory } from "../../src/graph/dual_layer";

describe("DualLayerMemory", () => {
  // ── Layer 1: Event Progression Graph ──

  describe("addEvent", () => {
    it("creates an event and returns event id", () => {
      const dm = new DualLayerMemory();
      const id = dm.addEvent("Test Event", "A test event", ["node1", "node2"], "session1", ["tag1"]);
      expect(id).toMatch(/^evt_[0-9a-f]+$/);
      expect(dm.eventCount()).toBe(1);
    });

    it("creates event without optional params", () => {
      const dm = new DualLayerMemory();
      const id = dm.addEvent("Minimal Event");
      expect(id).toBeDefined();
      expect(dm.eventCount()).toBe(1);
    });

    it("auto-links events in same session", () => {
      const dm = new DualLayerMemory();
      const id1 = dm.addEvent("Event 1", undefined, undefined, "session1");
      const id2 = dm.addEvent("Event 2", undefined, undefined, "session1");
      
      const chain = dm.getEventChain(id2);
      expect(chain.length).toBeGreaterThan(0);
    });
  });

  describe("getEvent", () => {
    it("returns event by id", () => {
      const dm = new DualLayerMemory();
      const id = dm.addEvent("Test Event", "Description");
      const evt = dm.getEvent(id);
      expect(evt).toBeDefined();
      expect(evt?.title).toBe("Test Event");
    });

    it("returns undefined for non-existent event", () => {
      const dm = new DualLayerMemory();
      expect(dm.getEvent("nonexistent")).toBeUndefined();
    });
  });

  describe("linkEvents", () => {
    it("links two events bidirectionally", () => {
      const dm = new DualLayerMemory();
      const id1 = dm.addEvent("Event 1");
      const id2 = dm.addEvent("Event 2");
      
      dm.linkEvents(id1, id2);
      
      const chain1 = dm.getEventChain(id1);
      const chain2 = dm.getEventChain(id2);
      
      expect(chain1.length).toBeGreaterThan(0);
      expect(chain2.length).toBeGreaterThan(0);
    });
  });

  describe("getEventChain", () => {
    it("returns event chain (predecessor sequence)", () => {
      const dm = new DualLayerMemory();
      const id1 = dm.addEvent("Event 1", undefined, undefined, "sess1");
      const id2 = dm.addEvent("Event 2", undefined, undefined, "sess1");
      const id3 = dm.addEvent("Event 3", undefined, undefined, "sess1");
      
      const chain = dm.getEventChain(id3);
      expect(chain).toBeInstanceOf(Array);
    });
  });

  describe("findEventsByTags", () => {
    it("finds events matching tags", () => {
      const dm = new DualLayerMemory();
      dm.addEvent("Event 1", undefined, undefined, undefined, ["tag1", "tag2"]);
      dm.addEvent("Event 2", undefined, undefined, undefined, ["tag3"]);
      
      const results = dm.findEventsByTags(["tag1"]);
      expect(results.length).toBe(1);
      expect(results[0].tags).toContain("tag1");
    });

    it("returns empty array when no matches", () => {
      const dm = new DualLayerMemory();
      dm.addEvent("Event 1", undefined, undefined, undefined, ["tag1"]);
      
      const results = dm.findEventsByTags(["nonexistent"]);
      expect(results.length).toBe(0);
    });
  });

  describe("findEventsBySession", () => {
    it("finds all events in a session", () => {
      const dm = new DualLayerMemory();
      dm.addEvent("Event 1", undefined, undefined, "session1");
      dm.addEvent("Event 2", undefined, undefined, "session1");
      dm.addEvent("Event 3", undefined, undefined, "session2");
      
      const results = dm.findEventsBySession("session1");
      expect(results.length).toBe(2);
    });

    it("returns sorted by start_time", () => {
      const dm = new DualLayerMemory();
      dm.addEvent("Event 2", undefined, undefined, "session1");
      dm.addEvent("Event 1", undefined, undefined, "session1");
      
      const results = dm.findEventsBySession("session1");
      expect(results[0].start_time).toBeLessThanOrEqual(results[1].start_time);
    });
  });

  describe("eventCount", () => {
    it("returns number of events", () => {
      const dm = new DualLayerMemory();
      expect(dm.eventCount()).toBe(0);
      dm.addEvent("Event 1");
      expect(dm.eventCount()).toBe(1);
      dm.addEvent("Event 2");
      expect(dm.eventCount()).toBe(2);
    });
  });

  // ── Layer 2: Topic Associative Network ──

  describe("addTopic", () => {
    it("creates a topic and returns topic id", () => {
      const dm = new DualLayerMemory();
      const id = dm.addTopic("Test Topic", "A test topic", ["node1"], ["evt1"], ["keyword1"]);
      expect(id).toMatch(/^tpc_[0-9a-f]+$/);
      expect(dm.topicCount()).toBe(1);
    });

    it("creates topic without optional params", () => {
      const dm = new DualLayerMemory();
      const id = dm.addTopic("Minimal Topic");
      expect(id).toBeDefined();
      expect(dm.topicCount()).toBe(1);
    });
  });

  describe("getTopic", () => {
    it("returns topic by id", () => {
      const dm = new DualLayerMemory();
      const id = dm.addTopic("Test Topic", "Description");
      const topic = dm.getTopic(id);
      expect(topic).toBeDefined();
      expect(topic?.name).toBe("Test Topic");
    });

    it("returns undefined for non-existent topic", () => {
      const dm = new DualLayerMemory();
      expect(dm.getTopic("nonexistent")).toBeUndefined();
    });
  });

  describe("linkTopics", () => {
    it("links two topics with symmetric weight", () => {
      const dm = new DualLayerMemory();
      const id1 = dm.addTopic("Topic 1");
      const id2 = dm.addTopic("Topic 2");
      
      dm.linkTopics(id1, id2, 0.8);
      
      const related = dm.getRelatedTopics(id1);
      expect(related.length).toBeGreaterThan(0);
    });
  });

  describe("getRelatedTopics", () => {
    it("returns related topics above min weight", () => {
      const dm = new DualLayerMemory();
      const id1 = dm.addTopic("Topic 1");
      const id2 = dm.addTopic("Topic 2");
      const id3 = dm.addTopic("Topic 3");
      
      dm.linkTopics(id1, id2, 0.8);
      dm.linkTopics(id1, id3, 0.2);
      
      const related = dm.getRelatedTopics(id1, 0.5);
      expect(related.length).toBe(1);
    });

    it("returns empty when no related topics", () => {
      const dm = new DualLayerMemory();
      const id = dm.addTopic("Topic 1");
      
      const related = dm.getRelatedTopics(id);
      expect(related.length).toBe(0);
    });

    it("respects minWeight parameter", () => {
      const dm = new DualLayerMemory();
      const id1 = dm.addTopic("Topic 1");
      const id2 = dm.addTopic("Topic 2");
      
      dm.linkTopics(id1, id2, 0.4);
      
      const related = dm.getRelatedTopics(id1, 0.5);
      expect(related.length).toBe(0);
    });
  });

  describe("searchByKeywords", () => {
    it("returns topics ordered by match count", () => {
      const dm = new DualLayerMemory();
      dm.addTopic("Topic 1", undefined, undefined, undefined, ["python", "typescript"]);
      dm.addTopic("Topic 2", undefined, undefined, undefined, ["python"]);
      dm.addTopic("Topic 3", undefined, undefined, undefined, ["rust"]);
      
      const results = dm.searchByKeywords(["python"]);
      expect(results.length).toBe(2);
      expect(results[0].keywords).toContain("python");
    });

    it("is case insensitive", () => {
      const dm = new DualLayerMemory();
      dm.addTopic("Topic 1", undefined, undefined, undefined, ["PYTHON"]);
      
      const results = dm.searchByKeywords(["python"]);
      expect(results.length).toBe(1);
    });
  });

  describe("topicCount", () => {
    it("returns number of topics", () => {
      const dm = new DualLayerMemory();
      expect(dm.topicCount()).toBe(0);
      dm.addTopic("Topic 1");
      expect(dm.topicCount()).toBe(1);
    });
  });

  // ── Persistence ──

  describe("toDict / fromDict", () => {
    it("serializes and deserializes correctly", () => {
      const dm = new DualLayerMemory();
      dm.addEvent("Event 1", "Desc", ["node1"], "session1", ["tag1"]);
      dm.addTopic("Topic 1", "Topic desc", ["node1"], ["evt1"], ["kw1"]);
      
      const dict = dm.toDict();
      expect(dict.events).toBeDefined();
      expect(dict.topics).toBeDefined();
      expect(dict.event_chain).toBeDefined();
      expect(dict.topic_links).toBeDefined();
      
      const restored = DualLayerMemory.fromDict(dict);
      expect(restored.eventCount()).toBe(1);
      expect(restored.topicCount()).toBe(1);
    });

    it("handles empty state", () => {
      const dm = new DualLayerMemory();
      const dict = dm.toDict();
      const restored = DualLayerMemory.fromDict(dict);
      expect(restored.eventCount()).toBe(0);
      expect(restored.topicCount()).toBe(0);
    });

    it("handles missing keys in dict", () => {
      const dm = new DualLayerMemory();
      const dict = {} as any;
      const restored = DualLayerMemory.fromDict(dict);
      expect(restored.eventCount()).toBe(0);
    });
  });
});