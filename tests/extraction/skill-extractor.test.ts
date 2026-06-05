import { describe, it, expect } from "vitest";
import { SkillExtractor, type Skill, type SkillExtractionMode } from "../../src/extraction/skill_extractor";
import type { Triplet } from "../../src/extraction/openie_extractor";

// ── Helpers ─────────────────────────────────────────────────────────────

function makeTriplets(subject: string, predicate: string, objects: string[]): Triplet[] {
  return objects.map((obj) => ({ subject, predicate, object: obj, confidence: 1.0 }));
}

class MockLLM {
  private response: string = "";

  setResponse(json: string): void {
    this.response = json;
  }

  generate(_opts: { prompt: string; system?: string; max_tokens?: number }): string {
    return this.response;
  }
}

// ── Tests ───────────────────────────────────────────────────────────────

describe("SkillExtractor", () => {
  describe("rule mode", () => {
    it("extracts skills from grouped triplets", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("Alice", "负责", ["项目A", "项目B", "项目C"]);
      const skills = extractor.extract(triplets);

      expect(skills.length).toBeGreaterThanOrEqual(1);
      expect(skills[0].name).toBeDefined();
      expect(skills[0].steps.length).toBeGreaterThanOrEqual(1);
      expect(skills[0].applicability).toBeDefined();
      expect(skills[0].confidence).toBeGreaterThan(0);
      expect(skills[0].source).toBe("rule");
    });

    it("returns empty for insufficient triplets", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("Bob", "开发", ["feature1"]);
      expect(extractor.extract(triplets)).toHaveLength(0);
    });

    it("returns empty for empty input", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      expect(extractor.extract([])).toHaveLength(0);
    });

    it("uses known template for '开发' predicate", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("Team", "开发", ["API", "UI"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].name).toBe("软件开发");
    });

    it("uses known template for 'is' predicate", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("Python", "is", ["language", "tool"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].name).toBe("Identity Classification");
    });

    it("uses known template for 'has' predicate", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("Server", "has", ["CPU", "RAM"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].name).toBe("Possession Pattern");
    });

    it("uses generic template for unknown predicate", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("System", "custom_action", ["result1", "result2"]);
      const skills = extractor.extract(triplets);
      expect(skills.length).toBeGreaterThanOrEqual(1);
      expect(skills[0].name).toContain("System");
      expect(skills[0].source).toBe("rule");
    });

    it("computes compression ratio", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const triplets = makeTriplets("Alice", "负责", ["A", "B"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].compression_ratio).toBeGreaterThan(0);
      expect(skills[0].source_triplets).toBe(2);
    });

    it("confidence increases with more triplets", () => {
      const extractor = new SkillExtractor(undefined, "rule");
      const few = makeTriplets("A", "负责", ["1", "2"]);
      const many = makeTriplets("B", "负责", ["1", "2", "3", "4", "5", "6"]);
      const s1 = extractor.extract(few);
      const s2 = extractor.extract(many);
      // More triplets → higher confidence
      expect(s2[0].confidence).toBeGreaterThan(s1[0].confidence);
    });
  });

  describe("llm mode", () => {
    it("extracts skills using LLM provider", () => {
      const llm = new MockLLM();
      llm.setResponse(JSON.stringify([{
        name: "Test Skill",
        steps: ["Step 1", "Step 2"],
        applicability: "For testing",
        confidence: 0.9,
      }]));
      const extractor = new SkillExtractor(llm, "llm");
      const triplets = makeTriplets("Test", "action", ["result1", "result2"]);
      const skills = extractor.extract(triplets);

      expect(skills.length).toBeGreaterThanOrEqual(1);
      expect(skills[0].name).toBe("Test Skill");
      expect(skills[0].source).toBe("llm");
    });

    it("returns empty when LLM returns empty", () => {
      const llm = new MockLLM();
      llm.setResponse("[]");
      const extractor = new SkillExtractor(llm, "llm");
      const triplets = makeTriplets("Test", "action", ["r1", "r2"]);
      expect(extractor.extract(triplets)).toHaveLength(0);
    });

    it("returns empty when no LLM provider set", () => {
      const extractor = new SkillExtractor(undefined, "llm");
      const triplets = makeTriplets("Test", "action", ["r1", "r2"]);
      expect(extractor.extract(triplets)).toHaveLength(0);
    });

    it("handles LLM errors gracefully", () => {
      const badLLM = {
        generate: () => { throw new Error("LLM error"); },
      };
      const extractor = new SkillExtractor(badLLM, "llm");
      const triplets = makeTriplets("Test", "action", ["r1", "r2"]);
      expect(extractor.extract(triplets)).toHaveLength(0);
    });

    it("parses JSON with markdown fence", () => {
      const llm = new MockLLM();
      llm.setResponse("```json\n[{\"name\":\"Fenced Skill\",\"steps\":[\"S1\"],\"applicability\":\"test\",\"confidence\":0.8}]\n```");
      const extractor = new SkillExtractor(llm, "llm");
      const triplets = makeTriplets("X", "Y", ["a", "b"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].name).toBe("Fenced Skill");
    });
  });

  describe("auto mode", () => {
    it("uses LLM when available", () => {
      const llm = new MockLLM();
      llm.setResponse(JSON.stringify([{
        name: "Auto Skill",
        steps: ["Step 1"],
        applicability: "test",
        confidence: 0.85,
      }]));
      const extractor = new SkillExtractor(llm, "auto");
      const triplets = makeTriplets("Auto", "works", ["a", "b"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].name).toBe("Auto Skill");
      expect(skills[0].source).toBe("llm");
    });

    it("falls back to rule when LLM returns empty", () => {
      const llm = new MockLLM();
      llm.setResponse("[]");
      const extractor = new SkillExtractor(llm, "auto");
      const triplets = makeTriplets("Fallback", "负责", ["a", "b"]);
      const skills = extractor.extract(triplets);
      expect(skills.length).toBeGreaterThanOrEqual(1);
      expect(skills[0].source).toBe("rule");
    });

    it("uses rule when no LLM provider", () => {
      const extractor = new SkillExtractor(undefined, "auto");
      const triplets = makeTriplets("NoLLM", "负责", ["a", "b"]);
      const skills = extractor.extract(triplets);
      expect(skills[0].source).toBe("rule");
    });
  });

  describe("mode property", () => {
    it("returns configured mode", () => {
      expect(new SkillExtractor(undefined, "rule").mode).toBe("rule");
      expect(new SkillExtractor(undefined, "llm").mode).toBe("llm");
      expect(new SkillExtractor(undefined, "auto").mode).toBe("auto");
    });

    it("defaults to auto for invalid mode", () => {
      expect(new SkillExtractor(undefined, "invalid" as SkillExtractionMode).mode).toBe("auto");
    });
  });
});
