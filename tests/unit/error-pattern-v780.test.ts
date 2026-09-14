// Error Pattern Card v7.8.0 Tests — dual-side cards (T1) + statusKey placeholder (T2)
// + lifecycle (T4) + v7.6/v7.7 compatibility locks.
// Design: docs/design/v7.8.0-strategy-cards-design.md §2/§3/§5/§7
// Contract: docs/contracts/error-card-injection-contract.md §6

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import { encodeCardMetadata } from "../../src/storage/strategies/error-pattern-card.js";
import type { ErrorPatternCardInput, SuccessStrategyPayload } from "../../src/types.js";

describe("dual-side cards (v7.8.0 T1)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-780-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  function legacyCard(overrides: Partial<ErrorPatternCardInput> = {}): ErrorPatternCardInput {
    return {
      cardId: `epc:card-${Math.random().toString(36).slice(2, 8)}`,
      errorSignature: {
        trigger: "before deploying a schema change",
        symptom: "deployment succeeds but runtime rejects new fields",
      },
      rootCauseCategory: "skill-defect",
      resolution: "run schema validation against the live environment before every deployment",
      provenance: { source: "remember" },
      ...overrides,
    };
  }

  const APPLICABLE = "when a transient network call fails";
  function successCard(overrides: Partial<ErrorPatternCardInput> = {}): ErrorPatternCardInput {
    return legacyCard({
      cardId: "epc:backoff",
      cardType: "success-strategy",
      successStrategy: {
        subtype: "procedural",
        applicableWhen: APPLICABLE,
        steps: ["retry with exponential backoff", "cap at three attempts"],
      },
      errorSignature: { trigger: APPLICABLE, symptom: "transient timeout" },
      rootCauseCategory: "invocation-timing",
      resolution: "retry transient network failures with exponential backoff",
      provenance: { source: "rsi" },
      ...overrides,
    });
  }

  it("#A1 success card create + edit: version chain advances, payload round-trips, metadata carries the discriminator", () => {
    expect(manager.storeErrorPatternCard(successCard({ cardId: "epc:backoff" })))
      .toMatchObject({ ok: true, cardId: "epc:backoff", version: 1, edited: false });
    expect(manager.storeErrorPatternCard(successCard({
      cardId: "epc:backoff",
      successStrategy: { subtype: "procedural", applicableWhen: APPLICABLE, steps: ["retry with exponential backoff", "cap at three attempts", "log the failure context"] },
    }))).toMatchObject({ ok: true, version: 2, edited: true });

    const cards = manager.queryErrorPatternCards({ cardType: "success-strategy" });
    expect(cards).toHaveLength(1);
    expect(cards[0].cardType).toBe("success-strategy");
    expect(cards[0].successStrategy).toEqual({
      subtype: "procedural",
      applicableWhen: APPLICABLE,
      steps: ["retry with exponential backoff", "cap at three attempts", "log the failure context"],
    });
    const meta = encodeCardMetadata(cards[0]);
    expect(meta.card_type).toBe("success-strategy");
    expect(JSON.parse(meta.success_strategy).steps).toHaveLength(3);
  });

  it("#A2 V1' forward: success-strategy without a payload rejected; invalid cardType value rejected", () => {
    const missing = manager.storeErrorPatternCard(successCard({ successStrategy: undefined }));
    expect(missing.ok).toBe(false);
    if (!missing.ok) {
      expect(missing.ruleId).toBe("V1'");
      expect(missing.reason).toContain("successStrategy");
    }
    const badType = manager.storeErrorPatternCard(legacyCard({ cardType: "not-a-type" as never }));
    expect(badType.ok).toBe(false);
    if (!badType.ok) expect(badType.ruleId).toBe("V1'");
  });

  it("#A3 V1' reverse: error-pattern carrying a payload rejected (dual-state guard)", () => {
    const payload: SuccessStrategyPayload = {
      subtype: "strategic",
      applicableWhen: "when picking a retry policy",
      steps: ["prefer idempotent operations"],
    };
    const absent = manager.storeErrorPatternCard(legacyCard({ successStrategy: payload }));
    expect(absent.ok).toBe(false);
    if (!absent.ok) expect(absent.ruleId).toBe("V1'");
    const explicit = manager.storeErrorPatternCard(legacyCard({ cardType: "error-pattern", successStrategy: payload }));
    expect(explicit.ok).toBe(false);
    if (!explicit.ok) expect(explicit.ruleId).toBe("V1'");
    // explicit "error-pattern" without payload is legal (and writes no new keys)
    expect(manager.storeErrorPatternCard(legacyCard({ cardId: "epc:plain", cardType: "error-pattern" })).ok).toBe(true);
  });

  it("#A4 legacy zero-migration: absent cardType writes no v7.8 keys (byte-identical metadata)", () => {
    const meta = encodeCardMetadata({
      cardId: "epc:legacy",
      errorSignature: { trigger: "t", symptom: "s" },
      rootCauseCategory: "state-defect",
      provenance: { source: "remember" },
      effectiveness: { hitCount: 0, avoidedCount: 0, inactive: false },
    });
    expect(Object.keys(meta).sort()).toEqual([
      "card_id", "card_schema_version", "effectiveness", "error_signature", "provenance", "root_cause_category",
    ]);
    expect("card_type" in meta).toBe(false);
    expect("success_strategy" in meta).toBe(false);

    manager.storeErrorPatternCard(legacyCard({ cardId: "epc:legacy" }));
    const [c] = manager.queryErrorPatternCards({});
    expect(c.cardType).toBeUndefined();
    expect(c.successStrategy).toBeUndefined();
    expect(fs.readFileSync(path.join(tmpDir, "MEMORY.md"), "utf-8")).not.toContain("card_type");
  });

  it("#M1 Input-side dual validation (review M1): subtype / applicableWhen / steps branches", () => {
    expect(manager.storeErrorPatternCard(successCard({
      successStrategy: { subtype: "magic" as never, applicableWhen: "a valid scenario", steps: ["step one"] },
    }))).toMatchObject({ ok: false, ruleId: "V1'" });
    expect(manager.storeErrorPatternCard(successCard({
      successStrategy: { subtype: "procedural", applicableWhen: "   ", steps: ["step one"] },
    }))).toMatchObject({ ok: false, ruleId: "V1'" });
    expect(manager.storeErrorPatternCard(successCard({
      successStrategy: { subtype: "procedural", applicableWhen: "a valid scenario", steps: [] },
    }))).toMatchObject({ ok: false, ruleId: "V1'" });
    expect(manager.storeErrorPatternCard(successCard({
      successStrategy: { subtype: "procedural", applicableWhen: "a valid scenario", steps: ["ok step", "  "] },
    }))).toMatchObject({ ok: false, ruleId: "V1'" });
    for (const subtype of ["procedural", "strategic", "tool-usage"] as const) {
      expect(manager.storeErrorPatternCard(successCard({
        cardId: `epc:${subtype}`,
        successStrategy: { subtype, applicableWhen: "a valid scenario", steps: ["step one"] },
      }))).toMatchObject({ ok: true });
    }
  });

  it("#B1 default injection face = error-pattern only (v7.7.0 behaviour locked)", () => {
    manager.storeErrorPatternCard(legacyCard({ cardId: "epc:err" }));
    manager.storeErrorPatternCard(successCard({ cardId: "epc:succ" }));
    // triggerQuery only matches the success card — default type must not surface it
    expect(manager.findCardsForInjection({ triggerQuery: APPLICABLE })).toEqual([]);
    const all = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change" });
    expect(all.map((c) => c.cardId)).toEqual(["epc:err"]);
  });

  it("#B2 cardType 'success-strategy' flips the face", () => {
    manager.storeErrorPatternCard(legacyCard({ cardId: "epc:err" }));
    manager.storeErrorPatternCard(successCard({ cardId: "epc:succ" }));
    expect(manager.findCardsForInjection({ cardType: "success-strategy", triggerQuery: APPLICABLE }).map((c) => c.cardId))
      .toEqual(["epc:succ"]);
    expect(manager.findCardsForInjection({ cardType: "error-pattern", triggerQuery: APPLICABLE })).toEqual([]);
  });

  it("#B3 queryErrorPatternCards: absent cardType = both sides (audit face); filter narrows", () => {
    manager.storeErrorPatternCard(legacyCard({ cardId: "epc:err" }));
    manager.storeErrorPatternCard(successCard({ cardId: "epc:succ" }));
    expect(manager.queryErrorPatternCards({}).map((c) => c.cardId).sort()).toEqual(["epc:err", "epc:succ"]);
    expect(manager.queryErrorPatternCards({ cardType: "error-pattern" }).map((c) => c.cardId)).toEqual(["epc:err"]);
    expect(manager.queryErrorPatternCards({ cardType: "success-strategy" }).map((c) => c.cardId)).toEqual(["epc:succ"]);
  });
});

describe("injection format — dual side (contract §6.2)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-780-fmt-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  const APPLICABLE = "when a transient network call fails";
  const storeSuccess = (cardId: string, steps: string[], subtype: "procedural" | "strategic" | "tool-usage" = "procedural", trigger = APPLICABLE): void => {
    manager.storeErrorPatternCard({
      cardId,
      cardType: "success-strategy",
      successStrategy: { subtype, applicableWhen: trigger, steps },
      errorSignature: { trigger, symptom: "transient timeout" },
      rootCauseCategory: "invocation-timing",
      resolution: "retry transient network failures with exponential backoff",
      provenance: { source: "rsi" },
    });
  };

  it("#C1 ✅ line format verbatim: multi-step carries …, single step does not", () => {
    storeSuccess("epc:backoff", ["retry with exponential backoff", "cap at three attempts"]);
    const multi = manager.findCardsForInjection({ cardType: "success-strategy", triggerQuery: APPLICABLE });
    expect(manager.formatCardsAsReminder(multi)).toBe(
      "[Experience Cards]\n" +
      "- ✅ [epc:backoff | strategy: procedural | from: rsi] when a transient network call fails → retry with exponential backoff…"
    );
    storeSuccess("epc:single", ["run the failing test in isolation first"], "tool-usage", "when inspecting a failing test");
    const one = manager.findCardsForInjection({ cardType: "success-strategy", triggerQuery: "when inspecting a failing test" });
    expect(manager.formatCardsAsReminder(one)).toBe(
      "[Experience Cards]\n" +
      "- ✅ [epc:single | strategy: tool-usage | from: rsi] when inspecting a failing test → run the failing test in isolation first"
    );
  });

  it("#C2 mixed list: [Experience Cards] header, ⚠️/✅ line parity", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:err",
      errorSignature: { trigger: "before deploying a schema change", symptom: "runtime rejects new fields" },
      rootCauseCategory: "skill-defect",
      resolution: "run schema validation first. Then deploy with a dry run.",
      provenance: { source: "remember" },
    });
    storeSuccess("epc:backoff", ["retry with exponential backoff", "cap at three attempts"]);
    const err = manager.findCardsForInjection({ cardType: "error-pattern", triggerQuery: "before deploying a schema change" });
    const succ = manager.findCardsForInjection({ cardType: "success-strategy", triggerQuery: APPLICABLE });
    expect(manager.formatCardsAsReminder([...err, ...succ])).toBe(
      "[Experience Cards]\n" +
      "- ⚠️ [epc:err | root: skill-defect | from: remember] before deploying a schema change → run schema validation first.\n" +
      "- ✅ [epc:backoff | strategy: procedural | from: rsi] when a transient network call fails → retry with exponential backoff…"
    );
  });

  it("#C3 pure error cards: block byte-identical to v7.7 contract §2 (compat lock)", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:deploy-schema-check",
      errorSignature: { trigger: "before deploying a schema change", symptom: "runtime rejects new fields" },
      rootCauseCategory: "skill-defect",
      resolution: "run schema validation first. Then deploy with a dry run.",
      provenance: { source: "remember" },
    });
    const cards = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change" });
    expect(manager.formatCardsAsReminder(cards)).toBe(
      "[Error Pattern Cards]\n" +
      "- ⚠️ [epc:deploy-schema-check | root: skill-defect | from: remember] " +
      "before deploying a schema change → run schema validation first."
    );
  });
});

describe("lifecycle + hit writeback (v7.8.0 T4, contract §6.3)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-780-life-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("#D1 hit writeback shared both sides: success card demotes at HIT_WINDOW, avoids revive, payload survives", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:succ",
      cardType: "success-strategy",
      successStrategy: { subtype: "procedural", applicableWhen: "when a transient network call fails", steps: ["retry with exponential backoff", "cap at three attempts"] },
      errorSignature: { trigger: "when a transient network call fails", symptom: "transient timeout" },
      rootCauseCategory: "invocation-timing",
      resolution: "retry transient network failures with exponential backoff",
      provenance: { source: "rsi" },
    });
    for (let i = 0; i < 4; i++) manager.recordErrorPatternHit("epc:succ", { avoided: false });
    expect(manager.recordErrorPatternHit("epc:succ", { avoided: false }).inactive).toBe(true);
    expect(manager.findCardsForInjection({ cardType: "success-strategy", triggerQuery: "when a transient network call fails" })).toEqual([]);
    expect(manager.recordErrorPatternHit("epc:succ", { avoided: true }).inactive).toBe(false);
    const [c] = manager.queryErrorPatternCards({ cardType: "success-strategy" });
    expect(c.successStrategy?.steps).toHaveLength(2);
    expect(c.effectiveness.hitCount).toBe(6);
  });

  it("#D2 lifecycle host writeback: persisted + surfaced, partial merges keep prior keys", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:life",
      errorSignature: { trigger: "t", symptom: "s" },
      rootCauseCategory: "skill-defect",
      resolution: "a resolution long enough to pass V3b floor check",
      provenance: { source: "remember" },
    });
    manager.recordErrorPatternHit("epc:life", { avoided: true, lifecycle: { stableRuns: 3, pathAttribution: "run-42" } });
    expect(manager.queryErrorPatternCards({})[0].effectiveness.lifecycle)
      .toEqual({ stableRuns: 3, pathAttribution: "run-42" });
    manager.recordErrorPatternHit("epc:life", { avoided: true, lifecycle: { backwardRetention: 2 } });
    expect(manager.queryErrorPatternCards({})[0].effectiveness.lifecycle)
      .toEqual({ stableRuns: 3, pathAttribution: "run-42", backwardRetention: 2 });

    resetMemoryManager();
    const reloaded = new MemoryManager({ workspace: tmpDir, autoDetect: false });
    expect(reloaded.queryErrorPatternCards({})[0].effectiveness.lifecycle)
      .toEqual({ stableRuns: 3, pathAttribution: "run-42", backwardRetention: 2 });
  });

  it("#D4 BIDIRECTIONAL cross-repo lock: mem lifecycle field names == vendored rsi alignment snapshot", () => {
    // rsi discipline.ts:58-70 declares the lock and names mem's fields; that half is
    // vendored here (protocol v4.3.2 variant — claw-rsi is unreachable in mem's CI checkout).
    const snap = JSON.parse(
      fs.readFileSync(path.join(__dirname, "../fixtures/rsi-mem-lifecycle-alignment.snapshot.json"), "utf-8")
    );
    expect(snap.source).toBe("claw-rsi/src/diagnostics/discipline.ts");
    expect(snap.sourceVersion).toBe("5.7.0");
    expect(snap._note).toContain("re-vendor");
    const snapFields = Object.values(snap.alignment).sort();
    expect(snapFields).toEqual(["backwardRetention", "pathAttribution", "stableRuns"]);
    expect(Object.keys(snap.alignment).sort()).toEqual(["backwardRetention", "longitudinalStability", "pathAttribution"]);

    // this repo's other half: CardEffectiveness.lifecycle field names must equal the snapshot values
    const typesSrc = fs.readFileSync(path.join(__dirname, "../../src/types.ts"), "utf-8");
    const marker = "lifecycle?: {";
    const start = typesSrc.indexOf(marker);
    expect(start).toBeGreaterThan(-1);
    const block = typesSrc.slice(start + marker.length, typesSrc.indexOf("};", start));
    const memFields = [...block.matchAll(/(\w+)\?:/g)].map((m) => m[1]).sort();
    expect(memFields).toEqual(snapFields);
  });

  it("#D3 no fabrication: fresh cards carry no lifecycle; plain hits don't create one; caller-set ignored", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:plain",
      errorSignature: { trigger: "t", symptom: "s" },
      rootCauseCategory: "skill-defect",
      resolution: "a resolution long enough to pass V3b floor check",
      provenance: { source: "remember" },
    });
    expect(manager.queryErrorPatternCards({})[0].effectiveness.lifecycle).toBeUndefined();
    manager.recordErrorPatternHit("epc:plain", { avoided: true });
    expect(manager.queryErrorPatternCards({})[0].effectiveness.lifecycle).toBeUndefined();
    manager.storeErrorPatternCard({
      cardId: "epc:inject",
      errorSignature: { trigger: "t", symptom: "s" },
      rootCauseCategory: "skill-defect",
      resolution: "a resolution long enough to pass V3b floor check",
      provenance: { source: "remember" },
      effectiveness: { hitCount: 0, avoidedCount: 0, inactive: false, lifecycle: { stableRuns: 9 } },
    } as never);
    expect(manager.queryErrorPatternCards({}).find((c) => c.cardId === "epc:inject")?.effectiveness.lifecycle)
      .toBeUndefined();
  });
});

describe("T2 statusKey placeholder + ctx shape lock (design §3)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-780-t2-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("#E1 statusKey accepted, ranking untouched (placeholder only)", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:a",
      errorSignature: { trigger: "before deploying a schema change", symptom: "s" },
      rootCauseCategory: "skill-defect",
      resolution: "a resolution long enough to pass V3b floor check",
      provenance: { source: "remember" },
    });
    manager.storeErrorPatternCard({
      cardId: "epc:b",
      errorSignature: { trigger: "before deploying a schema rollback", symptom: "s" },
      rootCauseCategory: "state-defect",
      resolution: "another resolution long enough to pass the floor",
      provenance: { source: "remember" },
    });
    const base = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change", limit: 5 });
    expect(manager.findCardsForInjection({
      triggerQuery: "before deploying a schema change",
      limit: 5,
      statusKey: "taskType=bugfix|stage=verify|errors=e1,e2",
    })).toEqual(base);
    expect(manager.findCardsForInjection({
      triggerQuery: "before deploying a schema change",
      limit: 5,
      statusKey: "taskType=feature|stage=plan",
    })).toEqual(base);
  });

  it("#E2 ctx shape lock: vendored snapshot matches TaskStatusSignal / statusSignalKey", () => {
    const snap = JSON.parse(
      fs.readFileSync(path.join(__dirname, "../fixtures/ctx-task-status-signal.snapshot.json"), "utf-8")
    );
    expect(snap.source).toBe("claw-ctx/src/engine.ts");
    expect(snap.sourceVersion).toBe("6.10.0");
    const body = snap.interfaceLines.join("\n");
    expect(body).toContain("taskType?: string");
    expect(body).toContain("stage?: string");
    expect(body).toContain("recentErrorIds?: string[]");
    expect(snap.functionSignature).toContain(
      "statusSignalKey(signal: TaskStatusSignal | undefined, fallbackTaskType?: string): string"
    );
    expect(snap._note).toContain("re-vendor");
  });
});

describe("v7.6 / v7.7 compatibility (design §7 兼容组)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-780-compat-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("#G1 v7.6 card full-flow regression: store → hit → query → inject → format", () => {
    expect(manager.storeErrorPatternCard({
      cardId: "epc:legacy",
      errorSignature: { trigger: "before deploying a schema change", symptom: "runtime rejects new fields" },
      rootCauseCategory: "skill-defect",
      resolution: "run schema validation against the live environment before every deployment",
      provenance: { source: "remember" },
    })).toMatchObject({ ok: true, version: 1, edited: false });
    expect(manager.recordErrorPatternHit("epc:legacy", { avoided: true }))
      .toMatchObject({ ok: true, hitCount: 1, inactive: false });
    const [c] = manager.queryErrorPatternCards({ category: "skill-defect" });
    expect(c.cardId).toBe("epc:legacy");
    expect(c.cardType).toBeUndefined();
    const hits = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change" });
    expect(hits.map((x) => x.cardId)).toEqual(["epc:legacy"]);
    expect(manager.formatCardsAsReminder(hits)).toBe(
      "[Error Pattern Cards]\n" +
      "- ⚠️ [epc:legacy | root: skill-defect | from: remember] " +
      "before deploying a schema change → run schema validation against the live environment before every deployment"
    );
  });

  it("#G2 v7.7.0 injection API compatibility: legacy query objects behave verbatim", () => {
    for (let i = 1; i <= 5; i++) {
      manager.storeErrorPatternCard({
        cardId: `epc:schema-${i}`,
        errorSignature: { trigger: `before deploying schema change variant ${i}`, symptom: `s${i}` },
        rootCauseCategory: "skill-defect",
        resolution: "a resolution long enough to pass the V3b floor",
        provenance: { source: "remember" },
      });
    }
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying schema change" })).toHaveLength(3);
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying schema change", limit: 5 })).toHaveLength(5);
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying schema change", triggerThreshold: 1.01 })).toEqual([]);
    expect(manager.findCardsForInjection({ category: "state-defect" })).toEqual([]);
  });
});
