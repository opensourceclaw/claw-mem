// Entity Extractor Tests (v6.30.0)

import { describe, it, expect } from "vitest";
import { EntityExtractor } from "../../src/entity/entity-extractor";

describe("EntityExtractor", () => {
  describe("basic extraction", () => {
    it("extracts @mentions as person", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Fixed bug reported by @peter and @john");

      expect(entities).toHaveLength(2);
      expect(entities.find(e => e.name === "peter")).toBeDefined();
      expect(entities.find(e => e.name === "peter")?.type).toBe("person");
      expect(entities.find(e => e.name === "john")).toBeDefined();
      expect(entities.find(e => e.name === "john")?.type).toBe("person");
    });

    it("extracts known project names", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Working on claw-mem and claw-ctx today");

      expect(entities).toHaveLength(2);
      expect(entities.find(e => e.name === "claw-mem")?.type).toBe("project");
      expect(entities.find(e => e.name === "claw-ctx")?.type).toBe("project");
    });

    it("extracts known tool names", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Using TypeScript and Docker for development");

      expect(entities).toHaveLength(2);
      expect(entities.find(e => e.name === "TypeScript")?.type).toBe("tool");
      expect(entities.find(e => e.name === "Docker")?.type).toBe("tool");
    });

    it("extracts file paths", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Modified src/types.ts and src/memory_manager.ts");

      expect(entities.length).toBeGreaterThanOrEqual(2);
      expect(entities.find(e => e.name === "src/types.ts")?.type).toBe("file");
      expect(entities.find(e => e.name === "src/memory_manager.ts")?.type).toBe("file");
    });

    it("extracts version tags", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Released v6.30.0 and working on 1.2.3-beta");

      expect(entities).toHaveLength(2);
      expect(entities.find(e => e.name === "v6.30.0")?.type).toBe("concept");
      expect(entities.find(e => e.name === "1.2.3-beta")?.type).toBe("concept");
    });

    it("extracts acronyms", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Using API and SDK for HTTP requests");

      expect(entities.length).toBeGreaterThanOrEqual(3);
      expect(entities.find(e => e.name === "API")?.type).toBe("concept");
      expect(entities.find(e => e.name === "SDK")?.type).toBe("concept");
      expect(entities.find(e => e.name === "HTTP")?.type).toBe("concept");
    });

    it("extracts capitalized phrases", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Working with John Smith and Mary Jane");

      expect(entities.length).toBeGreaterThanOrEqual(2);
      expect(entities.find(e => e.name === "John Smith")).toBeDefined();
      expect(entities.find(e => e.name === "Mary Jane")).toBeDefined();
    });
  });

  describe("filtering", () => {
    it("filters stopwords", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("The quick brown fox jumps over the lazy dog");

      // "The" should be filtered as stopword
      expect(entities.find(e => e.name === "The")).toBeUndefined();
    });

    it("deduplicates by name", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("claw-mem is great. I love claw-mem!");

      const clawMemEntities = entities.filter(e => e.name === "claw-mem");
      expect(clawMemEntities).toHaveLength(1);
    });

    it("keeps highest confidence for duplicates", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("Using TypeScript which is great");

      // TypeScript appears as tool (0.9) and potentially capitalized (0.6)
      const tsEntity = entities.find(e => e.name === "TypeScript");
      expect(tsEntity?.confidence).toBe(0.9);
      expect(tsEntity?.type).toBe("tool");
    });
  });

  describe("edge cases", () => {
    it("handles empty text", () => {
      const extractor = new EntityExtractor();
      expect(extractor.extract("")).toEqual([]);
      expect(extractor.extract("   ")).toEqual([]);
    });

    it("handles pure Chinese text", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("这是一段中文文本");

      // v6.30.0 doesn't support Chinese extraction
      expect(entities).toHaveLength(0);
    });

    it("handles text without entities", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("lowercase text without any entities");

      expect(entities).toHaveLength(0);
    });

    it("handles long text", () => {
      const extractor = new EntityExtractor();
      const longText = "Working on @peter project. ".repeat(100);
      const entities = extractor.extract(longText);

      // Should extract @peter multiple times but deduplicate
      expect(entities.find(e => e.name === "peter")).toBeDefined();
    });

    it("sorts entities by position", () => {
      const extractor = new EntityExtractor();
      const entities = extractor.extract("First @alice, then @bob, finally @charlie");

      expect(entities[0].name).toBe("alice");
      expect(entities[1].name).toBe("bob");
      expect(entities[2].name).toBe("charlie");
    });
  });

  describe("customization", () => {
    it("supports custom rules", () => {
      const extractor = new EntityExtractor({
        customRules: [
          {
            pattern: /#\w+/g,
            type: "concept",
            confidence: 0.8,
            nameTransform: (m) => m.slice(1),  // Remove # prefix
          },
        ],
      });

      const entities = extractor.extract("Working on #feature and @peter");
      const featureBranch = entities.find(e => e.name === "feature");
      expect(featureBranch).toBeDefined();
      expect(featureBranch?.type).toBe("concept");
      expect(entities.find(e => e.name === "peter")?.type).toBe("person");
    });

    it("supports custom stopwords", () => {
      const extractor = new EntityExtractor({
        customStopwords: ["Project", "System"],
      });

      const entities = extractor.extract("Project and System are stopwords");
      expect(entities.find(e => e.name === "Project")).toBeUndefined();
      expect(entities.find(e => e.name === "System")).toBeUndefined();
    });

    it("can add rules after construction", () => {
      const extractor = new EntityExtractor();
      extractor.addRule({
        pattern: /BUG-\d+/g,
        type: "event",
        confidence: 0.95,
      });

      const entities = extractor.extract("Fixed BUG-123 and BUG-456");
      const bug123 = entities.find(e => e.name === "BUG-123");
      const bug456 = entities.find(e => e.name === "BUG-456");
      expect(bug123).toBeDefined();
      expect(bug123?.type).toBe("event");
      expect(bug456).toBeDefined();
      expect(bug456?.type).toBe("event");
    });

    it("can add stopwords after construction", () => {
      const extractor = new EntityExtractor();
      extractor.addStopwords(["CustomStopword"]);

      const entities = extractor.extract("CustomStopword should be filtered");
      expect(entities.find(e => e.name === "CustomStopword")).toBeUndefined();
    });
  });
});
