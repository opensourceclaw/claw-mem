// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * Write-Time Gating
 *
 * Source: Selective Memory paper
 * Core idea: Only store salient information, avoid memory redundancy
 */

import * as fs from "fs";
import * as path from "path";
import { randomUUID } from "crypto";

// ── Data classes ──────────────────────────────────────────────────────

export interface GatingResult {
  stored: boolean;
  tier: "active" | "cold";
  salience_score: number;
  reason?: string;
  timestamp: Date;
}

export interface GatingFilterResult {
  should_store: boolean;
  importance_score: number;
  reason?: string;
  metadata: Record<string, unknown>;
}

// ── GatingFilter ──────────────────────────────────────────────────────

export class GatingFilter {
  static DEFAULT_THRESHOLD = 1.0;

  static TYPE_WEIGHTS: Record<string, number> = {
    semantic: 0.5,
    procedural: 0.3,
    episodic: 0.0,
  };

  private scorer: unknown;
  private threshold: number;
  private custom_score_func?: (memory: Record<string, unknown>) => number;

  constructor(
    scorer?: unknown,
    threshold: number = GatingFilter.DEFAULT_THRESHOLD,
    custom_score_func?: (memory: Record<string, unknown>) => number,
  ) {
    this.scorer = scorer;
    this.threshold = threshold;
    this.custom_score_func = custom_score_func;

    if (this.scorer == null && this.custom_score_func == null) {
      this.scorer = new DefaultImportanceScorer();
    }
  }

  should_store(memory: Record<string, unknown>): GatingFilterResult {
    let score: number;
    if (this.custom_score_func) {
      score = this.custom_score_func(memory);
    } else if (this.scorer && typeof (this.scorer as any).calculate === "function") {
      score = (this.scorer as any).calculate(memory).total_score;
    } else {
      score = this._default_score(memory);
    }

    const shouldStore = score >= this.threshold;
    const reason = this._generate_reason(memory, score, shouldStore);

    return {
      should_store: shouldStore,
      importance_score: score,
      reason,
      metadata: {
        memory_type: memory.memory_type ?? "unknown",
        threshold: this.threshold,
      },
    };
  }

  private _default_score(memory: Record<string, unknown>): number {
    let score = 1.0;

    const memType = (memory.memory_type as string) ?? "episodic";
    score += GatingFilter.TYPE_WEIGHTS[memType] ?? 0.0;

    const accessCount = (memory.access_count as number) ?? 0;
    if (accessCount > 10) {
      score += 0.3;
    } else if (accessCount > 5) {
      score += 0.2;
    } else if (accessCount > 1) {
      score += 0.1;
    }

    const source = (memory.source as string) ?? "system";
    if (source === "user") {
      score += 0.2;
    } else if (source === "agent") {
      score += 0.1;
    }

    return Math.min(2.0, score);
  }

  private _generate_reason(
    memory: Record<string, unknown>,
    score: number,
    shouldStore: boolean,
  ): string {
    const memType = memory.memory_type ?? "unknown";
    const source = memory.source ?? "unknown";
    if (shouldStore) {
      return `High importance (${score.toFixed(2)} >= ${this.threshold}): type=${memType}, source=${source}`;
    }
    return `Low importance (${score.toFixed(2)} < ${this.threshold}): type=${memType}, source=${source}`;
  }

  set_threshold(threshold: number): void {
    this.threshold = Math.max(0.0, Math.min(2.0, threshold));
  }

  get_threshold(): number {
    return this.threshold;
  }
}

class DefaultImportanceScorer {
  calculate(memory: Record<string, unknown>): { total_score: number } {
    let score = 1.0;
    const memType = (memory.memory_type as string) ?? "episodic";
    const typeWeights: Record<string, number> = {
      semantic: 0.5,
      procedural: 0.3,
      episodic: 0.0,
    };
    score += typeWeights[memType] ?? 0.0;

    const accessCount = (memory.access_count as number) ?? 0;
    if (accessCount > 10) {
      score += 0.3;
    } else if (accessCount > 5) {
      score += 0.2;
    } else if (accessCount > 1) {
      score += 0.1;
    }

    return { total_score: Math.min(2.0, score) };
  }
}

// ── AdaptiveThreshold ─────────────────────────────────────────────────

export class AdaptiveThreshold {
  constructor(
    public base_threshold: number = 1.0,
    public min_threshold: number = 0.5,
    public max_threshold: number = 1.5,
    public memory_capacity: number = 1000,
    public scale_factor: number = 0.5,
  ) {}

  get_threshold(current_memory_count: number): number {
    const usageRatio = current_memory_count / this.memory_capacity;
    const adjusted = (usageRatio - 0.5) * this.scale_factor * 2;
    const threshold = this.base_threshold + adjusted;
    return Math.max(this.min_threshold, Math.min(this.max_threshold, threshold));
  }

  get_stats(current_memory_count: number): Record<string, unknown> {
    const threshold = this.get_threshold(current_memory_count);
    return {
      current_count: current_memory_count,
      capacity: this.memory_capacity,
      usage_ratio: current_memory_count / this.memory_capacity,
      current_threshold: threshold,
      base_threshold: this.base_threshold,
      min_threshold: this.min_threshold,
      max_threshold: this.max_threshold,
    };
  }

  reset(): number {
    return this.base_threshold;
  }
}

// ── InMemoryStorage ───────────────────────────────────────────────────

export class InMemoryStorage {
  private _items: Record<string, unknown>[] = [];

  store(item: Record<string, unknown>): Record<string, unknown> {
    const storedItem = {
      ...item,
      _stored_at: new Date().toISOString(),
      _tier: "active",
    };
    this._items.push(storedItem);
    return storedItem;
  }

  get(key: string): Record<string, unknown> | undefined {
    for (const item of this._items) {
      if (item.id === key || String(item.content ?? "").startsWith(key)) {
        return item;
      }
    }
    return undefined;
  }

  count(): number {
    return this._items.length;
  }

  list_all(): Record<string, unknown>[] {
    return [...this._items];
  }

  clear(): void {
    this._items = [];
  }
}

// ── DiskStorage ───────────────────────────────────────────────────────

export class DiskStorage {
  private _count = 0;

  constructor(private storage_path: string = "/tmp/claw-mem-cold") {
    fs.mkdirSync(storage_path, { recursive: true });
  }

  archive(item: Record<string, unknown>): Record<string, unknown> {
    const storedItem = {
      ...item,
      _stored_at: new Date().toISOString(),
      _tier: "cold",
    };

    const filename = path.join(this.storage_path, `${Date.now()}.json`);
    fs.writeFileSync(filename, JSON.stringify(storedItem));
    this._count++;
    return storedItem;
  }

  count(): number {
    return this._count;
  }

  list_all(): Record<string, unknown>[] {
    const items: Record<string, unknown>[] = [];
    let files: string[];
    try {
      files = fs.readdirSync(this.storage_path);
    } catch {
      return items;
    }
    for (const fname of files) {
      if (fname.endsWith(".json")) {
        const data = fs.readFileSync(path.join(this.storage_path, fname), "utf-8");
        items.push(JSON.parse(data));
      }
    }
    return items;
  }
}

// ── VersionChain ──────────────────────────────────────────────────────

export class VersionChain {
  private _chain: Record<string, unknown>[] = [];

  append(item: Record<string, unknown>): void {
    this._chain.push({ ...item, _version: this._chain.length });
  }

  get(index: number): Record<string, unknown> | undefined {
    if (index >= 0 && index < this._chain.length) {
      return this._chain[index];
    }
    return undefined;
  }

  latest(): Record<string, unknown> | undefined {
    return this._chain.length > 0 ? this._chain[this._chain.length - 1] : undefined;
  }

  get length(): number {
    return this._chain.length;
  }

  clear(): void {
    this._chain = [];
  }
}

// ── SalienceScorer ────────────────────────────────────────────────────

export class SalienceScorer {
  static SOURCE_REPUTATION: Record<string, number> = {
    user: 1.0,
    agent: 0.8,
    system: 0.6,
    external: 0.4,
  };

  weights: Record<string, number>;
  novelty_window: number;
  recent_items: string[] = [];

  constructor(
    weights?: Record<string, number>,
    novelty_window: number = 100,
  ) {
    this.weights = weights ?? {
      source_reputation: 0.4,
      novelty: 0.3,
      reliability: 0.3,
    };
    this.novelty_window = novelty_window;
  }

  compute(item: Record<string, unknown>): number {
    const sourceScore = this._source_reputation((item.source as string) ?? "external");
    const noveltyScore = this._novelty((item.content as string) ?? "");
    const reliabilityScore = this._reliability(item);

    const salience =
      this.weights.source_reputation * sourceScore +
      this.weights.novelty * noveltyScore +
      this.weights.reliability * reliabilityScore;

    this._update_recent((item.content as string) ?? "");
    return salience;
  }

  private _source_reputation(source: string): number {
    return SalienceScorer.SOURCE_REPUTATION[source] ?? 0.5;
  }

  private _novelty(content: string): number {
    if (this.recent_items.length === 0) return 1.0;

    const similarities = this.recent_items.map((recent) =>
      this._simple_similarity(content, recent),
    );
    const avgSimilarity =
      similarities.reduce((a, b) => a + b, 0) / similarities.length;
    return Math.max(0.0, Math.min(1.0, 1.0 - avgSimilarity));
  }

  private _reliability(item: Record<string, unknown>): number {
    let score = 0.5;

    const source = item.source as string;
    if (source === "user" || source === "agent") {
      score += 0.2;
    }

    if (item.verified === true) {
      score += 0.2;
    }

    const context = item.context;
    if (context && typeof context === "object" && Object.keys(context).length > 0) {
      score += 0.1;
    }

    return Math.max(0.0, Math.min(1.0, score));
  }

  private _simple_similarity(text1: string, text2: string): number {
    const words1 = new Set(text1.toLowerCase().split(/\s+/));
    const words2 = new Set(text2.toLowerCase().split(/\s+/));

    if (words1.size === 0 || words2.size === 0) return 0.0;

    let intersection = 0;
    for (const w of words1) {
      if (words2.has(w)) intersection++;
    }

    const union = new Set([...words1, ...words2]);
    return union.size > 0 ? intersection / union.size : 0.0;
  }

  private _update_recent(content: string): void {
    this.recent_items.push(content);
    if (this.recent_items.length > this.novelty_window) {
      this.recent_items.shift();
    }
  }
}

// ── WriteTimeGating ───────────────────────────────────────────────────

export class WriteTimeGating {
  threshold: number;
  active_memory: InMemoryStorage;
  cold_storage: DiskStorage;
  salience_scorer: SalienceScorer;
  version_chain: VersionChain;

  constructor(
    threshold: number = 0.6,
    active_memory?: InMemoryStorage,
    cold_storage?: DiskStorage,
  ) {
    this.threshold = threshold;
    this.active_memory = active_memory ?? new InMemoryStorage();
    this.cold_storage = cold_storage ?? new DiskStorage();
    this.salience_scorer = new SalienceScorer();
    this.version_chain = new VersionChain();
  }

  write(item: Record<string, unknown>): GatingResult {
    const startTime = Date.now();

    const salience = this.salience_scorer.compute(item);

    let storedItem: Record<string, unknown>;
    let tier: "active" | "cold";
    let stored: boolean;
    let reason: string;

    if (salience >= this.threshold) {
      storedItem = this.active_memory.store(item);
      tier = "active";
      stored = true;
      reason = `High salience (${salience.toFixed(2)} >= ${this.threshold})`;
    } else {
      storedItem = this.cold_storage.archive(item);
      tier = "cold";
      stored = true;
      reason = `Low salience (${salience.toFixed(2)} < ${this.threshold})`;
    }

    this.version_chain.append(storedItem);

    return {
      stored,
      tier,
      salience_score: salience,
      reason,
      timestamp: new Date(),
    };
  }

  should_store(item: Record<string, unknown>): boolean {
    const salience = this.salience_scorer.compute(item);
    return salience >= this.threshold;
  }

  get_stats(): Record<string, unknown> {
    return {
      active_count: this.active_memory.count(),
      cold_count: this.cold_storage.count(),
      version_chain_length: this.version_chain.length,
      threshold: this.threshold,
    };
  }

  promote(item_id: string, target_tier: string = "active"): boolean {
    const coldItems = this.cold_storage.list_all();
    for (const item of coldItems) {
      if (
        item.id === item_id ||
        String(item.content ?? "").startsWith(item_id)
      ) {
        this.active_memory.store(item);
        return true;
      }
    }
    return false;
  }
}
