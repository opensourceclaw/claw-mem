// Copyright 2026 OpenSourceClaw Contributors
// v7.10.0 (ADR-007): MemoryRecord schema extension — records with and without
// evidence[]/eventTime round-trip without mutating legacy records.

import { describe, it, expect } from "vitest";
import type { MemoryEvidence, MemoryRecord } from "../../src/types";

function legacyRecord(): MemoryRecord {
  return {
    id: "mem-legacy",
    text: "Legacy record without evidence.",
    memory_type: "episodic",
    created_at: "2026-11-16T10:00:00.000Z",
    metadata: { session_id: "s-legacy" },
    tags: ["legacy"],
  };
}

function evidenceRecord(): MemoryRecord {
  return {
    id: "mem-evidence",
    text: "Peter prefers dark mode; the decision was discussed on 2026-11-15.",
    memory_type: "semantic",
    created_at: "2026-11-16T11:00:00.000Z",
    metadata: {},
    tags: ["preference"],
    eventTime: "2026-11-15",
    evidence: [
      {
        span: "Peter prefers dark mode",
        offset: 0,
        eventTime: "2026-11-15",
        sourceRefs: ["session-abc", "memory/2026-11-15.md"],
      },
    ],
  };
}

describe("MemoryRecord evidence schema (v7.10.0, ADR-007)", () => {
  it("legacy records keep exactly their pre-v7.10 shape", () => {
    const record = legacyRecord();
    expect("evidence" in record).toBe(false);
    expect("eventTime" in record).toBe(false);
  });

  it("records with evidence and eventTime survive a JSON round-trip", () => {
    const record = evidenceRecord();
    const roundtripped = JSON.parse(JSON.stringify(record)) as MemoryRecord;

    expect(roundtripped).toEqual(record);
    expect(roundtripped.evidence).toEqual(record.evidence);
    expect(roundtripped.eventTime).toBe("2026-11-15");
  });

  it("records without evidence round-trip unchanged (backward compatibility)", () => {
    const record = legacyRecord();
    const roundtripped = JSON.parse(JSON.stringify(record)) as MemoryRecord;
    expect(roundtripped).toEqual(record);
  });

  it("MemoryEvidence requires span + sourceRefs; offset/eventTime are optional", () => {
    const minimal: MemoryEvidence = { span: "x", sourceRefs: ["session-1"] };
    expect(minimal.offset).toBeUndefined();
    expect(minimal.eventTime).toBeUndefined();
    expect(Array.isArray(minimal.sourceRefs)).toBe(true);
  });

  it("eventTime keeps the original precision (YYYY / YYYY-MM / YYYY-MM-DD)", () => {
    for (const eventTime of ["2026", "2026-11", "2026-11-16"]) {
      const record = { ...evidenceRecord(), eventTime };
      expect(JSON.parse(JSON.stringify(record)).eventTime).toBe(eventTime);
    }
  });
});
