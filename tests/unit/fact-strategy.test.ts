// Fact Strategy Unit Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { FactStrategy } from "../../src/storage/strategies/fact.js";
import { EpisodicStorage } from "../../src/storage/episodic.js";
import { EntityIndex } from "../../src/entity/entity-index.js";
import { VersionChain } from "../../src/storage/version-chain.js";
import type { StrategyContext, MemoryRecord } from "../../src/storage/strategy-registry.js";

describe("FactStrategy", () => {
  let tmpDir: string;
  let strategy: FactStrategy;
  let context: StrategyContext;
  let entityIndex: EntityIndex;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-fact-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    entityIndex = new EntityIndex();
    strategy = new FactStrategy();
    context = {
      episodic: new EpisodicStorage(tmpDir),
      semantic: {} as any,
      procedural: {} as any,
      entityIndex,
      versionChain: new VersionChain(tmpDir),
      workspace: tmpDir,
    };
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  function createFact(content: string): MemoryRecord {
    return {
      id: `fact_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      text: content,
      memory_type: "fact",
      created_at: new Date().toISOString(),
      metadata: {},
      tags: ["fact"],
    };
  }

  it("stores fact and indexes entities", () => {
    const record = createFact("claw-mem v6.31.0 adds strategy registry");
    const result = strategy.store(record, context);

    expect(result.strategy).toBe("fact");

    // Entity should be indexed
    const entityResult = entityIndex.search("clawmem");
    expect(entityResult).not.toBeNull();
  });

  it("retrieves facts by keyword", () => {
    strategy.store(createFact("TypeScript is used for development"), context);
    strategy.store(createFact("Docker containers for deployment"), context);

    const results = strategy.retrieve("TypeScript", { limit: 10 }, context);
    expect(results.length).toBe(1);
    expect(results[0].text).toContain("TypeScript");
  });

  it("retrieves facts by entity", () => {
    strategy.store(createFact("claw-mem bug fix #42"), context);
    strategy.store(createFact("Other unrelated fact"), context);

    const results = strategy.retrieve("clawmem", { limit: 10 }, context);
    expect(results.length).toBeGreaterThan(0);
  });

  it("works without entity index", () => {
    context.entityIndex = null;

    const record = createFact("Test fact without entity index");
    const result = strategy.store(record, context);

    expect(result.strategy).toBe("fact");
  });

  it("returns stats", () => {
    strategy.store(createFact("Fact 1"), context);
    strategy.store(createFact("Fact 2"), context);

    const stats = strategy.getStats(context);
    expect(stats.name).toBe("fact");
    expect(stats.memoryCount).toBeGreaterThan(0);
  });
});