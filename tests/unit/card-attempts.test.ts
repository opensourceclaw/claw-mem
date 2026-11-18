// v7.11 SIM (arXiv 2611.18856) — predicted → fixed/missed attempt triplet.
// Additive + zero migration; host write-back only; non-backfilled attempts are
// excluded from effectiveness stats.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import type { ErrorPatternCardInput } from "../../src/types.js";

const CARD_ID = "epc:deploy-schema-check";

describe("CardAttempt triplet (v7.11 SIM)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-card-attempts-"));
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
      cardId: CARD_ID,
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

  function readCard() {
    return manager.queryErrorPatternCards({ includeInactive: true })[0];
  }

  it("legacy cards without attempts read normally; stats are empty with null rate", () => {
    expect(manager.storeErrorPatternCard(cardInput()).ok).toBe(true);
    expect(readCard().effectiveness.attempts).toBeUndefined();
    expect(manager.getCardAttemptStats(CARD_ID)).toMatchObject({
      ok: true,
      attempts: 0,
      backfilled: 0,
      predicted: 0,
      fixed: 0,
      missed: 0,
      fixedRate: null,
    });
  });

  it("caller-supplied attempts are rejected at store time (host-written only)", () => {
    const result = manager.storeErrorPatternCard({
      ...cardInput(),
      effectiveness: {
        attempts: [
          {
            runId: "forged",
            predictedIssueIds: ["a"],
            fixedIds: ["a"],
            missedIds: [],
            backfilled: true,
            observedAt: "2026-11-17T00:00:00Z",
          },
        ],
      },
    } as unknown as ErrorPatternCardInput);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toContain("host-written only");
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(0);
  });

  it("recordCardAttempt appends an unbackfilled attempt; stats exclude it", () => {
    manager.storeErrorPatternCard(cardInput());
    const result = manager.recordCardAttempt(CARD_ID, {
      runId: "run-1",
      predictedIssueIds: ["issue-a", "issue-b"],
      at: "2026-11-17T10:00:00Z",
    });
    expect(result).toMatchObject({ ok: true, runId: "run-1", attempts: 1 });

    expect(readCard().effectiveness.attempts).toEqual([
      {
        runId: "run-1",
        predictedIssueIds: ["issue-a", "issue-b"],
        fixedIds: [],
        missedIds: [],
        backfilled: false,
        observedAt: "2026-11-17T10:00:00Z",
      },
    ]);
    expect(manager.getCardAttemptStats(CARD_ID)).toMatchObject({
      ok: true,
      attempts: 1,
      backfilled: 0,
      predicted: 0,
      fixed: 0,
      missed: 0,
      fixedRate: null,
    });
  });

  it("backfill completes the partition and enters effectiveness stats", () => {
    manager.storeErrorPatternCard(cardInput());
    manager.recordCardAttempt(CARD_ID, {
      runId: "run-1",
      predictedIssueIds: ["a", "b", "c"],
    });

    const result = manager.backfillCardAttempt(CARD_ID, "run-1", {
      fixedIds: ["a", "b"],
      missedIds: ["c"],
      at: "2026-11-17T11:00:00Z",
    });
    expect(result).toMatchObject({ ok: true, fixed: 2, missed: 1 });

    const attempt = readCard().effectiveness.attempts![0];
    expect(attempt.backfilled).toBe(true);
    expect(attempt.fixedIds).toEqual(["a", "b"]);
    expect(attempt.missedIds).toEqual(["c"]);

    const stats = manager.getCardAttemptStats(CARD_ID);
    expect(stats).toMatchObject({
      ok: true,
      attempts: 1,
      backfilled: 1,
      predicted: 3,
      fixed: 2,
      missed: 1,
    });
    if (stats.ok) expect(stats.fixedRate).toBeCloseTo(2 / 3, 10);
  });

  it("rejects inconsistent backfills (foreign / overlap / incomplete)", () => {
    manager.storeErrorPatternCard(cardInput());
    manager.recordCardAttempt(CARD_ID, { runId: "run-1", predictedIssueIds: ["a", "b"] });

    const foreign = manager.backfillCardAttempt(CARD_ID, "run-1", {
      fixedIds: ["a", "x"],
      missedIds: ["b"],
    });
    expect(foreign.ok).toBe(false);
    if (!foreign.ok) expect(foreign.reason).toContain("not in predictedIssueIds");

    const overlap = manager.backfillCardAttempt(CARD_ID, "run-1", {
      fixedIds: ["a"],
      missedIds: ["a"],
    });
    expect(overlap.ok).toBe(false);
    if (!overlap.ok) expect(overlap.reason).toContain("both fixed and missed");

    const incomplete = manager.backfillCardAttempt(CARD_ID, "run-1", {
      fixedIds: ["a"],
      missedIds: [],
    });
    expect(incomplete.ok).toBe(false);
    if (!incomplete.ok) expect(incomplete.reason).toContain("backfill incomplete");

    // Rejected attempts do not corrupt the ledger.
    const attempt = readCard().effectiveness.attempts![0];
    expect(attempt.backfilled).toBe(false);
    expect(attempt.fixedIds).toEqual([]);
    expect(attempt.missedIds).toEqual([]);
  });

  it("rejects duplicate runId and a second backfill", () => {
    manager.storeErrorPatternCard(cardInput());
    expect(manager.recordCardAttempt(CARD_ID, { runId: "run-1", predictedIssueIds: ["a"] }).ok).toBe(true);
    const duplicate = manager.recordCardAttempt(CARD_ID, { runId: "run-1", predictedIssueIds: ["b"] });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.reason).toContain("already exists");

    expect(
      manager.backfillCardAttempt(CARD_ID, "run-1", { fixedIds: ["a"], missedIds: [] }).ok,
    ).toBe(true);
    const second = manager.backfillCardAttempt(CARD_ID, "run-1", {
      fixedIds: ["a"],
      missedIds: [],
    });
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.reason).toContain("already backfilled");
  });

  it("rejects an empty prediction and non-string ids", () => {
    manager.storeErrorPatternCard(cardInput());
    const empty = manager.recordCardAttempt(CARD_ID, { runId: "r", predictedIssueIds: [] });
    expect(empty.ok).toBe(false);
    if (!empty.ok) expect(empty.reason).toContain("non-empty");

    const bad = manager.recordCardAttempt(CARD_ID, {
      runId: "r",
      predictedIssueIds: [""],
    });
    expect(bad.ok).toBe(false);
  });

  it("recordErrorPatternHit preserves the attempts ledger (no drift)", () => {
    manager.storeErrorPatternCard(cardInput());
    manager.recordCardAttempt(CARD_ID, { runId: "run-1", predictedIssueIds: ["a"] });
    const hit = manager.recordErrorPatternHit(CARD_ID, { avoided: true, at: "2026-11-17T12:00:00Z" });
    expect(hit.ok).toBe(true);
    const attempt = readCard().effectiveness.attempts![0];
    expect(attempt.runId).toBe("run-1");
    expect(attempt.backfilled).toBe(false);
  });
});
