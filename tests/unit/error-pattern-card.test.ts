// Error Pattern Card Integration Tests (v7.6.0, ADR-003/004)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import type { ErrorPatternCardInput } from "../../src/types.js";

describe("ErrorPatternCard (store/query/match, ADR-003)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-"));
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
      verification: "npx schema-validate --env prod",
      provenance: { source: "remember", author: "peter" },
      ...overrides,
    };
  }

  it("creates a new card (version 1) with MEMORY.md entry + version chain file", () => {
    const result = manager.storeErrorPatternCard(cardInput());
    expect(result).toMatchObject({ ok: true, cardId: "epc:deploy-schema-check", version: 1, edited: false });

    // version chain file under its own directory (not preferences/)
    const chainFile = path.join(tmpDir, "memory", "error-pattern-cards", "epc_deploy-schema-check.json");
    expect(fs.existsSync(chainFile)).toBe(true);

    // MEMORY.md entry visible
    const mem = fs.readFileSync(path.join(tmpDir, "MEMORY.md"), "utf-8");
    expect(mem).toContain("error_pattern_card");
    expect(mem).toContain("category:skill-defect");
  });

  it("generates a cardId with epc: prefix when omitted", () => {
    const { cardId } = cardInput();
    void cardId;
    const result = manager.storeErrorPatternCard(cardInput({ cardId: undefined }));
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.cardId).toMatch(/^epc:/);
  });

  it("editing the same cardId archives + re-stores (version 2), keeping one entry", () => {
    expect(manager.storeErrorPatternCard(cardInput())).toMatchObject({ ok: true, version: 1 });
    const edit = manager.storeErrorPatternCard(
      cardInput({
        resolution: "run schema validation AND a dry-run against the live environment before deploying",
        rootCauseCategory: "invocation-timing",
      }),
    );
    expect(edit).toMatchObject({ ok: true, version: 2, edited: true });

    // one MEMORY.md entry, chain history length 2
    const mem = fs.readFileSync(path.join(tmpDir, "MEMORY.md"), "utf-8");
    expect(mem.match(/card:epc:deploy-schema-check/g)).toHaveLength(1);

    const cards = manager.queryErrorPatternCards({ includeInactive: true });
    expect(cards).toHaveLength(1);
    expect(cards[0].resolution).toContain("dry-run");
    expect(cards[0].rootCauseCategory).toBe("invocation-timing");
    expect(cards[0].createdAt).toBeTruthy();
  });

  it("keeps card history in its own chain directory (preference chain untouched)", () => {
    manager.store("dark", "preference", [], { pref_key: "theme" });
    manager.storeErrorPatternCard(cardInput());

    expect(fs.existsSync(path.join(tmpDir, "memory", "preferences", "theme.json"))).toBe(true);
    expect(fs.existsSync(path.join(tmpDir, "memory", "error-pattern-cards", "epc_deploy-schema-check.json"))).toBe(true);
    // card chain file must not appear in the preferences directory
    expect(fs.existsSync(path.join(tmpDir, "memory", "preferences", "epc_deploy-schema-check.json"))).toBe(false);
  });

  it("refuses error_pattern_card through the generic store (no silent fallback)", () => {
    expect(manager.store("some lesson text", "error_pattern_card", [], {})).toBe(false);
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(0);
  });

  it("resolves the strategy and exposes stats via registry", () => {
    expect(manager.getStoreStrategy("error_pattern_card")).toBe("error-pattern-card");
    manager.storeErrorPatternCard(cardInput());
  });

  it("queryErrorPatternCards filters by category and decodes full structure", () => {
    manager.storeErrorPatternCard(cardInput()); // skill-defect
    manager.storeErrorPatternCard(
      cardInput({
        cardId: "epc:api-old-interface",
        errorSignature: { trigger: "after refactoring an api", symptom: "calls still hit the removed old interface" },
        rootCauseCategory: "state-defect",
        resolution: "record the deprecation status immediately after the refactor",
        verification: undefined,
        provenance: { source: "rsi:analyze" },
      }),
    );

    const all = manager.queryErrorPatternCards({ includeInactive: true });
    expect(all).toHaveLength(2);

    const skillDefect = manager.queryErrorPatternCards({ category: "skill-defect" });
    expect(skillDefect).toHaveLength(1);
    expect(skillDefect[0].errorSignature.symptom).toContain("runtime rejects");
    expect(skillDefect[0].effectiveness).toMatchObject({ hitCount: 0, avoidedCount: 0, inactive: false });

    const rsiCard = manager.queryErrorPatternCards({ includeInactive: true })
      .find((c) => c.cardId === "epc:api-old-interface");
    expect(rsiCard?.verification).toBeUndefined();
    expect(rsiCard?.provenance.source).toBe("rsi:analyze");
  });

  it("matchErrorPattern hits symptom substring first, text as fallback", () => {
    manager.storeErrorPatternCard(cardInput());

    // signature (symptom) hit
    const bySymptom = manager.matchErrorPattern("runtime rejects new fields");
    expect(bySymptom).toHaveLength(1);
    expect(bySymptom[0].cardId).toBe("epc:deploy-schema-check");

    // trigger hit
    const byTrigger = manager.matchErrorPattern("before deploying");
    expect(byTrigger).toHaveLength(1);

    // text (resolution) fallback hit
    const byText = manager.matchErrorPattern("schema validation against the live");
    expect(byText).toHaveLength(1);

    // no match
    expect(manager.matchErrorPattern("zzz-no-such-symptom-zzz")).toHaveLength(0);
  });

  it("rejects structurally invalid inputs at the entry guard", () => {
    expect(manager.storeErrorPatternCard(cardInput({ errorSignature: { trigger: "", symptom: "x" } })))
      .toMatchObject({ ok: false });
    expect(manager.storeErrorPatternCard(cardInput({ rootCauseCategory: "not-a-category" })))
      .toMatchObject({ ok: false });
    expect(manager.storeErrorPatternCard(cardInput({ resolution: "   " })))
      .toMatchObject({ ok: false });
    expect(manager.storeErrorPatternCard(cardInput({ provenance: { source: "" } })))
      .toMatchObject({ ok: false });
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(0);
  });

  it("is reachable through the bridge RPC surface", async () => {
    const { handleRequest } = await import("../../src/bridge.js");
    const req = {
      id: 1,
      method: "query_error_pattern_cards",
      params: {},
    };
    const res = await handleRequest(req as never, manager);
    expect(res.result).toHaveProperty("cards");
  });
});
