// Error pattern card remember-intent tests (v7.6.0, design §3.4 / ADR-003)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import { parseCardIntentText, suggestCardId, buildCardInputFromParams, CARD_INTENT_PREFIX } from "../../src/storage/error-pattern-card/parse.js";

describe("parseCardIntentText (remember intent recognition)", () => {
  const fullJson =
    '{"trigger": "before deploying a schema change", "symptom": "runtime rejects new fields", "rootCauseCategory": "skill-defect", "resolution": "run schema validation against the live environment before every deployment", "verification": "npx schema-validate --env prod"}';

  it("recognizes 错误模式卡 and error pattern prefixes (case/punct-insensitive)", () => {
    expect(parseCardIntentText(`错误模式卡: ${fullJson}`).kind).toBe("card");
    expect(parseCardIntentText(`error pattern: ${fullJson}`).kind).toBe("card");
    expect(parseCardIntentText(`Error Pattern ${fullJson}`).kind).toBe("card");
    expect(CARD_INTENT_PREFIX.test("  Error Pattern x")).toBe(true);
  });

  it("extracts a complete card input with remember provenance default", () => {
    const res = parseCardIntentText(`错误模式卡：${fullJson}`);
    expect(res.kind).toBe("card");
    if (res.kind === "card") {
      expect(res.input).toMatchObject({
        errorSignature: { trigger: "before deploying a schema change" },
        rootCauseCategory: "skill-defect",
        resolution: "run schema validation against the live environment before every deployment",
        verification: "npx schema-validate --env prod",
        provenance: { source: "remember" },
      });
    }
  });

  it("accepts snake_case keys and explicit source/author/card_id", () => {
    const res = parseCardIntentText(
      `error pattern: {"card_id": "epc:deploy-schema", "trigger": "t", "symptom": "s", "root_cause_category": "state-defect", "resolution": "record deprecation status right after the refactor", "provenance_source": "rsi:analyze", "author": "edith"}`,
    );
    expect(res.kind).toBe("card");
    if (res.kind === "card") {
      expect(res.input.cardId).toBe("epc:deploy-schema");
      expect(res.input.rootCauseCategory).toBe("state-defect");
      expect(res.input.provenance).toEqual({ source: "rsi:analyze", author: "edith" });
    }
  });

  it("guides back incomplete payloads with the missing field list", () => {
    const noResolution = parseCardIntentText(
      '错误模式卡: {"trigger": "t", "symptom": "s", "rootCauseCategory": "skill-defect"}',
    );
    expect(noResolution.kind).toBe("card-incomplete");
    if (noResolution.kind === "card-incomplete") expect(noResolution.missing).toContain("resolution");

    const badCategory = parseCardIntentText(
      'error pattern: {"trigger": "t", "symptom": "s", "rootCauseCategory": "nope", "resolution": "a long enough resolution string here"}',
    );
    expect(badCategory.kind).toBe("card-incomplete");
    if (badCategory.kind === "card-incomplete") expect(badCategory.missing).toContain("rootCauseCategory");

    const unparseable = parseCardIntentText("错误模式卡: 部署前先跑 schema 校验");
    expect(unparseable.kind).toBe("card-incomplete");

    const empty = parseCardIntentText("错误模式卡:");
    expect(empty.kind).toBe("card-incomplete");
  });

  it("returns other for non-intent text (never mis-routed)", () => {
    expect(parseCardIntentText("remember to run schema validation before deploying").kind).toBe("other");
    expect(parseCardIntentText("").kind).toBe("other");
  });
});

describe("suggestCardId (epc: trigger slug)", () => {
  it("slugs a trigger into a stable epc: id", () => {
    expect(suggestCardId("Before deploying a schema change!")).toBe("epc:before-deploying-a-schema-change");
  });

  it("truncates long triggers and returns undefined for empty", () => {
    const long = "do ".repeat(60).trim();
    const slug = suggestCardId(long);
    expect(slug?.startsWith("epc:")).toBe(true);
    expect(slug.length).toBeLessThanOrEqual("epc:".length + 40);
    expect(suggestCardId("")).toBeUndefined();
    expect(suggestCardId("!!!")).toBeUndefined();
  });
});

describe("buildCardInputFromParams (flat RPC params)", () => {
  it("assembles a complete input, defaulting provenance to remember", () => {
    const res = buildCardInputFromParams({
      card_id: "epc:x",
      trigger: "t1",
      symptom: "s1",
      root_cause_category: "skill-defect",
      resolution: "a resolution longer than twenty characters",
    });
    expect(res).toEqual({
      input: {
        cardId: "epc:x",
        errorSignature: { trigger: "t1", symptom: "s1" },
        rootCauseCategory: "skill-defect",
        resolution: "a resolution longer than twenty characters",
        provenance: { source: "remember" },
      },
    });
  });

  it("lists missing fields and rejects unknown categories", () => {
    const res = buildCardInputFromParams({ trigger: "t1" });
    expect("missing" in res).toBe(true);
    if ("missing" in res) expect(res.missing.sort()).toEqual(["resolution", "root_cause_category", "symptom"]);
  });
});

describe("store_error_pattern_card bridge RPC", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-intent-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  async function rpc(params: Record<string, unknown>): Promise<{ result?: any; error?: any }> {
    const { handleRequest } = await import("../../src/bridge.js");
    return handleRequest({ id: 1, method: "store_error_pattern_card", params } as never, manager) as never;
  }

  it("stores from structured params with a trigger-slug cardId when card_id absent", async () => {
    const res = await rpc({
      trigger: "before deploying a schema change",
      symptom: "runtime rejects new fields",
      root_cause_category: "skill-defect",
      resolution: "run schema validation against the live environment before every deployment",
    });
    expect(res.result).toMatchObject({ ok: true, cardId: "epc:before-deploying-a-schema-change" });
    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.provenance.source).toBe("remember");
  });

  it("stores from intent text with 错误模式卡 prefix (JSON payload)", async () => {
    const res = await rpc({
      text: '错误模式卡: {"trigger": "t2", "symptom": "s2", "rootCauseCategory": "state-defect", "resolution": "a sufficiently long resolution for this card", "source": "rsi:analyze"}',
    });
    expect(res.result).toMatchObject({ ok: true });
    const [card] = manager.queryErrorPatternCards({ includeInactive: true });
    expect(card.rootCauseCategory).toBe("state-defect");
    expect(card.provenance.source).toBe("rsi:analyze");
  });

  it("returns missing-field guidance instead of a silent drop", async () => {
    const res = await rpc({ trigger: "only a trigger" });
    expect(res.result).toMatchObject({ ok: false, reason: "missing required card fields" });
    expect(res.result.missing).toContain("resolution");
    expect(manager.queryErrorPatternCards({ includeInactive: true })).toHaveLength(0);

    const noPrefix = await rpc({ text: "run schema validation before deploying" });
    expect(noPrefix.result).toMatchObject({ ok: false });
    expect(String(noPrefix.result.reason)).toContain("prefix");
  });
});
