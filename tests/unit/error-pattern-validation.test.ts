// Error Pattern Card Validation Gate Tests (v7.6.0, ADR-006)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import type { ErrorPatternCardInput } from "../../src/types.js";

describe("ErrorPatternCard validation gate (storeErrorPatternCard, ADR-006)", () => {
  let tmpDir: string;
  let manager: MemoryManager;
  const REJ_DIR = () => path.join(tmpDir, "memory", "error-pattern-card-rejections");

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-gate-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  function cardInput(overrides: Partial<ErrorPatternCardInput> = {}): ErrorPatternCardInput {
    return {
      cardId: "epc:deploy-schema-check",
      errorSignature: {
        trigger: "before deploying a schema change",
        symptom: "deployment succeeds but runtime rejects new fields",
      },
      rootCauseCategory: "skill-defect",
      resolution: "run schema validation against the live environment before every deployment",
      provenance: { source: "remember", author: "peter" },
      ...overrides,
    };
  }

  function rejectionFiles(): string[] {
    if (!fs.existsSync(REJ_DIR())) return [];
    return fs.readdirSync(REJ_DIR()).filter((f) => f.endsWith(".jsonl"));
  }

  it("V1 rejects empty/missing signature fields with ruleId and traces", () => {
    expect(manager.storeErrorPatternCard(cardInput({ errorSignature: { trigger: "", symptom: "x" } })))
      .toMatchObject({ ok: false, ruleId: "V1" });
    expect(manager.storeErrorPatternCard(cardInput({ errorSignature: { trigger: "t", symptom: "" } })))
      .toMatchObject({ ok: false, ruleId: "V1" });
    expect(manager.storeErrorPatternCard(cardInput({ resolution: "   " })))
      .toMatchObject({ ok: false, ruleId: "V1" });
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(0);
    expect(rejectionFiles()).toHaveLength(3);
  });

  it("V2 rejects missing provenance.source", () => {
    expect(manager.storeErrorPatternCard(cardInput({ provenance: { source: "" } })))
      .toMatchObject({ ok: false, ruleId: "V2" });
    expect(manager.storeErrorPatternCard(cardInput({ provenance: undefined as never })))
      .toMatchObject({ ok: false, ruleId: "V2" });
  });

  it("V3b rejects resolutions shorter than RESOLUTION_MIN_CHARS (20), 20+ passes", () => {
    const short = "x".repeat(19);
    expect(manager.storeErrorPatternCard(cardInput({ resolution: short })))
      .toMatchObject({ ok: false, ruleId: "V3b" });
    const ok20 = "y".repeat(20);
    expect(manager.storeErrorPatternCard(cardInput({ resolution: ok20 })))
      .toMatchObject({ ok: true, edited: false });
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(1);
  });

  it("V3c rejects unregistered rootCauseCategory at runtime", () => {
    expect(manager.storeErrorPatternCard(cardInput({ rootCauseCategory: "not-a-category" as never })))
      .toMatchObject({ ok: false, ruleId: "V3c" });
  });

  it("V1 rejects negative effectiveness counts smuggled in input (server-owned field)", () => {
    const res = manager.storeErrorPatternCard({
      ...cardInput(),
      effectiveness: { hitCount: -1, avoidedCount: 0, inactive: false },
    } as unknown as ErrorPatternCardInput);
    expect(res).toMatchObject({ ok: false, ruleId: "V1" });
  });

  it("V3a warns on create with ~duplicate trigger of an active card but still stores", () => {
    manager.storeErrorPatternCard(cardInput()); // active card, trigger t1
    const res = manager.storeErrorPatternCard(
      cardInput({
        cardId: "epc:deploy-schema-check-v2",
        errorSignature: { trigger: "before deploying a schema change to production", symptom: "s" },
      }),
    );
    expect(res).toMatchObject({
      ok: true,
      edited: false,
      warning: { ruleId: "V3a-trigger-similarity", similarCardId: "epc:deploy-schema-check" },
    });
    if (res.ok && res.warning) expect(res.warning.similarity).toBe(1);
    // stored despite the advisory
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(2);
    // warn event traced
    const list = manager.listErrorPatternRejections();
    expect(list).toHaveLength(1);
    expect(list[0]).toMatchObject({ action: "warn", ruleId: "V3a-trigger-similarity" });
    expect(list[0].caller).toBe("remember");
  });

  it("V3a does not warn for dissimilar triggers or same-cardId edits", () => {
    manager.storeErrorPatternCard(cardInput());
    // dissimilar trigger
    const dissimilar = manager.storeErrorPatternCard(
      cardInput({
        cardId: "epc:check-billing-api",
        errorSignature: { trigger: "check the billing api response shape", symptom: "s2" },
      }),
    );
    expect(dissimilar).toMatchObject({ ok: true });
    if (dissimilar.ok) expect(dissimilar.warning).toBeUndefined();
    // same-cardId edit of a ~duplicate trigger is an intentional edit
    const edit = manager.storeErrorPatternCard(cardInput()); // same trigger, same cardId
    expect(edit).toMatchObject({ ok: true, edited: true });
    if (edit.ok) expect(edit.warning).toBeUndefined();
  });

  it("V3a ignores inactive cards as comparison targets", () => {
    manager.storeErrorPatternCard(cardInput());
    for (let i = 0; i < 5; i++) {
      manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false });
    }
    const res = manager.storeErrorPatternCard(
      cardInput({
        cardId: "epc:new-similar",
        errorSignature: { trigger: "before deploying a schema change to production", symptom: "s" },
      }),
    );
    expect(res).toMatchObject({ ok: true });
    if (res.ok) expect(res.warning).toBeUndefined();
  });

  it("traces generic-store refusal as a rejection event", () => {
    expect(manager.store("some lesson text", "error_pattern_card", [], {})).toBe(false);
    const list = manager.listErrorPatternRejections();
    expect(list).toHaveLength(1);
    expect(list[0]).toMatchObject({ action: "reject", ruleId: "generic-store-refusal" });
    expect(list[0].input).toHaveProperty("contentPreview");
  });

  it("listErrorPatternRejections filters by action/since and limits, newest first", () => {
    manager.store("lesson", "error_pattern_card", [], {}); // generic refusal (reject)
    manager.storeErrorPatternCard(cardInput({ errorSignature: { trigger: "", symptom: "x" } })); // V1 reject
    manager.storeErrorPatternCard(cardInput()); // valid card
    manager.storeErrorPatternCard(
      cardInput({ cardId: "epc:dup", trigger: "before deploying a schema change to prod" }), // V3a warn
    );

    const list = manager.listErrorPatternRejections();
    expect(list.length).toBeGreaterThanOrEqual(3);
    // newest first by ts
    for (let i = 1; i < list.length; i++) expect(list[i - 1].ts >= list[i].ts).toBe(true);

    const rejects = manager.listErrorPatternRejections({ action: "reject" });
    expect(rejects.every((r) => r.action === "reject")).toBe(true);
    expect(rejects.some((r) => r.ruleId === "generic-store-refusal")).toBe(true);
    expect(rejects.some((r) => r.ruleId === "V1")).toBe(true);
    expect(rejects.every((r) => r.ruleId !== "V3a-trigger-similarity")).toBe(true);

    const warns = manager.listErrorPatternRejections({ action: "warn" });
    expect(warns.every((w) => w.action === "warn")).toBe(true);

    const limited = manager.listErrorPatternRejections({ limit: 2 });
    expect(limited).toHaveLength(2);

    // since is inclusive on ts; events may share a millisecond, so assert the
    // semantic: nothing older than the cutoff survives, and the newest stays.
    const sinceTs = list[1].ts;
    const since = manager.listErrorPatternRejections({ since: sinceTs });
    expect(since.every((e) => e.ts >= sinceTs)).toBe(true);
    expect(since[0]).toEqual(list[0]);
  });

  it("stores fields as given on valid input (createdAt server-side, no caller control)", () => {
    const res = manager.storeErrorPatternCard(cardInput({ provenance: { source: "rsi:analyze" } }));
    expect(res).toMatchObject({ ok: true, edited: false });
    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.provenance.source).toBe("rsi:analyze");
    expect(card.effectiveness).toMatchObject({ hitCount: 0, avoidedCount: 0, inactive: false });
    expect(card.createdAt).toBeTruthy();
  });

  it("is reachable through the bridge RPC surface", async () => {
    manager.store("lesson", "error_pattern_card", [], {});
    const { handleRequest } = await import("../../src/bridge.js");
    const res = await handleRequest(
      { id: 1, method: "list_error_pattern_rejections", params: { action: "reject" } } as never,
      manager,
    );
    expect(res.result.rejections).toHaveLength(1);
    expect(res.result.rejections[0].ruleId).toBe("generic-store-refusal");
  });
});
