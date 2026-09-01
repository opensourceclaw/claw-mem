// claw-mem v7.5.1 — ChainVisualizer mermaid escaping tests
//
// CodeQL js/incomplete-sanitization (#11/#12): escapeMermaid must escape
// backslashes before inserting \[ \] escapes, plus Mermaid comment (#) and
// statement separator (;) characters, so crafted labels cannot bypass
// sanitization or inject graph structure.
//
// Licensed under the Apache License, Version 2.0

import { describe, expect, it } from "vitest";
import { ChainVisualizer } from "../../src/inference/chain-visualizer";
import type { InferenceChain } from "../../src/inference/types";

function makeChain(query: string): InferenceChain {
  return {
    chainId: "escape-test",
    query,
    steps: [],
    result: [],
    confidence: 1.0,
    timestamp: 0,
    version: "1",
  };
}

/** Render the query node label line: `    Q["<escaped>"]` */
function queryLabel(query: string): string {
  const mermaid = new ChainVisualizer().renderMermaid(makeChain(query));
  const line = mermaid.split("\n").find((l) => l.trim().startsWith('Q["'));
  if (!line) throw new Error("query node not rendered");
  return line.trim();
}

describe("ChainVisualizer mermaid escaping (v7.5.1, CodeQL incomplete-sanitization)", () => {
  it("escapes a bare backslash first", () => {
    expect(queryLabel(`a\\b`)).toBe(`Q["a\\\\b"]`);
  });

  it("backslash-escaped brackets survive without re-escaping the inserted slash", () => {
    // user input `\[x\]` must render as literal \[x\] in mermaid,
    // not as a broken/unbalanced escape (the CodeQL bypass vector)
    expect(queryLabel(`\\[x\\]`)).toBe(`Q["\\\\\\[x\\\\\\]"]`);
  });

  it("handles combined backslash + comment-injection payload", () => {
    expect(queryLabel(`\\#[x]`)).toBe(`Q["\\\\\\#\\[x\\]"]`);
  });

  it("escapes Mermaid comment char #", () => {
    expect(queryLabel(`note #1`)).toBe(`Q["note \\#1"]`);
  });

  it("escapes Mermaid statement separator ;", () => {
    expect(queryLabel(`a;b`)).toBe(`Q["a\\;b"]`);
  });

  it("replaces double quotes", () => {
    expect(queryLabel(`say "hi"`)).toBe(`Q["say 'hi'"]`);
  });

  it("replaces newlines with <br/>", () => {
    expect(queryLabel(`line1\nline2`)).toBe(`Q["line1<br/>line2"]`);
  });

  it("escapes brackets", () => {
    expect(queryLabel(`a[b]c`)).toBe(`Q["a\\[b\\]c"]`);
  });

  it("full adversarial payload: every metacharacter fully escaped in label", () => {
    const label = queryLabel(`a\\b#[x];"c"\n`);
    const inner = label.slice(3, -2); // strip Q[" and "]"
    // backslash first, then #, ;, quote, newline, brackets — in that order;
    // no raw metacharacter (unpaired escape) may survive
    expect(inner).toBe(`a\\\\b\\#\\[x\\]\\;'c'<br/>`);
    expect(inner).not.toContain("\n");
    expect(inner).not.toMatch(/(?<!\\)[#;"\[\]]/);
    expect(inner).not.toMatch(/(^|[^\\])\\[^\\#;\-\[\]]/);
  });
});
