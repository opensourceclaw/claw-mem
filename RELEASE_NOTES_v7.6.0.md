# claw-mem v7.6.0 Release Notes — Error Pattern Cards

**Release Date:** 2026-09-06
**Type:** Minor (feature) release

---

## Overview

v7.6.0 introduces **error pattern cards** — a curated memory type that makes
"mistakes we must not repeat" first-class, attributable, and effective.

The feature is grounded in two research lines. SWE-Milestone
(arXiv 2603.13428 v4) documents that logic errors recur across milestones at
substantial rates when failure lessons are never explicitly recorded, never
attributed, and never surfaced ahead of similar tasks. Recuris
(arXiv 2608.24876 v1) contributes the mechanism: a four-component attribution
of each failure (the defect in the skill/lesson itself, missing task-state
bookkeeping, mistimed recall, and wrong completion predicates) plus a
write-time validation gate. claw-mem maps that vocabulary onto its own memory
surface rather than adopting it wholesale — the mapping is fixed in ADR-003
through ADR-006, and claw-rsi's future card-production contract aligns to this
side as the source of truth.

## What's New

- **Card type + versioned storage (ADR-003)**: a structured card
  (`errorSignature.trigger` → `symptom` → `rootCauseCategory` → `resolution`)
  stored in the L3 curated layer with its own version chain
  (`memory/error-pattern-cards/{cardId}.json`). Re-storing the same `cardId`
  is an *edit* (archive old → store new), so a recurring mistake improves one
  card instead of spawning duplicates.
- **Attribution enum (ADR-004)**: `skill-defect` / `state-defect` /
  `invocation-timing` / `transition-judgment`, runtime-validated and pinned
  against the rsi planning stub by a literal alignment test.
- **Effectiveness closed loop (ADR-005)**: hit recording with avoided /
  non-avoided counters, lazy demotion after repeated non-avoided hits or
  idle grace, automatic revive on the first avoided hit, inactive cards
  excluded from default queries and downranked in signature matching.
- **Write validation gate (ADR-006)**: field-completeness, provenance, and
  consistency checks at the dedicated store entry; near-duplicate triggers
  produce an advisory (edit the existing card) rather than a rejection; every
  reject and warning is traced to an append-only trail
  (`memory/error-pattern-card-rejections/`) and queryable via
  `listErrorPatternRejections`.
- **Authoring surface**: a new `memory_error_pattern_card_store` tool
  (16 → 17 tools, additive only), plus intent recognition on `memory_store`
  text (`错误模式卡` / `error pattern` prefix + JSON). Incomplete payloads are
  guided back with the missing field list — never silently dropped.

## Honest Boundaries

This release ships mechanisms, not calibrated numbers. The effectiveness
fields start at constant initial values because no real-world hit data exists
yet; demotion windows and the similarity threshold are documented initial
guesses awaiting calibration, and no pseudo-calibrated figures are presented.
`verification` is optional — no fabricated verification commands. The rsi
production interface remains a reserved surface: nothing assumes it has fired.

## Compatibility

Additive only. The generic store refuses `error_pattern_card` explicitly
(strong schema must not route around the gate); the eight existing storage
strategies, plugin tool signatures, and bridge methods are unchanged.

## Tests

Full suite 961 passing (78 files) at release time, including chain-integrity
tests for hit recording and literal-locked tests for the trigger-similarity
algorithm.

---
