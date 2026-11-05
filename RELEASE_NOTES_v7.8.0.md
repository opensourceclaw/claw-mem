## Release Highlights

claw-mem v7.8.0 extends the card system from error-side to dual-side: success strategy cards join error pattern cards in one versioned store, turning "what worked" into a first-class, reusable memory object — paired with a policy composition framework that makes memory strategy explicit, inspectable, and measurable.

### Success Strategy Cards (dual-side card store)
- `ErrorPatternCard` / `ErrorPatternCardInput` gain additive `cardType` (`"error-pattern"` | `"success-strategy"`) and `successStrategy` payload (subtype: procedural / strategic / tool-usage; applicableWhen; steps). Legacy cards need zero migration.
- New `V1'` write-gate rule: dual-state guard (success cards require payload; error cards reject it), with subtype enum and non-empty steps validation.
- Injection surface: `findCardsForInjection` / `queryErrorPatternCards` accept `cardType` (default preserves v7.7.0 behavior byte-for-byte); strategy cards render as `✅ [strategy:<subtype>]` lines under an `[Experience Cards]` header.
- This store is the frozen consumption contract for claw-rsi's success-card producer side.

### Policy Composition Framework
- `describeActivePolicies()` projects the six active strategy slots (retention decay ρ=0.85 / streak cap 5 / grace period 30 / hit window 5 / importance weights / usage boost) as a read-only view — explicit, not behavior-changing.
- Optional workspace config override (`memory/policy-composition.json`, shallow-merge, corruption-safe fallback); apply supports replay-only in this version. No auto-tuning.
- Factor-experiment protocol with append-only records (`memory/policy-experiments/`) — measurement first, proposals require review.

### Lifecycle Fields (no fabrication)
- `CardEffectiveness.lifecycle` gains `stableRuns` / `backwardRetention` / `pathAttribution` — host-reported via `recordErrorPatternHit` opts, persisted and surfaced, never synthesized.

### Cross-Repo Integrity Lock
- Vendored snapshot of claw-rsi's lifecycle field declarations with a bidirectional source-lock test: renaming fields on either side turns both repos' CI red.

**Compatibility**: v7.6/v7.7 card behavior preserved byte-for-byte on default paths; 1004 tests green; `tsc` clean.

**Full Changelog**: https://github.com/opensourceclaw/claw-mem/compare/v7.7.0...v7.8.0
