// Entity Resolver Tests (v6.30.0)

import { describe, it, expect } from "vitest";
import { EntityResolver } from "../../src/entity/entity-resolver";

describe("EntityResolver", () => {
  describe("canonicalization", () => {
    it("canonicalizes to lowercase", () => {
      const resolver = new EntityResolver();
      expect(resolver.canonicalize("ClawMem")).toBe("clawmem");
      expect(resolver.canonicalize("TYPESCRIPT")).toBe("typescript");
    });

    it("removes separators", () => {
      const resolver = new EntityResolver();
      expect(resolver.canonicalize("claw-mem")).toBe("clawmem");
      expect(resolver.canonicalize("claw_mem")).toBe("clawmem");
      expect(resolver.canonicalize("claw.mem")).toBe("clawmem");
      expect(resolver.canonicalize("claw mem")).toBe("clawmem");
    });

    it("removes trailing punctuation", () => {
      const resolver = new EntityResolver();
      expect(resolver.canonicalize("openclaw!")).toBe("openclaw");
      expect(resolver.canonicalize("typescript?")).toBe("typescript");
      expect(resolver.canonicalize("docker.")).toBe("docker");
    });

    it("maps aliases to canonical", () => {
      const resolver = new EntityResolver();
      expect(resolver.canonicalize("claw-mem")).toBe("clawmem");
      expect(resolver.canonicalize("ClawMem")).toBe("clawmem");
      expect(resolver.canonicalize("TypeScript")).toBe("typescript");
      expect(resolver.canonicalize("TS")).toBe("typescript");
    });
  });

  describe("resolve", () => {
    it("returns canonical name", () => {
      const resolver = new EntityResolver();
      const result = resolver.resolve("claw-mem");

      expect(result.canonical).toBe("clawmem");
    });

    it("returns alternatives", () => {
      const resolver = new EntityResolver();
      const result = resolver.resolve("clawmem");

      expect(result.alternatives).toContain("claw-mem");
      expect(result.alternatives).toContain("ClawMem");
    });

    it("detects new entities", () => {
      const resolver = new EntityResolver();
      const result = resolver.resolve("some-new-project");

      expect(result.isNew).toBe(true);
    });

    it("detects known entities", () => {
      const resolver = new EntityResolver();
      // Default aliases include clawmem
      const result = resolver.resolve("clawmem");

      expect(result.isNew).toBe(false);
    });
  });

  describe("alias management", () => {
    it("handles custom aliases", () => {
      const resolver = new EntityResolver({
        customAliases: {
          "myproject": ["MyProject", "MP", "my-project"],
        },
      });

      expect(resolver.canonicalize("MyProject")).toBe("myproject");
      expect(resolver.canonicalize("MP")).toBe("myproject");
      expect(resolver.canonicalize("my-project")).toBe("myproject");
    });

    it("can add aliases after construction", () => {
      const resolver = new EntityResolver();
      resolver.addAlias("newproject", "NP");
      resolver.addAliases("newproject", ["NewProject", "new-project"]);

      expect(resolver.canonicalize("NP")).toBe("newproject");
      expect(resolver.canonicalize("NewProject")).toBe("newproject");
    });

    it("returns aliases for canonical name", () => {
      const resolver = new EntityResolver();
      const aliases = resolver.getAliases("clawmem");

      expect(aliases).toContain("claw-mem");
      expect(aliases).toContain("ClawMem");
    });
  });

  describe("known entity tracking", () => {
    it("checks if entity is known", () => {
      const resolver = new EntityResolver();

      expect(resolver.isKnown("clawmem")).toBe(true);
      expect(resolver.isKnown("typescript")).toBe(true);
      expect(resolver.isKnown("unknown-entity")).toBe(false);
    });

    it("can register new known entities", () => {
      const resolver = new EntityResolver();

      expect(resolver.isKnown("newentity")).toBe(false);
      resolver.registerKnown("newentity");
      expect(resolver.isKnown("newentity")).toBe(true);
    });
  });

  describe("edge cases", () => {
    it("handles empty name", () => {
      const resolver = new EntityResolver();
      expect(resolver.canonicalize("")).toBe("");
    });

    it("handles name with special chars", () => {
      const resolver = new EntityResolver();
      expect(resolver.canonicalize("Project!!!")).toBe("project");
      expect(resolver.canonicalize("What???")).toBe("what");
    });

    it("fuzzy search returns exact matches (v6.30.0 placeholder)", () => {
      const resolver = new EntityResolver();
      const results = resolver.fuzzySearch("clawmem", 0.8);

      expect(results).toContain("clawmem");
    });

    it("fuzzy search returns empty for unknown (v6.30.0 placeholder)", () => {
      const resolver = new EntityResolver();
      const results = resolver.fuzzySearch("unknown-entity", 0.8);

      expect(results).toHaveLength(0);
    });
  });
});
