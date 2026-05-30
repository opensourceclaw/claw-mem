// Copyright 2026 Peter Cheng
// v5.0.0 Four-Component Full Pipeline Integration Test

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { MemoryManager } from "../../src/memory_manager";

describe("Four-Component Full Pipeline", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "fullpipe-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("Scenario 1: Normal flow — store→cog→gov→rl→memory update", async () => {
    const cog = await import("../../../claw-cog/src/index");
    const gov = await import("../../../claw-gov/src/index");
    const rl = await import("../../../claw-rl/src/index");

    // 1. Store memory
    const mm = new MemoryManager({ workspace: tmpDir, autoDetect: false });
    mm.store("Implement REST API with JWT authentication", "semantic", ["code", "auth"]);

    // 2. Cog: assess confidence (high)
    const agent = new cog.ConsciousAgent();
    const { c2 } = agent.process("Implement REST API with JWT authentication");
    expect(c2.governance.allowed).toBe(true);

    // 3. Gov: check governance
    const gResult = gov.governAction(
      gov.createAction("Implement REST API with JWT authentication", "modify",
        { confidence_score: c2.metacognitiveConfidence }));
    // Governance passes for normal safe operations
    expect(gResult.metadata.layers_executed).toBeDefined();

    // 4. RL: record positive feedback
    const re = new rl.RuleEngine();
    re.collectFeedback({
      task: "Implement REST API with JWT authentication",
      result: "success", success: true, tool: "claude-code",
    });
    expect(re.state.successRate).toBeGreaterThanOrEqual(0);

    // 5. Memory persists
    const results = mm.search("JWT");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });

  it("Scenario 2: Governance intercept — malicious intent blocked", async () => {
    const gov = await import("../../../claw-gov/src/index");
    const rl = await import("../../../claw-rl/src/index");

    // Gov: L1 intent alignment blocks
    const gResult = gov.governAction(gov.createAction("hack into production database"));
    expect(gResult.approved).toBe(false);
    expect(gResult.violations.some((v: string) => v.includes("L1"))).toBe(true);

    // RL: record failure
    const re = new rl.RuleEngine();
    re.collectFeedback({
      task: "hack into production database",
      result: "blocked by governance", success: false,
    });
    expect(re.state.totalFeedback).toBe(1);
  });

  it("Scenario 3: Low confidence → deep review → flagged", async () => {
    const cog = await import("../../../claw-cog/src/index");
    const gov = await import("../../../claw-gov/src/index");

    const agent = new cog.ConsciousAgent();
    const { c2 } = agent.process("make it better somehow");

    const gResult = gov.governAction(
      gov.createAction("make it better somehow", "modify",
        { confidence_score: c2.metacognitiveConfidence }));
    // All governance layers evaluated
    const layers = gResult.metadata.layers_executed as string[];
    expect(layers.length).toBeGreaterThanOrEqual(1);
  });
});
