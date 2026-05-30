// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * claw-mem decay module - Oblivion forgetting mechanism (v2.14.0+)
 *
 * Provides edge-level exponential decay for the MultiGraphMemory,
 * replacing the legacy MemoryDecay class.
 *
 * Core components:
 *   - DecayConfig: Tunable configuration.
 *   - DecayController: Edge weight computation and cleanup.
 *   - DecayScheduler: Periodic + event-driven decay triggering.
 *   - TieredDecayEngine (v4.7.0): HOT/WARM/COLD tier lifecycle management.
 */

export {
  exponentialDecay,
  calculateWeight,
  halfLifeToDays,
  HALF_LIFE,
  LAMBDA,
  type DecayConfig,
  DEFAULT_DECAY_CONFIG,
} from "./functions";
export { DecayController } from "./controller";
export { DecayScheduler } from "./scheduler";
export { TieredDecayEngine, TierLevel } from "./tiered_decay";
