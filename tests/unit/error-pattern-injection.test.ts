// Error Pattern Card Injection Path Tests (v7.7.0, joint design §7 mem list)
// Thin adapter over v7.6.0: findCardsForInjection (trigger similarity ∪ category,
// active-only) + formatCardsAsReminder (contract §2 format, whole-card truncation).
// Frozen surfaces asserted in-place: ADR-006 gate + hit writeback semantics replay.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager, resetMemoryManager } from "../../src/memory_manager.js";
import { triggerSimilarity, SIMILARITY_THRESHOLD } from "../../src/index.js";
import type { ErrorPatternCardInput } from "../../src/types.js";

describe("findCardsForInjection (v7.7.0)", () => {
  let tmpDir: string;
  let manager: MemoryManager;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-inj-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  function card(overrides: Partial<ErrorPatternCardInput> = {}): ErrorPatternCardInput {
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

  it("#1 triggerQuery similar to card trigger is recalled (superset-phrase match)", () => {
    manager.storeErrorPatternCard(card({ cardId: "epc:schema" }));
    // 查询 = 卡 trigger 原文 + 追加语境 → bigram 交集/min = 1.0（相似度上界）
    const hit = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change in production" });
    expect(hit.map((c) => c.cardId)).toContain("epc:schema");
  });

  it("#2 default threshold == SIMILARITY_THRESHOLD (same 'similar' as V3a, source lock)", () => {
    expect(SIMILARITY_THRESHOLD).toBe(0.8);
    // identical-ish trigger passes 0.8; unrelated one does not
    manager.storeErrorPatternCard(card({ cardId: "epc:schema" }));
    const near = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change!" });
    expect(near.map((c) => c.cardId)).toContain("epc:schema");
    const far = manager.findCardsForInjection({ triggerQuery: "cooking pasta for dinner tonight" });
    expect(far).toEqual([]);
  });

  it("#3 low similarity → honest empty (nothing synthesized); empty query = recency path not empty", () => {
    manager.storeErrorPatternCard(card({ cardId: "epc:schema" }));
    expect(manager.findCardsForInjection({ triggerQuery: "x" })).toEqual([]); // 相似度 0
    // 无 triggerQuery = recency 路径（#8 语义），库里有卡则返回
    expect(manager.findCardsForInjection({}).length).toBe(1);
    expect(manager.findCardsForInjection({ category: "state-defect" })).toEqual([]); // category 无匹配
  });

  it("#4 category exact filter composes with trigger matching", () => {
    manager.storeErrorPatternCard(card({ cardId: "epc:schema", rootCauseCategory: "skill-defect" }));
    manager.storeErrorPatternCard(card({
      cardId: "epc:timing",
      errorSignature: { trigger: "before deploying a schema rollback", symptom: "rollback lands late" },
      rootCauseCategory: "invocation-timing",
    }));
    const onlySkill = manager.findCardsForInjection({
      triggerQuery: "before deploying a schema",
      category: "invocation-timing",
    });
    expect(onlySkill.map((c) => c.cardId)).toEqual(["epc:timing"]); // 相似命中但被 category 过滤
  });

  it("#5 inactive cards NEVER enter the injection face (demotion then query)", () => {
    manager.storeErrorPatternCard(card({ cardId: "epc:schema" }));
    for (let i = 0; i < 5; i++) manager.recordErrorPatternHit("epc:schema", { avoided: false }); // HIT_WINDOW=5 → demote
    const before = manager.recordErrorPatternHit("epc:schema", { avoided: false });
    expect(before.inactive).toBe(true);
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying a schema change" })).toEqual([]);
    // avoided 复活后重新可注入（v7.6.0 复活机制 + v7.7.0 注入面衔接）
    manager.recordErrorPatternHit("epc:schema", { avoided: true });
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying a schema change" }).map((c) => c.cardId)).toContain("epc:schema");
  });

  it("#6 explicit limit caps the result; default limit = 3", () => {
    for (let i = 1; i <= 5; i++) {
      manager.storeErrorPatternCard(card({
        cardId: `epc:schema-${i}`,
        errorSignature: { trigger: `before deploying schema change variant ${i}`, symptom: "s" + i },
      }));
    }
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying schema change" })).toHaveLength(3);
    expect(manager.findCardsForInjection({ triggerQuery: "before deploying schema change", limit: 5 })).toHaveLength(5);
  });

  it("#7 sorting: similarity desc, then lastHitAt desc (never-hit last)", () => {
    manager.storeErrorPatternCard(card({
      cardId: "epc:weak",
      errorSignature: { trigger: "deploying a schema alter script", symptom: "s" },
    }));
    manager.storeErrorPatternCard(card({ cardId: "epc:strong" })); // 最接近 triggerQuery
    const hits = manager.findCardsForInjection({
      triggerQuery: "before deploying a schema change",
      limit: 5,
    });
    expect(hits[0].cardId).toBe("epc:strong");
  });

  it("#8 no triggerQuery → recency path (lastHitAt desc, never-hit last) — queryErrorPatternCards semantics", () => {
    manager.storeErrorPatternCard(card({ cardId: "epc:a" }));
    manager.storeErrorPatternCard(card({ cardId: "epc:b" }));
    manager.recordErrorPatternHit("epc:a", { avoided: true }); // a 有了 lastHitAt
    const hits = manager.findCardsForInjection({ category: "skill-defect" });
    expect(hits[0].cardId).toBe("epc:a");
  });
});

describe("formatCardsAsReminder (contract §2)", () => {
  let tmpDir: string;
  let manager: MemoryManager;
  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-fmt-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });
  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });
  const store1 = (): void => {
    manager.storeErrorPatternCard({
      cardId: "epc:deploy-schema-check",
      errorSignature: { trigger: "before deploying a schema change", symptom: "runtime rejects new fields" },
      rootCauseCategory: "skill-defect",
      resolution: "run schema validation first. Then deploy with a dry run.",
      provenance: { source: "remember" },
    });
  };

  it("#9 known card → exact contract block format (header/line/provenance/first sentence)", () => {
    store1();
    const cards = manager.findCardsForInjection({ triggerQuery: "before deploying a schema change" });
    const block = manager.formatCardsAsReminder(cards);
    expect(block).toBe(
      "[Error Pattern Cards]\n" +
      "- ⚠️ [epc:deploy-schema-check | root: skill-defect | from: remember] " +
      "before deploying a schema change → run schema validation first."
    );
  });

  it("#10 empty list → empty string (no bare header)", () => {
    expect(manager.formatCardsAsReminder([])).toBe("");
  });

  it("#11 maxChars truncation drops whole cards + suppressed trailer", () => {
    store1();
    manager.storeErrorPatternCard({
      cardId: "epc:second",
      errorSignature: { trigger: "when restarting the gateway cluster", symptom: "sessions drop" },
      rootCauseCategory: "state-defect",
      resolution: "drain sessions before restart",
      provenance: { source: "review" },
    });
    const cards = manager.findCardsForInjection({ limit: 5 });
    // 预算 = 恰好容纳第一张卡的完整块 → 第二张必超
    const singleBlock = manager.formatCardsAsReminder([cards[0]]);
    const two = manager.formatCardsAsReminder(cards, { maxChars: singleBlock.length });
    expect(two).toContain("epc:");
    expect(two.split("\n").filter((l) => l.startsWith("- ⚠️")).length).toBe(1);
    expect(two).toContain("(+1 more suppressed)");
  });

  it("#12 truncation boundary: budget exactly fits all cards → no suppression", () => {
    store1();
    const cards = manager.findCardsForInjection({ triggerQuery: "schema" });
    const full = manager.formatCardsAsReminder(cards);
    expect(manager.formatCardsAsReminder(cards, { maxChars: full.length })).toBe(full);
  });
});

describe("frozen-surface regression (v7.6.0 semantics unchanged)", () => {
  let tmpDir: string;
  let manager: MemoryManager;
  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-epc-frz-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    manager = new MemoryManager({ workspace: tmpDir, autoDetect: false });
  });
  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("#13 ADR-006 gate replay: V3c invalid enum still rejected", () => {
    const r = manager.storeErrorPatternCard({
      cardId: "epc:bad",
      errorSignature: { trigger: "t", symptom: "s" },
      rootCauseCategory: "not-a-category" as never,
      resolution: "a resolution long enough to pass V3b floor check",
      provenance: { source: "remember" },
    });
    expect(r.ok).toBe(false);
    if (!r.ok) expect(r.ruleId).toBe("V3c");
  });

  it("#14 hit writeback replay: HIT_WINDOW=5 non-avoided demotes; avoided revives", () => {
    manager.storeErrorPatternCard({
      cardId: "epc:cycle",
      errorSignature: { trigger: "t", symptom: "s" },
      rootCauseCategory: "skill-defect",
      resolution: "a resolution long enough to pass V3b floor check",
      provenance: { source: "remember" },
    });
    for (let i = 0; i < 4; i++) manager.recordErrorPatternHit("epc:cycle", { avoided: false });
    const fifth = manager.recordErrorPatternHit("epc:cycle", { avoided: false });
    expect(fifth.inactive).toBe(true);
    const revive = manager.recordErrorPatternHit("epc:cycle", { avoided: true });
    expect(revive.inactive).toBe(false);
  });

  it("#15 enum stub alignment: mem literals == rsi literals (source-lock against drift)", () => {
    // mem 是 source of truth（types.ts 注释）；本测试从 claw-rsi 原件提取字面量比对
    const rsiSrc = fs.readFileSync(
      path.join(__dirname, "../../../claw-rsi/src/analyzer.ts"), "utf-8"
    );
    const m = rsiSrc.match(/RootCauseCategoryLiteral\s*=\s*([\s\S]*?);/);
    expect(m).not.toBeNull();
    const literals = [...(m![1].match(/"([a-z-]+)"/g) ?? [])].map((s) => s.slice(1, -1)).sort();
    expect(literals).toEqual(["invocation-timing", "skill-defect", "state-defect", "transition-judgment"]);
    // triggerSimilarity 导出面可用（裁决 #1 公开）
    expect(typeof triggerSimilarity).toBe("function");
    expect(triggerSimilarity("abc", "abc")).toBe(1);
  });
});
