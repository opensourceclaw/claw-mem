// Error pattern card effectiveness constants (v7.6.0, ADR-005/006)
// Initial values awaiting real-data calibration — documented as uncalibrated;
// no pseudo-calibration of numbers with no data behind them.
export const GRACE_PERIOD_DAYS = 30; // never-hit idle window before demotion
export const HIT_WINDOW = 5; // consecutive non-avoided hits -> demotion
export const RESOLUTION_MIN_CHARS = 20; // V3b: resolution length floor (anti-fluff)
export const SIMILARITY_THRESHOLD = 0.8; // V3a: trigger duplicate suspicion threshold
