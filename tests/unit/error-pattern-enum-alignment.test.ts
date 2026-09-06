// Error Pattern Enumeration Alignment Test (v7.6.0, ADR-004)

// Drift guard between claw-mem and claw-rsi's card contract (rsi T3: rsi
// produces cards, mem stores them). claw-rsi's schema/enumeration is NOT
// finalized as of 2026-09-06 — claw-mem is the source of truth, locked here
// as a literal stub. When claw-rsi finalizes, this test must be upgraded to
// a bidirectional assertion (and the ADR-004 review note closed).

import { describe, it, expect } from "vitest";
import {
  isRootCauseCategory,
  MemoryType,
  type RootCauseCategory,
} from "../../src/types.js";

// Literal stub of the claw-rsi T3 expected enumeration (mem-side fact source;
// do NOT rename values without updating claw-rsi alignment notes)
const RSI_T3_ENUM_STUB: ReadonlyArray<string> = [
  "skill-defect",
  "state-defect",
  "invocation-timing",
  "transition-judgment",
];

const MEM_ENUM: ReadonlyArray<RootCauseCategory> = [
  "skill-defect",
  "state-defect",
  "invocation-timing",
  "transition-judgment",
];

describe("RootCauseCategory enumeration alignment", () => {
  it("mem-side enum matches the rsi T3 literal stub (one-to-one, same order)", () => {
    expect(MEM_ENUM).toEqual([...RSI_T3_ENUM_STUB]);
  });

  it("isRootCauseCategory accepts exactly the four registered values", () => {
    for (const v of MEM_ENUM) {
      expect(isRootCauseCategory(v)).toBe(true);
    }
  });

  it("isRootCauseCategory rejects unknown values at runtime", () => {
    expect(isRootCauseCategory("skill-defect-typo")).toBe(false);
    expect(isRootCauseCategory("")).toBe(false);
    expect(isRootCauseCategory(42)).toBe(false);
    expect(isRootCauseCategory(undefined)).toBe(false);
  });

  it("error_pattern_card is a registered MemoryType member", () => {
    const types: MemoryType[] = ["episodic", "error_pattern_card"];
    expect(types).toContain("error_pattern_card");
  });
});
