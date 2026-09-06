// Error Pattern Card Effectiveness Tests (v7.6.0, ADR-005)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { vi } from "vitest";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import { VersionChain } from "../../src/storage/version-chain.js";
import type { ErrorPatternCardInput } from "../../src/types.js";

describe("ErrorPatternCard effectiveness (recordErrorPatternHit, ADR-005)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-hit-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    vi.useRealTimers();
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

  function seedCard(): void {
    const r = manager.storeErrorPatternCard(cardInput());
    if (!r.ok) throw new Error("seed card failed");
  }

  it("records two-state counters (avoided vs non-avoided)", () => {
    seedCard();
    expect(manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: true }))
      .toMatchObject({ ok: true, hitCount: 1, avoidedCount: 1, inactive: false });
    expect(manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false }))
      .toMatchObject({ ok: true, hitCount: 2, avoidedCount: 1, inactive: false });

    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.effectiveness).toMatchObject({ hitCount: 2, avoidedCount: 1 });
    expect(card.effectiveness.lastHitAt).toBeTruthy();
  });

  it("returns not-found for unknown cardIds", () => {
    expect(manager.recordErrorPatternHit("epc:nope")).toMatchObject({ ok: false, reason: "not-found" });
  });

  it("appends one chain version per hit with complete effectiveness (hit chain integrity)", () => {
    seedCard();
    const chain = new VersionChain(tmpDir, "error-pattern-cards");
    expect(chain.getHistory("epc:deploy-schema-check")).toHaveLength(1); // v1 creation

    manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: true });
    manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: true });
    manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false });

    const history = chain.getHistory("epc:deploy-schema-check");
    expect(history).toHaveLength(4); // creation + 3 hit commits (archive-old semantics)
    // Chain stores the archived (replaced) state: each commit archives the
    // entry before the update, so hit i's completion lands on the chain at
    // hit i+1's commit. hitCount/avoidedCount must move exactly once per hit.
    const effs = history.map((v) => JSON.parse(String(v.metadata?.effectiveness)));
    expect(effs.map((e: { hitCount: number }) => e.hitCount)).toEqual([0, 0, 1, 2]);
    expect(effs.map((e: { avoidedCount: number }) => e.avoidedCount)).toEqual([0, 0, 1, 2]);
  });

  it("demotes after HIT_WINDOW consecutive non-avoided hits (never deleted)", () => {
    seedCard();
    for (let i = 0; i < 4; i++) {
      const r = manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false });
      expect(r).toMatchObject({ ok: true, inactive: false });
    }
    const fifth = manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false });
    expect(fifth).toMatchObject({ ok: true, inactive: true });

    // excluded by default, visible with includeInactive, still stored (not deleted)
    expect(manager.queryErrorPatternCards()).toHaveLength(0);
    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.effectiveness.inactive).toBe(true);
    expect(card.effectiveness.inactivatedAt).toBeTruthy();
    expect(card.effectiveness.hitCount).toBe(5);
  });

  it("an avoided hit breaks the non-avoided streak (no demotion)", () => {
    seedCard();
    // 2 avoided then 4 non-avoided: tail run is 4 < HIT_WINDOW
    manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: true });
    manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: true });
    for (let i = 0; i < 4; i++) {
      const r = manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false });
      expect(r).toMatchObject({ ok: true, inactive: false });
    }
    expect(manager.queryErrorPatternCards()).toHaveLength(1); // still active
  });

  it("auto-revives an inactive card on the first avoided hit", () => {
    seedCard();
    for (let i = 0; i < 5; i++) {
      manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: false });
    }
    const [inactive] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(inactive.effectiveness.inactive).toBe(true);

    const revived = manager.recordErrorPatternHit("epc:deploy-schema-check", { avoided: true });
    expect(revived).toMatchObject({ ok: true, inactive: false, avoidedCount: 1 });

    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.effectiveness.inactive).toBe(false);
    expect(card.effectiveness.inactivatedAt).toBeUndefined();
  });

  it("demotes never-hit cards lazily after the grace period (read-time)", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-01T00:00:00Z"));
    seedCard(); // createdAt = 2026-09-01, hitCount 0

    // within grace: still active
    vi.setSystemTime(new Date("2026-09-15T00:00:00Z"));
    expect(manager.queryErrorPatternCards()).toHaveLength(1);

    // past grace (44 days > 30): demoted on read
    vi.setSystemTime(new Date("2026-10-15T00:00:00Z"));
    expect(manager.queryErrorPatternCards()).toHaveLength(0);
    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.effectiveness.inactive).toBe(true);
    expect(card.effectiveness.inactivatedAt).toBeTruthy();
    vi.useRealTimers();
  });

  it("downranks inactive cards in signature matching at equal score", () => {
    const sharedSymptom = "shared-symptom-marker";
    manager.storeErrorPatternCard(
      cardInput({
        cardId: "epc:active-one",
        errorSignature: { trigger: "t-active", symptom: sharedSymptom },
      }),
    );
    manager.storeErrorPatternCard(
      cardInput({
        cardId: "epc:inactive-one",
        errorSignature: { trigger: "t-inactive", symptom: sharedSymptom },
        rootCauseCategory: "state-defect",
      }),
    );
    // demote the second card
    for (let i = 0; i < 5; i++) {
      manager.recordErrorPatternHit("epc:inactive-one", { avoided: false });
    }

    const matches = manager.matchErrorPattern(sharedSymptom);
    expect(matches).toHaveLength(2);
    expect(matches[0].cardId).toBe("epc:active-one");
    expect(matches[1].cardId).toBe("epc:inactive-one");
  });

  it("is reachable through the bridge RPC surface", async () => {
    seedCard();
    const { handleRequest } = await import("../../src/bridge.js");
    const res = await handleRequest(
      { id: 1, method: "record_error_pattern_hit", params: { card_id: "epc:deploy-schema-check", avoided: true } } as never,
      manager,
    );
    expect(res.result).toMatchObject({ ok: true, hitCount: 1 });
  });
});
