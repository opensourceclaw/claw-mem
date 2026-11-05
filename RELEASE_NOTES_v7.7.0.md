# claw-mem v7.7.0 Release Notes — Error Pattern Card Injection

**Release Date:** 2026-09-13
**Type:** Minor (feature) release

---

## Overview

v7.6.0 introduced error pattern cards as a first-class memory type; v7.7.0 adds the
**injection path** — the surface that lets a host agent surface the right card *ahead of*
a similar task, rather than only looking it up after the fact.

The release is deliberately thin: two additive methods and two exports. The card schema,
the effectiveness closed loop, the ADR-006 write gate and the existing query behaviour are
untouched. What is new is a single, contract-owned way to ask "which cards apply to this
situation?" and a single, contract-owned way to render them.

## What's New

- **`findCardsForInjection({ triggerQuery?, triggerThreshold?, category?, limit? })`** —
  trigger similarity reuses the existing `triggerSimilarity` (bigram overlap; the algorithm
  is locked), and the default threshold is `SIMILARITY_THRESHOLD`, so duplicate detection and
  retrieval share one definition of "similar". `category` filtering and active-only semantics
  follow the existing card queries, including read-time lazy demotion; **inactive cards never
  enter the injection surface** (they are filtered before similarity is computed). Ordering is
  similarity descending, then `lastHitAt` descending with never-hit cards last. With no
  `triggerQuery` the recency path is used. No match returns an honest empty array.
- **`formatCardsAsReminder(cards, { maxChars? })`** — a pure function and the contract's single
  rendering owner: an `[Error Pattern Cards]` header, one line per card
  (`cardId | root cause | source` → trigger → resolution first sentence), whole-card truncation
  with a `(+N more suppressed)` tail, and an empty string for an empty array (never a bare header).
- **Public surface** — `triggerSimilarity` and `SIMILARITY_THRESHOLD` are exported, since the
  host side and the contract tests depend on the same definition.
- **Contract status** — `docs/contracts/error-card-injection-contract.md` moves from Draft to
  **Active**, matching the shipped implementation.
- **Version-drift closure (protocol v4.3.1)** — the runtime version constant still reported the
  previous minor at release time. v7.7.0 fixes `src/version.ts` and adds a machine-checked
  consistency test asserting the constant and the two manifests agree; the test was verified to
  actually fail under a deliberate perturbation before being restored, so the drift cannot
  recur silently.

## Honest Boundaries

This release ships mechanisms, not calibrated numbers. The retrieval limit, the block capacity
budget and the similarity threshold are documented initial defaults awaiting calibration against
real corpora; no pseudo-calibrated figures are presented. Hit recording is unchanged from v7.6.0 —
v7.7.0 adds no new statistics API.

## Compatibility

Additive only. Two methods and two exports are added; the card schema, version chain,
ADR-006 gate, T4 filter and all existing query behaviour are unchanged. The contract's status
line is the only edited document.

## Tests

Full suite 980 passing across 80 files at release time, including 15 new injection tests
(retrieval, threshold source-lock, honest empty, category combinations, inactive-never-injected
plus revive-after-avoidance, limit default, dual-key ordering, exact format assertions,
whole-card truncation, and the stored-procedure replay evidence from the frozen layer), plus the
new version-consistency test.

---
