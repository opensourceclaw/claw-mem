// T3 policy composition tests (v7.8.0, design §4 — CLC methodology, read-only projection)
// describeActivePolicies reads out current effective values; apply accepts only a
// verbatim round-trip (zero behaviour change this version); experiment records are
// append-only JSONL under memory/policy-experiments/.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import {
  describeActivePolicies,
  apply,
  appendExperimentRecord,
  listExperimentRecords,
  emptyRunSample,
  POLICY_COMPOSITION_FILE,
} from "../../src/index.js";

describe("describeActivePolicies (design §4.1)", () => {
  it("#F1 slot set: 6 slots across retain/store/retire, all enabled", () => {
    const comp = describeActivePolicies();
    expect(comp.slots.map((s) => s.id).sort()).toEqual([
      "retain.importance-scoring",
      "retain.usage-boost",
      "retire.grace-period",
      "retire.hit-window",
      "retire.retention-decay",
      "store.layer-routing",
    ].sort());
    expect(comp.slots.map((s) => s.dimension).sort()).toEqual(
      ["retain", "retain", "retire", "retire", "retire", "store"]
    );
    expect(comp.slots.every((s) => s.enabled)).toBe(true);
    expect(comp.slots.every((s) => typeof s.params === "object")).toBe(true);
  });

  it("#F2 params are the source values (read-out, not re-declared): ρ/streak/grace/HIT/weights", () => {
    const byId = Object.fromEntries(describeActivePolicies().slots.map((s) => [s.id, s.params]));
    expect(byId["retire.retention-decay"]).toEqual({ rho: 0.85, maxStreak: 5 });
    expect(byId["retire.grace-period"]).toEqual({ gracePeriodDays: 30 });
    expect(byId["retire.hit-window"]).toEqual({ hitWindow: 5 });
    expect(byId["retain.usage-boost"]).toEqual({
      selectedBoost: 0.1,
      successScore: 0.75,
      failureScore: 0.3,
      neutralScore: 0.5,
    });
    expect(byId["retain.importance-scoring"]).toMatchObject({
      length: 0.2, keywords: 0.3, metadata: 0.2, recency: 0.3,
    });
    expect(byId["store.layer-routing"]).toEqual({ routes: "episodic|semantic|procedural" });
  });

  it("#F5 config override: read from {workspace}/memory/policy-composition.json; unknown slots never projected; corrupt config falls back", () => {
    const ws = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-policy-ws-"));
    try {
      expect(describeActivePolicies(ws)).toEqual(describeActivePolicies()); // no config → spot values
      const file = path.join(ws, POLICY_COMPOSITION_FILE);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, JSON.stringify({
        slots: [
          { id: "retire.hit-window", dimension: "retire", params: { hitWindow: 4 }, enabled: true },
          { id: "retire.grace-period", dimension: "retire", params: { gracePeriodDays: 14 }, enabled: false },
          { id: "does.not.exist", dimension: "retire", params: { x: 1 }, enabled: true },
        ],
      }), "utf-8");

      const overridden = describeActivePolicies(ws);
      const byId = Object.fromEntries(overridden.slots.map((s) => [s.id, s]));
      expect(byId["retire.hit-window"].params).toEqual({ hitWindow: 4 });
      expect(byId["retire.grace-period"]).toEqual({
        id: "retire.grace-period", dimension: "retire", params: { gracePeriodDays: 14 }, enabled: false,
      });
      expect(byId["does.not.exist"]).toBeUndefined(); // unknown id never projected
      expect(byId["retire.retention-decay"].params).toEqual({ rho: 0.85, maxStreak: 5 }); // untouched slot keeps spot value

      fs.writeFileSync(file, "{corrupt", "utf-8");
      expect(describeActivePolicies(ws)).toEqual(describeActivePolicies()); // corrupt → spot values, never throws
    } finally {
      fs.rmSync(ws, { recursive: true, force: true });
    }
  });

  it("#F3 apply: verbatim round-trip is a no-op (slot order irrelevant); any param drift is refused", () => {
    expect(apply(describeActivePolicies())).toEqual({ ok: true, noop: true });
    const shuffled = { slots: [...describeActivePolicies().slots].reverse() };
    expect(apply(shuffled)).toEqual({ ok: true, noop: true });

    const drifted = describeActivePolicies();
    const slot = drifted.slots.find((s) => s.id === "retire.hit-window")!;
    slot.params.hitWindow = 4;
    const r = apply(drifted);
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.reason).toContain("not supported");
  });
});

describe("factor experiment protocol (design §4.2)", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-policy-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("#F4 experiment records land append-only; corrupt lines skipped, reads never throw", () => {
    expect(listExperimentRecords(tmpDir)).toEqual([]);
    const p1 = appendExperimentRecord(tmpDir, emptyRunSample("2026-09-14T00:00:00.000Z"));
    expect(p1.startsWith(path.join(tmpDir, "memory", "policy-experiments"))).toBe(true);
    appendExperimentRecord(tmpDir, { ...emptyRunSample("2026-09-15T00:00:00.000Z"), experimentId: "dry-run-001" });

    const recs = listExperimentRecords(tmpDir);
    expect(recs.map((r) => r.startedAt)).toEqual(["2026-09-14T00:00:00.000Z", "2026-09-15T00:00:00.000Z"]);
    expect(recs.map((r) => r.experimentId)).toEqual(["dry-run-000", "dry-run-001"]);
    expect(recs[0].factor).toEqual({ slotId: "retire.hit-window", param: "hitWindow", from: 5, to: 5 });
    expect(recs[0].windowDays).toBe(7);
    expect(recs[0].observations.note).toContain("no conclusion");

    // append-only: two records = two files, nothing rewritten
    const dir = path.join(tmpDir, "memory", "policy-experiments");
    expect(fs.readdirSync(dir).filter((f) => f.endsWith(".jsonl"))).toHaveLength(2);

    // a corrupt line never breaks reads
    fs.appendFileSync(path.join(dir, "corrupt.jsonl"), "{not json\n", "utf-8");
    expect(listExperimentRecords(tmpDir)).toHaveLength(2);
  });
});
