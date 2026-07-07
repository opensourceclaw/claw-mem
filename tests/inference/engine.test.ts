// claw-mem v6.34.0 — InferenceEngine Tests
//
// Unit tests for the InferenceEngine module.

import { describe, it, expect, beforeEach } from "vitest";
import {
  InferenceEngine,
  KnowledgeDeriver,
  ContradictionDetector,
  ChainVisualizer,
  DerivationType,
  ContradictionType,
  ContradictionSeverity,
  InferenceStepType,
} from "../../dist/src/inference/index.js";
import type { MemoryForInference } from "../../dist/src/inference/index.js";

describe("InferenceEngine", () => {
  let engine: InferenceEngine;

  beforeEach(() => {
    engine = new InferenceEngine();
  });

  describe("derive", () => {
    it("should return empty result when no memories", async () => {
      const result = await engine.derive("test query");
      expect(result.knowledge).toHaveLength(0);
      expect(result.confidence).toBe(0);
    });

    it("should return chain with query as first step", async () => {
      const result = await engine.derive("test query");
      expect(result.chain.steps[0].type).toBe(InferenceStepType.PREMISE);
      expect(result.chain.steps[0].content).toContain("test query");
    });

    it("should calculate processing time", async () => {
      const result = await engine.derive("test");
      expect(result.processingTimeMs).toBeGreaterThanOrEqual(0);
    });
  });

  describe("detectContradictions", () => {
    it("should return empty array when no memories", async () => {
      const result = await engine.detectContradictions([]);
      expect(result).toHaveLength(0);
    });

    it("should return empty array with single memory", async () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "User lives in Shanghai" },
      ];
      const result = await engine.detectContradictions(memories);
      expect(result).toHaveLength(0);
    });
  });

  describe("getStats", () => {
    it("should return initial stats", () => {
      const stats = engine.getStats();
      expect(stats.totalDerivations).toBe(0);
      expect(stats.cacheHits).toBe(0);
    });
  });

  describe("clearCache", () => {
    it("should clear cache without error", () => {
      expect(() => engine.clearCache()).not.toThrow();
    });
  });
});

describe("KnowledgeDeriver", () => {
  let deriver: KnowledgeDeriver;

  beforeEach(() => {
    deriver = new KnowledgeDeriver();
  });

  describe("deriveTransitive", () => {
    it("should derive transitive relation A→C from A→B and B→C", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Alice knows Bob", confidence: 0.9 },
        { id: "m2", content: "Bob knows Charlie", confidence: 0.9 },
      ];

      const result = deriver.deriveTransitive(memories);

      expect(result.knowledge.length).toBeGreaterThan(0);
      expect(result.knowledge[0].subject).toBe("Alice");
      expect(result.knowledge[0].object).toBe("Charlie");
      expect(result.knowledge[0].type).toBe(DerivationType.TRANSITIVE);
    });

    it("should return empty when no transitive chains", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Alice knows Bob" },
        { id: "m2", content: "Charlie knows David" },
      ];

      const result = deriver.deriveTransitive(memories);
      expect(result.knowledge).toHaveLength(0);
    });

    it("should return empty when no memories", () => {
      const result = deriver.deriveTransitive([]);
      expect(result.knowledge).toHaveLength(0);
      expect(result.steps).toHaveLength(0);
    });

    it("should apply confidence decay for transitive derivation", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Alice knows Bob", confidence: 1.0 },
        { id: "m2", content: "Bob knows Charlie", confidence: 1.0 },
      ];

      const result = deriver.deriveTransitive(memories);

      // Confidence should be min(1.0, 1.0) * 0.85 = 0.85
      expect(result.knowledge[0].confidence).toBeCloseTo(0.85, 1);
    });

    it("should include premise steps for each relation", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Alice knows Bob" },
        { id: "m2", content: "Bob knows Charlie" },
      ];

      const result = deriver.deriveTransitive(memories);

      const premiseSteps = result.steps.filter(
        (s) => s.type === InferenceStepType.PREMISE
      );
      expect(premiseSteps.length).toBeGreaterThanOrEqual(2);
    });
  });
});

describe("ContradictionDetector", () => {
  let detector: ContradictionDetector;

  beforeEach(() => {
    detector = new ContradictionDetector();
  });

  describe("detectDirect", () => {
    it("should detect direct contradiction for conflicting locations", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Peter lives in Shanghai", confidence: 0.9 },
        { id: "m2", content: "Peter lives in Shenzhen", confidence: 0.9 },
      ];

      const result = detector.detectDirect(memories);

      expect(result.length).toBeGreaterThan(0);
      expect(result[0].type).toBe(ContradictionType.DIRECT);
      expect(result[0].description).toContain("conflicting values");
    });

    it("should not detect contradiction for same values", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Peter lives in Shanghai" },
        { id: "m2", content: "Peter lives in Shanghai" },
      ];

      const result = detector.detectDirect(memories);
      expect(result).toHaveLength(0);
    });

    it("should return empty for no memories", () => {
      const result = detector.detectDirect([]);
      expect(result).toHaveLength(0);
    });

    it("should assign correct severity based on confidence", () => {
      const memories: MemoryForInference[] = [
        { id: "m1", content: "Peter lives in Shanghai", confidence: 1.0 },
        { id: "m2", content: "Peter lives in Shenzhen", confidence: 1.0 },
        { id: "m3", content: "Peter lives in Beijing", confidence: 1.0 },
      ];

      const result = detector.detectDirect(memories);
      expect(result[0].severity).toBe(ContradictionSeverity.HIGH);
    });
  });

  describe("generateSuggestions", () => {
    it("should generate resolution suggestions", () => {
      const memories: MemoryForInference[] = [
        {
          id: "m1",
          content: "Peter lives in Shanghai",
          confidence: 0.9,
          timestamp: 1000,
        },
        {
          id: "m2",
          content: "Peter lives in Shenzhen",
          confidence: 0.8,
          timestamp: 2000,
        },
      ];

      const reports = detector.detectDirect(memories);
      const suggestions = detector.generateSuggestions(reports[0]);

      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions.some((s) => s.type === "keep_newer")).toBe(true);
      expect(suggestions.some((s) => s.type === "ask_user")).toBe(true);
    });
  });
});

describe("ChainVisualizer", () => {
  let visualizer: ChainVisualizer;

  beforeEach(() => {
    visualizer = new ChainVisualizer();
  });

  describe("renderText", () => {
    it("should render chain as text", () => {
      const chain = {
        chainId: "test-chain",
        query: "test query",
        steps: [
          {
            stepId: "s1",
            type: InferenceStepType.PREMISE,
            content: "Test premise",
            memories: [],
            confidence: 0.9,
            timestamp: Date.now(),
          },
        ],
        result: [
          {
            id: "k1",
            type: DerivationType.TRANSITIVE,
            subject: "A",
            predicate: "knows",
            object: "C",
            confidence: 0.85,
            chainId: "test-chain",
            sourceMemoryIds: ["m1", "m2"],
            timestamp: Date.now(),
          },
        ],
        confidence: 0.85,
        timestamp: Date.now(),
        version: "1.0.0",
      };

      const text = visualizer.renderText(chain);

      expect(text).toContain("Inference Chain: test-chain");
      expect(text).toContain("Query: test query");
      expect(text).toContain("PREMISE");
      expect(text).toContain("A knows C");
    });
  });

  describe("renderJson", () => {
    it("should render chain as JSON", () => {
      const chain = {
        chainId: "test-chain",
        query: "test query",
        steps: [],
        result: [],
        confidence: 0.85,
        timestamp: Date.now(),
        version: "1.0.0",
      };

      const json = visualizer.renderJson(chain);

      expect(json).toHaveProperty("chainId", "test-chain");
      expect(json).toHaveProperty("query", "test query");
      expect(json).toHaveProperty("confidence", 0.85);
    });
  });

  describe("renderMermaid", () => {
    it("should render chain as Mermaid flowchart", () => {
      const chain = {
        chainId: "test-chain",
        query: "test query",
        steps: [],
        result: [
          {
            id: "k1",
            type: DerivationType.TRANSITIVE,
            subject: "A",
            predicate: "knows",
            object: "C",
            confidence: 0.85,
            chainId: "test-chain",
            sourceMemoryIds: [],
            timestamp: Date.now(),
          },
        ],
        confidence: 0.85,
        timestamp: Date.now(),
        version: "1.0.0",
      };

      const mermaid = visualizer.renderMermaid(chain);

      expect(mermaid).toContain("```mermaid");
      expect(mermaid).toContain("flowchart TD");
    });
  });
});
