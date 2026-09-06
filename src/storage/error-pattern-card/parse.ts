// remember-intent parsing for error pattern cards (v7.6.0, design §3.4).
// Pure rules, no LLM: a `错误模式卡` / `error pattern` prefix marks card
// intent; the payload is extracted as JSON (or flat key: value is NOT
// guessed — incomplete payloads are guided back, never silently mis-stored
// as episodic text). cardId suggestion is a semantic slug of the trigger so
// recurring mistakes edit the same card instead of creating duplicates.

import type { ErrorPatternCardInput } from "../../types.js";
import { isRootCauseCategory } from "../../types.js";

export type ParseCardResult =
  | { kind: "card"; input: ErrorPatternCardInput }
  | { kind: "other" }
  | { kind: "card-incomplete"; missing: string[]; guide: string };

export const CARD_INTENT_PREFIX = /^\s*(错误模式卡|error\s*pattern)\s*[:：\s]*/i;

const FIELD_ALIASES: Record<string, string> = {
  card_id: "cardId",
  root_cause_category: "rootCauseCategory",
  provenance_source: "source",
  provenance_author: "author",
};

export function parseCardIntentText(text: string): ParseCardResult {
  const body = String(text ?? "").trim();
  const m = CARD_INTENT_PREFIX.exec(body);
  if (!m) return { kind: "other" };
  const payload = body.slice(m[0].length).trim();
  if (!payload) {
    return {
      kind: "card-incomplete",
      missing: ["trigger", "symptom", "rootCauseCategory", "resolution"],
      guide: "错误模式卡需要结构化字段:请用 memory_error_pattern_card_store 工具填写 trigger / symptom / rootCauseCategory(四枚举之一: skill-defect, state-defect, invocation-timing, transition-judgment)/ resolution(≥20 字符)/ 可选 verification",
    };
  }

  let raw: unknown;
  try {
    raw = JSON.parse(payload.replace(/^```(json)?|```$/g, ""));
  } catch {
    return {
      kind: "card-incomplete",
      missing: ["trigger", "symptom", "rootCauseCategory", "resolution"],
      guide: `「${payload.slice(0, 60)}…」不是可解析的 JSON — 请提供结构化字段(见 memory_error_pattern_card_store)`,
    };
  }
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
    return {
      kind: "card-incomplete",
      missing: ["trigger", "symptom", "rootCauseCategory", "resolution"],
      guide: "错误模式卡载荷需为 JSON 对象",
    };
  }

  const o = raw as Record<string, unknown>;
  const get = (canonical: string): unknown => {
    const keys = new Set<string>([canonical, snake(canonical)]);
    for (const [alias, value] of Object.entries(FIELD_ALIASES)) {
      if (value === canonical) keys.add(alias);
    }
    for (const k of keys) {
      if (o[k] !== undefined) return o[k];
    }
    return undefined;
  };
  const trigger = typeof get("trigger") === "string" ? (get("trigger") as string).trim() : "";
  const cardId = typeof get("cardId") === "string" && (get("cardId") as string).trim()
    ? (get("cardId") as string).trim()
    : suggestCardId(trigger);
  const symptom = typeof get("symptom") === "string" ? (get("symptom") as string).trim() : "";
  const rootCauseCategory = get("rootCauseCategory");
  const resolution = typeof get("resolution") === "string" ? (get("resolution") as string).trim() : "";
  const verification = typeof get("verification") === "string" && (get("verification") as string).trim()
    ? (get("verification") as string).trim()
    : undefined;
  const source = typeof get("source") === "string" && (get("source") as string).trim()
    ? (get("source") as string).trim()
    : "remember";
  const author = typeof get("author") === "string" && (get("author") as string).trim()
    ? (get("author") as string).trim()
    : undefined;

  const missing: string[] = [];
  if (!trigger) missing.push("trigger");
  if (!symptom) missing.push("symptom");
  if (!isRootCauseCategory(rootCauseCategory)) missing.push("rootCauseCategory");
  if (!resolution) missing.push("resolution");
  if (missing.length > 0) {
    return {
      kind: "card-incomplete",
      missing,
      guide: `缺少字段: ${missing.join(", ")} — 请补全后重试(或改用 memory_error_pattern_card_store)`,
    };
  }
  return {
    kind: "card",
    input: {
      ...(cardId ? { cardId } : {}),
      errorSignature: { trigger, symptom },
      rootCauseCategory: rootCauseCategory as ErrorPatternCardInput["rootCauseCategory"],
      resolution,
      ...(verification ? { verification } : {}),
      provenance: { source, ...(author ? { author } : {}) },
    },
  };
}

/** Semantic cardId suggestion: epc:{trigger slug}, stable for edit-on-recur. */
export function suggestCardId(trigger: string): string | undefined {
  const slug = String(trigger ?? "")
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40);
  return slug ? `epc:${slug}` : undefined;
}

/**
 * Assemble a card input from flat JSON-RPC params (bridge store face):
 * card_id / trigger / symptom / root_cause_category / resolution /
 * verification / source / author. provenance.source defaults to "remember"
 * when absent — rsi must pass source="rsi:analyze" explicitly.
 */
export function buildCardInputFromParams(
  params: Record<string, unknown>,
): { input: ErrorPatternCardInput } | { missing: string[] } {
  const trigger = typeof params.trigger === "string" ? params.trigger.trim() : "";
  const symptom = typeof params.symptom === "string" ? params.symptom.trim() : "";
  const resolution = typeof params.resolution === "string" ? params.resolution.trim() : "";
  const rootCauseCategory = params.root_cause_category;
  const cardId = typeof params.card_id === "string" && params.card_id.trim()
    ? params.card_id.trim()
    : suggestCardId(trigger);
  const verification = typeof params.verification === "string" && params.verification.trim()
    ? params.verification.trim()
    : undefined;
  const source = typeof params.source === "string" && params.source.trim()
    ? params.source.trim()
    : "remember";
  const author = typeof params.author === "string" && params.author.trim() ? params.author.trim() : undefined;

  const missing: string[] = [];
  if (!trigger) missing.push("trigger");
  if (!symptom) missing.push("symptom");
  if (!isRootCauseCategory(rootCauseCategory)) missing.push("root_cause_category");
  if (!resolution) missing.push("resolution");
  if (missing.length > 0) return { missing };

  return {
    input: {
      ...(cardId ? { cardId } : {}),
      errorSignature: { trigger, symptom },
      rootCauseCategory: rootCauseCategory as ErrorPatternCardInput["rootCauseCategory"],
      resolution,
      ...(verification ? { verification } : {}),
      provenance: { source, ...(author ? { author } : {}) },
    },
  };
}

function snake(k: string): string {
  return k.replace(/[A-Z]/g, (c: string) => `_${c.toLowerCase()}`);
}
