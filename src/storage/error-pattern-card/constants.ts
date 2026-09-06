// Error pattern card effectiveness constants (v7.6.0, ADR-005)
// Initial values awaiting real-data calibration — documented as uncalibrated;
// no pseudo-calibration of numbers with no data behind them.
export const GRACE_PERIOD_DAYS = 30; // never-hit idle window before demotion
export const HIT_WINDOW = 5; // consecutive non-avoided hits -> demotion
