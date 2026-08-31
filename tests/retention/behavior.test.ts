// claw-mem v7.5.0 — Retention score behavior tests (ADR-002)
//
// Black-box behavioral verification through the public MemoryManager API:
//  1. old-but-commonly-used memory stays high and ranks no worse than control
//  2. old-but-unused memory decays and drops in fused ranking
//  3. selection clears the missed streak and recovers the score
//  4. retentionEnabled=false behaves exactly like v7.4.2
// Licensed under the Apache License, Version 2.0

import { afterEach, describe, expect, it } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { MemoryManager } from "../../src/memory_manager";
import { MemoryConfig } from "../../src/config";

const RHO = 0.85;

interface TestContext {
  manager: MemoryManager;
  dir: string;
}

function makeManager(retentionEnabled = true): TestContext {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-retention-"));
  const config = new MemoryConfig({ autoDetect: false, workspace: dir, retentionEnabled });
  const manager = new MemoryManager({ workspace: dir, config });
  return { manager, dir };
}

/** Write a memory entry dated `daysAgo` directly into episodic storage. */
function writeAgedMemory(ctx: TestContext, daysAgo: number, id: string, content: string): void {
  const date = new Date(Date.now() - daysAgo * 86400000);
  const file = path.join(ctx.manager.workspace, "memory", `${date.toISOString().slice(0, 10)}.md`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(
    file,
    `<!-- tags: retention-test; id: ${id} -->\n${content} <!-- ts:${date.toISOString()} -->\n`,
    "utf-8",
  );
}

/** Read the retention state persisted on a search result record. */
function retentionOf(record: Record<string, unknown>): { score: number; missedStreak: number } {
  const meta = (record.metadata ?? {}) as Record<string, unknown>;
  const raw = meta.retention;
  const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
  return { score: parsed.score as number, missedStreak: parsed.missedStreak as number };
}

const cleanups: Array<() => void> = [];
afterEach(() => {
  while (cleanups.length) cleanups.pop()!();
});

describe("retention behavior (v7.5.0)", () => {
  it("old but commonly used: 5 hits in a row keep score >= 0.75 and rank no worse than control", () => {
    const ctx = makeManager();
    cleanups.push(() => fs.rmSync(ctx.dir, { recursive: true, force: true }));
    const { manager } = ctx;

    // m1: 30 days old, commonly retrieved; m2: fresh, same topic
    writeAgedMemory(ctx, 30, "m1", "celestial alpha config");
    writeAgedMemory(ctx, 0, "m2", "celestial beta config");

    manager.buildIndex();
    manager.hybridRetriever; // force hybrid retriever creation (real fusion path)

    // 5 consecutive searches both hit and return m1 (topK covers both)
    for (let i = 0; i < 5; i++) {
      const results = manager.search(`celestial ${i}`, undefined, 10);
      expect(results.map((r) => (r as any).id ?? (r as any).metadata?.id)).toContain("m1");
    }

    // retention of m1 read via a fresh search result record
    const rec = manager.search("celestial", undefined, 10)
      .find((r) => (r as any).id === "m1") as Record<string, unknown>;
    const r = retentionOf(rec);
    expect(r.score).toBeGreaterThanOrEqual(0.75);
    expect(r.missedStreak).toBe(0);

    // fused ranking: with retention, m1's position is not worse than without
    const control = manager.hybridSearch("celestial", { topK: 2, fusion: { retentionWeight: 0 } });
    const experimental = manager.hybridSearch("celestial", { topK: 2 });
    const ids = (r: { results: Array<{ id: string }> }) => r.results.map((x) => x.id);
    const controlPos = ids(control).indexOf("m1");
    const expPos = ids(experimental).indexOf("m1");
    expect(controlPos).toBeGreaterThanOrEqual(0);
    expect(expPos).toBeLessThanOrEqual(controlPos);
  });

  it("old but unused: 5 candidate-misses decay score to <= 0.5 * initial and lower fused score", () => {
    const ctx = makeManager();
    cleanups.push(() => fs.rmSync(ctx.dir, { recursive: true, force: true }));
    const { manager } = ctx;

    // m3: 30 days old, always outranked by m4 (fresh) → candidate-missed
    writeAgedMemory(ctx, 30, "m3", "shared omicron config");
    writeAgedMemory(ctx, 0, "m4", "shared epsilon config");
    manager.buildIndex();
    manager.hybridRetriever; // force hybrid retriever creation (real fusion path)

    // 5 rounds: both match "shared", topK=1 → m4 selected, m3 missed
    for (let i = 0; i < 5; i++) {
      const results = manager.search(`shared ${i}`, undefined, 1);
      expect(results.length).toBe(1);
      expect((results[0] as any).id).toBe("m4");
    }

    // read m3 via hybrid (both returned now): retention field is the
    // pre-event score — 5 misses → 0.5·ρ^15 ≈ 0.044 ≤ 0.5·initial (0.25)
    const hybrid = manager.hybridSearch("shared", { topK: 2 });
    const m3 = hybrid.results.find((x) => x.id === "m3")!;
    const m4 = hybrid.results.find((x) => x.id === "m4")!;
    expect(m3.retention).toBeLessThan(0.5 * 0.5); // ≤ 0.5·neutral 0.5
    expect(m3.retention).toBeCloseTo(0.5 * Math.pow(RHO, 15), 4);

    // fused ranking impact: low retention widens m3's fused-score distance
    // to the high-retention m4 (selected every round) vs the no-retention control
    const control = manager.hybridSearch("shared", { topK: 2, fusion: { retentionWeight: 0 } });
    const controlM3 = control.results.find((x) => x.id === "m3")!;
    const controlM4 = control.results.find((x) => x.id === "m4")!;
    const gapExp = (m4.fusedScore as number) - (m3.fusedScore as number);
    const gapCtl = (controlM4.fusedScore as number) - (controlM3.fusedScore as number);
    expect(gapExp).toBeGreaterThan(gapCtl);
  });

  it("selection clears the missed streak and recovers the score", () => {
    const ctx = makeManager();
    cleanups.push(() => fs.rmSync(ctx.dir, { recursive: true, force: true }));
    const { manager } = ctx;

    writeAgedMemory(ctx, 30, "m5", "solstice config");
    writeAgedMemory(ctx, 0, "m6", "solstice config v2");
    manager.buildIndex();
    manager.hybridRetriever; // force hybrid retriever creation (real fusion path)

    // decay m5 with 5 candidate misses (topK=1 always selects fresh m6)
    for (let i = 0; i < 5; i++) manager.search(`solstice ${i}`, undefined, 1);

    // first read (hybrid) reports the pre-event score after 5 misses: 0.5·ρ^15
    const read1 = manager.hybridSearch("solstice", { topK: 2 });
    const m5first = read1.results.find((x) => x.id === "m5")!;
    expect(m5first.retention).toBeCloseTo(0.5 * Math.pow(RHO, 15), 4);
    expect(m5first.retention).toBeLessThan(0.25);

    // selection clears the streak and recovers the score:
    // read1 selected m5 (+0.1), this search selects it again (+0.1)
    const rec = manager.search("solstice only", undefined, 10)
      .find((r) => (r as any).id === "m5") as Record<string, unknown>;
    const after = retentionOf(rec);
    expect(after.missedStreak).toBe(0);
    expect(after.score).toBeGreaterThan(m5first.retention as number);
    expect(after.score).toBeCloseTo((m5first.retention as number) + 0.2, 5);
  });

  it("retentionEnabled=false: search/hybridSearch behave exactly like v7.4.2", () => {
    const ctx = makeManager(false);
    cleanups.push(() => fs.rmSync(ctx.dir, { recursive: true, force: true }));
    const { manager } = ctx;

    manager.store("legacy memory alpha", "episodic", [], {});
    manager.store("legacy memory beta", "episodic", [], {});
    manager.buildIndex();
    manager.hybridRetriever; // force hybrid retriever creation (real fusion path)

    // repeated retrieval creates no retention state, no metadata writes
    for (let i = 0; i < 3; i++) {
      const results = manager.search("legacy", undefined, 10);
      expect(results.length).toBe(2);
      for (const r of results) {
        expect((r.metadata ?? {}) as Record<string, unknown>).not.toHaveProperty("retention");
      }
    }
    const stats = manager.getStats();
    expect((stats.retention as { count: number }).count).toBe(0);

    // hybrid results carry no retention and fuse identically to retentionWeight: 0
    const defaultFusion = manager.hybridSearch("legacy", { topK: 2 });
    const zeroRetention = manager.hybridSearch("legacy", { topK: 2, fusion: { retentionWeight: 0 } });
    for (const r of defaultFusion.results) {
      expect(r).not.toHaveProperty("retention");
    }
    expect(JSON.stringify(defaultFusion.results.map((r) => r.id)))
      .toBe(JSON.stringify(zeroRetention.results.map((r) => r.id)));
    // order-equivalent fused scores: default fusion adds a constant
    // retention term (0.2 × neutral 0.5 = 0.1) over retentionWeight 0
    for (let i = 0; i < defaultFusion.results.length; i++) {
      const a = defaultFusion.results[i];
      const b = zeroRetention.results[i];
      if (a.id === b.id) {
        expect(a.fusedScore).toBeCloseTo(b.fusedScore + 0.1, 4);
      }
    }
  });

  it("cached search hits still update retention (PRD §6 risk item 3)", () => {
    const ctx = makeManager();
    cleanups.push(() => fs.rmSync(ctx.dir, { recursive: true, force: true }));
    const { manager } = ctx;

    manager.store("cache hit memory zeta", "episodic", [], {});
    manager.buildIndex();

    // first search populates the cache; second (within TTL) hits it
    manager.search("cache hit", undefined, 10);
    const rec = manager.search("cache hit", undefined, 10)[0] as Record<string, unknown>;
    const r = retentionOf(rec);
    // two boosts (cache miss + cache hit) → 0.5 + 0.2
    expect(r.score).toBeCloseTo(0.7, 5);
    expect(r.missedStreak).toBe(0);
  });
});
