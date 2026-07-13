import { describe, it, expect } from "vitest";
import { DummyExtractor, LLMExtractor, KeywordExtractor } from "../../src/deprecated/graph/extractors";

describe("DummyExtractor", () => {
  it("extracts no facts", () => {
    const extractor = new DummyExtractor();
    const facts = extractor.extractFacts("Some text with information");
    expect(facts).toEqual([]);
  });

  it("extracts no concepts", () => {
    const extractor = new DummyExtractor();
    const concepts = extractor.extractConcepts("Some text with information");
    expect(concepts).toEqual([]);
  });
});

describe("LLMExtractor", () => {
  describe("constructor", () => {
    it("creates with null LLM client", () => {
      const extractor = new LLMExtractor(null);
      expect(extractor).toBeDefined();
    });

    it("creates with LLM client", () => {
      const llm = { generate: () => "result" };
      const extractor = new LLMExtractor(llm);
      expect(extractor).toBeDefined();
    });
  });

  describe("extractFacts", () => {
    it("uses LLM when available", () => {
      const llm = {
        generate: (prompt: string) => "Fact 1\nFact 2"
      };
      const extractor = new LLMExtractor(llm);
      const facts = extractor.extractFacts("Some text");
      
      expect(facts.length).toBe(2);
      expect(facts[0]).toBe("Fact 1");
    });

    it("falls back to rule-based when no LLM", () => {
      const extractor = new LLMExtractor();
      const facts = extractor.extractFacts("This is a test sentence. This is another one.");
      
      expect(facts.length).toBeGreaterThan(0);
    });

    it("handles LLM generation error gracefully", () => {
      const llm = {
        generate: () => { throw new Error("LLM error"); }
      };
      const extractor = new LLMExtractor(llm);
      const facts = extractor.extractFacts("Some text");
      
      expect(facts.length).toBeGreaterThan(0);
    });

    it("handles LLM returning empty response", () => {
      const llm = {
        generate: () => ""
      };
      const extractor = new LLMExtractor(llm);
      const facts = extractor.extractFacts("Some text");
      
      // Falls back to rule-based
      expect(Array.isArray(facts)).toBe(true);
    });
  });

  describe("extractConcepts", () => {
    it("uses LLM when available", () => {
      const llm = {
        generate: (prompt: string) => "Concept1\nConcept2"
      };
      const extractor = new LLMExtractor(llm);
      const concepts = extractor.extractConcepts("Some text");
      
      expect(concepts.length).toBe(2);
    });

    it("falls back to rule-based when no LLM", () => {
      const extractor = new LLMExtractor();
      const concepts = extractor.extractConcepts("Python TypeScript JavaScript");
      
      expect(concepts.length).toBeGreaterThan(0);
    });

    it("handles LLM error gracefully", () => {
      const llm = {
        generate: () => { throw new Error("error"); }
      };
      const extractor = new LLMExtractor(llm);
      const concepts = extractor.extractConcepts("Python TypeScript");
      
      expect(Array.isArray(concepts)).toBe(true);
    });
  });

  describe("generateReflection", () => {
    it("uses LLM when available", () => {
      const llm = {
        generate: (prompt: string) => "Reflection summary"
      };
      const extractor = new LLMExtractor(llm);
      const reflection = extractor.generateReflection([
        { content: "Memory 1" },
        { content: "Memory 2" }
      ]);
      
      expect(reflection).toBe("Reflection summary");
    });

    it("falls back to rule-based when no LLM", () => {
      const extractor = new LLMExtractor();
      const reflection = extractor.generateReflection([
        { content: "Memory content here" }
      ]);
      
      expect(reflection).toContain("Review:");
    });

    it("handles empty nodes", () => {
      const extractor = new LLMExtractor();
      const reflection = extractor.generateReflection([]);
      
      expect(reflection).toBe("Not enough information to generate reflection");
    });

    it("handles LLM error gracefully", () => {
      const llm = {
        generate: () => { throw new Error("error"); }
      };
      const extractor = new LLMExtractor(llm);
      const reflection = extractor.generateReflection([
        { content: "Memory" }
      ]);
      
      expect(reflection).toContain("Review:");
    });
  });

  describe("extractFactsRuleBased", () => {
    it("splits by sentence terminators", () => {
      const extractor = new LLMExtractor();
      const facts = extractor.extractFactsRuleBased("First sentence. Second sentence!");
      
      expect(facts.length).toBeGreaterThanOrEqual(1);
    });

    it("filters by length", () => {
      const extractor = new LLMExtractor();
      const facts = extractor.extractFactsRuleBased("Short. A longer sentence here.");
      
      expect(facts.length).toBe(1);
    });

    it("limits to 5 facts", () => {
      const extractor = new LLMExtractor();
      const facts = extractor.extractFactsRuleBased(
        "One. Two. Three. Four. Five. Six. Seven."
      );
      
      expect(facts.length).toBeLessThanOrEqual(5);
    });
  });

  describe("extractConceptsRuleBased", () => {
    it("extracts Chinese concepts", () => {
      const extractor = new LLMExtractor();
      const concepts = extractor.extractConceptsRuleBased("学习Python编程技术");
      
      expect(concepts.length).toBeGreaterThan(0);
    });

    it("extracts English concepts", () => {
      const extractor = new LLMExtractor();
      const concepts = extractor.extractConceptsRuleBased("Python TypeScript JavaScript programming");
      
      expect(concepts.length).toBeGreaterThan(0);
    });

    it("deduplicates concepts", () => {
      const extractor = new LLMExtractor();
      const concepts = extractor.extractConceptsRuleBased("Python Python Python");
      
      const unique = new Set(concepts);
      expect(unique.size).toBe(concepts.length);
    });

    it("limits to 10 concepts", () => {
      const extractor = new LLMExtractor();
      const concepts = extractor.extractConceptsRuleBased(
        "Python TypeScript JavaScript Go Rust Ruby PHP Swift Kotlin Scala"
      );
      
      expect(concepts.length).toBeLessThanOrEqual(10);
    });
  });

  describe("generateReflectionRuleBased", () => {
    it("returns latest memory content", () => {
      const extractor = new LLMExtractor();
      const reflection = extractor.generateReflectionRuleBased([
        { content: "First memory" },
        { content: "Second memory" }
      ]);
      
      expect(reflection).toContain("Second memory");
    });

    it("handles empty array", () => {
      const extractor = new LLMExtractor();
      const reflection = extractor.generateReflectionRuleBased([]);
      
      expect(reflection).toBe("Not enough information to generate reflection");
    });
  });
});

describe("KeywordExtractor", () => {
  describe("constructor", () => {
    it("creates extractor", () => {
      const extractor = new KeywordExtractor();
      expect(extractor).toBeDefined();
    });
  });

  describe("extractFacts", () => {
    it("delegates to LLMExtractor rule-based", () => {
      const extractor = new KeywordExtractor();
      const facts = extractor.extractFacts("First sentence. Second sentence.");
      
      expect(Array.isArray(facts)).toBe(true);
    });
  });

  describe("extractConcepts", () => {
    it("extracts concepts filtering stopwords", () => {
      const extractor = new KeywordExtractor();
      const concepts = extractor.extractConcepts("学习Python编程技术 the programming");
      
      expect(concepts.length).toBeGreaterThan(0);
      // Should filter out common stopwords
      const hasStopword = concepts.some(c => 
        ["的", "了", "是", "在", "the", "a", "an"].includes(c.toLowerCase())
      );
      expect(hasStopword).toBe(false);
    });

    it("limits to 10 concepts", () => {
      const extractor = new KeywordExtractor();
      const concepts = extractor.extractConcepts(
        "Python TypeScript JavaScript Go Rust Ruby PHP Swift Kotlin Scala"
      );
      
      expect(concepts.length).toBeLessThanOrEqual(10);
    });
  });
});