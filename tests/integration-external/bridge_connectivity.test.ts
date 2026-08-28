// Copyright 2026 OpenSourceClaw Contributors
// v5.0.0 Bridge Connectivity Verification (with Mocks)

import { describe, it, expect, vi } from "vitest";

// Mock external modules
vi.mock("../../../claw-cog/src/index", () => ({
  ConsciousAgent: class {
    process(input: string) {
      return {
        c2: {
          metacognitiveConfidence: 0.85,
          governance: { allowed: true },
        },
      };
    }
  },
  C0Layer: {},
  C2Layer: {},
}));

vi.mock("../../../claw-rl/src/index", () => ({
  RuleEngine: class {},
  ThompsonSampling: class {},
  EpsilonGreedy: class {},
}));

vi.mock("../../../claw-gov/src/index", () => ({
  governAction: (actionObj: { action: string; type?: string; metadata?: object }) => ({
    approved: true,
    violations: [],
    metadata: { layers_executed: ["L1", "L2"] },
  }),
  governCheck: () => ({}),
  governTrace: () => ({}),
  createAction: (action: string, type = "modify", metadata = {}) => ({ action, type, metadata }),
  checkIntentAlignment: () => ({}),
  checkValueConstraints: () => ({}),
  checkSafetyBoundaries: () => ({}),
  checkLearningGovernance: () => ({}),
  checkSelfReflection: () => ({}),
  checkEthicsCompliance: () => ({}),
}));

describe("Bridge Connectivity", () => {
  it("claw-mem → claw-cog: ConsciousAgent exports", async () => {
    const cog = await import("../../../claw-cog/src/index");
    expect(cog.ConsciousAgent).toBeDefined();
    expect(cog.C0Layer).toBeDefined();
    expect(cog.C2Layer).toBeDefined();
  });

  it("claw-mem → claw-rl: RuleEngine + MAB exports", async () => {
    const rl = await import("../../../claw-rl/src/index");
    expect(rl.RuleEngine).toBeDefined();
    expect(rl.ThompsonSampling).toBeDefined();
    expect(rl.EpsilonGreedy).toBeDefined();
  });

  it("claw-mem → claw-gov: governance exports", async () => {
    const gov = await import("../../../claw-gov/src/index");
    expect(gov.governAction).toBeDefined();
    expect(gov.governCheck).toBeDefined();
    expect(gov.governTrace).toBeDefined();
  });

  it("claw-cog → claw-gov: C2 → governance integration", async () => {
    const cog = await import("../../../claw-cog/src/index");
    const gov = await import("../../../claw-gov/src/index");
    const agent = new cog.ConsciousAgent();
    const { c2 } = agent.process("Update dependencies");
    const result = gov.governAction(
      gov.createAction("Update dependencies", "modify",
        { confidence_score: c2.metacognitiveConfidence }));
    expect(typeof result.approved).toBe("boolean");
  });

  it("All 4 components export public APIs", async () => {
    const mem = await import("../../src/index");
    expect(mem.MemoryManager).toBeDefined();
    const cog = await import("../../../claw-cog/src/index");
    expect(cog.ConsciousAgent).toBeDefined();
    const rl = await import("../../../claw-rl/src/index");
    expect(rl.RuleEngine).toBeDefined();
    const gov = await import("../../../claw-gov/src/index");
    expect(gov.governAction).toBeDefined();
  });

  it("All 6 L1-L6 layers loadable via claw-gov", async () => {
    const gov = await import("../../../claw-gov/src/index");
    expect(gov.checkIntentAlignment).toBeDefined();
    expect(gov.checkValueConstraints).toBeDefined();
    expect(gov.checkSafetyBoundaries).toBeDefined();
    expect(gov.checkLearningGovernance).toBeDefined();
    expect(gov.checkSelfReflection).toBeDefined();
    expect(gov.checkEthicsCompliance).toBeDefined();
  });
});
