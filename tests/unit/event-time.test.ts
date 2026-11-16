// Copyright 2026 OpenSourceClaw Contributors
// v7.10.0 (ADR-007 §3): eventTime ?? created_at drives time filtering,
// time ordering, hybrid timeRange filtering, and memory_stats coverage.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";

const ALPHA = "timeline marker alpha";
const BETA = "timeline marker beta";
const GAMMA = "timeline marker gamma";

function textsOf(rows: Array<Record<string, unknown>>): string[] {
  return rows.map((r) => String(r.content ?? r.text ?? ""));
}

describe("ADR-007 eventTime semantics", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-eventtime-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });

    manager.store(ALPHA, "episodic", [], {}, {
      eventTime: "2026-01-01",
      evidence: [{ span: "alpha", sourceRefs: [] }],
    });
    manager.store(BETA, "episodic", [], {}, { eventTime: "2026-06-01" });
    manager.store(GAMMA, "episodic", []);

    manager.buildIndex();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("decorates hits with eventTime/evidence; created_at-only records stay bare", () => {
    const rows = manager.search("timeline marker");
    expect(rows).toHaveLength(3);

    const byText = new Map(rows.map((r) => [String(r.content ?? r.text ?? ""), r]));
    expect(byText.get(ALPHA)!.eventTime).toBe("2026-01-01");
    expect(byText.get(ALPHA)!.evidence).toEqual([{ span: "alpha", sourceRefs: [] }]);
    expect(byText.get(BETA)!.eventTime).toBe("2026-06-01");
    expect("eventTime" in byText.get(GAMMA)!).toBe(false);
    expect("evidence" in byText.get(GAMMA)!).toBe(false);
  });

  it("filters by eventTime ?? created_at (since)", () => {
    const texts = textsOf(manager.search("timeline marker", undefined, 10, { since: "2026-05-01" }));
    expect(texts).toContain(BETA);
    expect(texts).toContain(GAMMA); // no eventTime → created_at (now)
    expect(texts).not.toContain(ALPHA);
  });

  it("filters by eventTime ?? created_at (until)", () => {
    const texts = textsOf(manager.search("timeline marker", undefined, 10, { until: "2026-02-01" }));
    expect(texts).toEqual([ALPHA]);
  });

  it("orders by effective time when orderBy=time", () => {
    const texts = textsOf(manager.search("timeline marker", undefined, 10, { orderBy: "time" }));
    expect(texts).toEqual([GAMMA, BETA, ALPHA]);
  });

  it("applies the same semantics on the substring fallback path", () => {
    (manager as any)._index.built = false; // force the full-scan path
    const texts = textsOf(manager.search("timeline marker", undefined, 10, { since: "2026-05-01" }));
    expect(texts.sort()).toEqual([BETA, GAMMA].sort());
  });

  it("applies effective-time ranges to hybrid search", () => {
    const all = manager.hybridSearch("timeline marker", { topK: 10 });
    expect(all.results.length).toBe(3);

    const ranged = manager.hybridSearch("timeline marker", {
      topK: 10,
      filters: { timeRange: { start: "2026-05-01" } },
    });
    const texts = ranged.results.map((r) => r.text);
    expect(texts).toContain(BETA);
    expect(texts).toContain(GAMMA);
    expect(texts).not.toContain(ALPHA);
  });

  it("reports evidence/eventTime coverage in memory_stats", () => {
    const stats = manager.getStats() as any;
    expect(stats.evidence.sampleSize).toBe(3);
    expect(stats.evidence.withEvidence).toBe(1);
    expect(stats.evidence.withEventTime).toBe(2);
    expect(stats.evidence.coverage).toBeCloseTo(1 / 3, 5);
  });
});
