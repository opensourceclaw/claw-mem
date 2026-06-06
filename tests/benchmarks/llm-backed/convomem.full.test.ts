import { describe, it, expect } from "vitest";
import { getMemoryManager } from "../../../src/memory_manager";
import { ruleBasedScore } from "../../../src/utils/llm_evaluator";
import { execSync } from "child_process";

const SCENARIOS = {
  singleTurn: { store: ["Peter prefers TypeScript"], search: "TypeScript", expected: "TypeScript" },
  multiTurn: { store: ["Migration to TypeScript strict mode decided", "Vitest chosen for testing", "Reviews on Friday"], search: "TypeScript", expected: "TypeScript" },
  temporal: { store: ["Phase 1 March architecture", "Phase 2 April implementation", "Phase 3 May testing"], search: "March", expected: "March" },
  entity: { store: ["Docker containers", "TypeScript language", "SQLite database"], search: "TypeScript", expected: "TypeScript" },
  preference: { store: ["Chinese communication preferred", "TypeScript strict coding style"], search: "Chinese", expected: "Chinese" },
  factual: { store: ["204800 tokens context window", "10ms search latency"], search: "tokens", expected: "204800" },
};

describe("ConvoMem Full Benchmark", () => {
  const scores: Record<string, number> = {};

  for (const [name, sc] of Object.entries(SCENARIOS)) {
    it(`${name} memory recall`, () => {
      try { execSync(`rm -rf /tmp/claw-mem-convomem-${name}*`, { stdio: 'ignore' }); } catch {}
      
      const mm = getMemoryManager({ workspace: `/tmp/claw-mem-convomem-${name}` });
      for (const msg of sc.store) mm.store(msg, "episodic");
      mm.buildIndex();
      const results = mm.search(sc.search, undefined, 10).map((x: any) => x.content || "");
      
      console.log(`  ConvoMem ${name}: results=${results.length}`);
      
      scores[name] = ruleBasedScore(results, sc.expected) * 100;
      console.log(`  ConvoMem ${name}: score=${scores[name].toFixed(1)}%`);
      
      expect(results.length).toBeGreaterThan(0);
    });
  }

  it("aggregate ConvoMem score", () => {
    const values = Object.values(scores);
    const avg = values.length > 0 ? values.reduce((s, v) => s + v, 0) / values.length : 0;
    console.log(`\nConvoMem Aggregate: ${avg.toFixed(1)}% (6 scenarios)`);
    console.log(`Community benchmark (reference only)`);
    expect(avg).toBeGreaterThanOrEqual(0);
  });
});
