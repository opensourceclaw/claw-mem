// triggerSimilarity locked-algorithm tests (v7.6.0, ADR-006 V3a)
// Overlap coefficient over character bigrams of the lowercased,
// non-alphanumeric/CJK-stripped trigger. Do not change semantics without
// updating these literals.

import { describe, it, expect } from "vitest";
import { triggerSimilarity } from "../../src/storage/error-pattern-card/similarity.js";

describe("triggerSimilarity (ADR-006 V3a, locked algorithm)", () => {
  it("identical triggers score 1.0", () => {
    expect(triggerSimilarity("before deploying a schema change", "before deploying a schema change")).toBe(1);
  });

  it("a trigger extended by a tail is 1.0 (suffix words overlap fully)", () => {
    expect(
      triggerSimilarity("before deploying a schema change", "before deploying a schema change to production"),
    ).toBe(1);
  });

  it("normalizes case and punctuation before comparing", () => {
    expect(triggerSimilarity("Before Deploying - A Schema Change!", "before deploying a schema change")).toBe(1);
  });

  it("scores partial overlap below the threshold (0.714 < 0.8)", () => {
    // normalized "abcdefgh" vs "abcdefzz": bigrams ab,bc,cd,de,ef shared of min 7
    expect(triggerSimilarity("ab cd ef gh", "ab cd ef zz")).toBeCloseTo(5 / 7, 5);
  });

  it("scores disjoint triggers 0", () => {
    expect(triggerSimilarity("abc", "xyz")).toBe(0);
  });

  it("handles empty inputs as 0", () => {
    expect(triggerSimilarity("", "before deploying a schema change")).toBe(0);
    expect(triggerSimilarity("before deploying a schema change", "")).toBe(0);
  });
});
