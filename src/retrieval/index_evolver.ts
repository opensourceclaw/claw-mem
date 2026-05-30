// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Index Evolver (adaptive rebuild)
 *
 * Monitors access frequency and write volume to trigger
 * incremental index rebuilds for hot data.
 */

import type { InMemoryIndex } from "../storage/index";
interface MemoryEntry { id: string; content: string; }

export interface EvolverConfig {
  accessThreshold?: number;   // Access count to trigger rebuild
  writeThreshold?: number;    // Write count to trigger incremental rebuild
  rebuildIntervalMs?: number; // Minimum interval between rebuilds
}

export class IndexEvolver {
  private _index: InMemoryIndex;
  private _accessCount = 0;
  private _writeCount = 0;
  private _lastRebuild = 0;
  private _config: Required<EvolverConfig>;

  constructor(index: InMemoryIndex, config: EvolverConfig = {}) {
    this._index = index;
    this._config = {
      accessThreshold: config.accessThreshold ?? 1000,
      writeThreshold: config.writeThreshold ?? 100,
      rebuildIntervalMs: config.rebuildIntervalMs ?? 60000,
    };
  }

  /** Record an access (search) and check if rebuild needed. */
  touchAccess(count = 1): void {
    this._accessCount += count;
    this._maybeRetrigger();
  }

  /** Record a write and check if incremental rebuild needed. */
  touchWrite(count = 1): void {
    this._writeCount += count;
    this._maybeRetrigger();
  }

  get stats(): Record<string, unknown> {
    return {
      accessCount: this._accessCount,
      writeCount: this._writeCount,
      lastRebuild: new Date(this._lastRebuild).toISOString(),
      indexBuilt: this._index.built,
      bm25Docs: this._index.bm25.doc_count,
    };
  }

  private _maybeRetrigger(): void {
    const now = Date.now();
    if (now - this._lastRebuild < this._config.rebuildIntervalMs) return;
    if (this._writeCount >= this._config.writeThreshold) {
      // Rebuild: incremental (existing loadOrBuild works)
      this._index.loadOrBuild([]);
      this._lastRebuild = now;
      this._writeCount = 0;
    }
  }
}
