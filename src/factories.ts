// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — ComponentFactory (Dependency Injection | TS)
 */

import { SynonymExpander } from "./retrieval/synonym.js";
import { QueryCache } from "./retrieval/query_cache.js";
import { CacheManager } from "./cache/index.js";

export interface FactoryConfig {
  maxCacheSize?: number;
  cacheTtlSec?: number;
  compressionThreshold?: number;
  enableCompression?: boolean;
  enableGating?: boolean;
  enableDecay?: boolean;
  enableGraph?: boolean;
}

export class ComponentFactory {
  private _config: FactoryConfig;
  private _instances: Map<string, unknown> = new Map();

  constructor(config: FactoryConfig = {}) {
    this._config = config;
  }

  get config(): FactoryConfig { return this._config; }

  // ── Retrieval Components ──────────────────────────────────────

  createSynonymExpander(customSynonyms?: Record<string, string[]>,
                        enabled = true, maxExpansions = 5): SynonymExpander {
    const key = `synonym_${enabled}_${maxExpansions}`;
    if (this._instances.has(key)) return this._instances.get(key) as SynonymExpander;
    const se = new SynonymExpander(customSynonyms, enabled, maxExpansions);
    this._instances.set(key, se);
    return se;
  }

  createQueryCache(maxSize?: number, ttlSeconds?: number): QueryCache {
    const key = `cache_${maxSize ?? 1000}_${ttlSeconds ?? 300}`;
    if (this._instances.has(key)) return this._instances.get(key) as QueryCache;
    const qc = new QueryCache(maxSize ?? 1000, ttlSeconds ?? 300);
    this._instances.set(key, qc);
    return qc;
  }

  // ── Cache Components ───────────────────────────────────────────

  createCacheManager(config?: Record<string, unknown>): CacheManager {
    const key = `cache_manager_${JSON.stringify(config ?? {})}`;
    if (this._instances.has(key)) return this._instances.get(key) as CacheManager;
    const cm = new CacheManager(config as Record<string, unknown>);
    this._instances.set(key, cm);
    return cm;
  }

  // ── Generic ───────────────────────────────────────────────────

  getInstance<T>(key: string, factory: () => T): T {
    if (this._instances.has(key)) return this._instances.get(key) as T;
    const inst = factory();
    this._instances.set(key, inst);
    return inst;
  }

  clear(): void {
    this._instances.clear();
  }
}

export function getDefaultFactory(): ComponentFactory {
  if (!_default) _default = new ComponentFactory();
  return _default;
}
export function resetDefaultFactory(): void { _default = null; }

let _default: ComponentFactory | null = null;
