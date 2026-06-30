// Strategy Registry - Storage strategy interface and registry (v6.31.0)

import type { MemoryRecord } from "../types.js";
import type { EpisodicStorage } from "./episodic.js";
import type { SemanticStorage } from "./semantic.js";
import type { ProceduralStorage } from "./procedural.js";
import type { EntityIndex } from "../entity/entity-index.js";
import type { VersionChain } from "./version-chain.js";

/** Strategy context passed to each strategy */
export interface StrategyContext {
  episodic: EpisodicStorage;
  semantic: SemanticStorage;
  procedural: ProceduralStorage;
  entityIndex: EntityIndex | null;
  versionChain: VersionChain;
  workspace: string;
}

/** Options for retrieval operations */
export interface RetrieveOptions {
  limit?: number;
  offset?: number;
  memoryType?: string;
}

/** Result of a store operation */
export interface StoreResult {
  id: string;
  strategy: string;
  version?: number;
  previousId?: string;
  overwritten?: boolean;
}

/** Strategy statistics */
export interface StrategyStats {
  name: string;
  memoryCount: number;
  lastUpdated?: string;
}

/** Storage strategy interface */
export interface StorageStrategy {
  /** Unique strategy name */
  readonly name: string;
  /** Supported memory types */
  readonly memoryTypes: string[];
  /** Store a memory record */
  store(record: MemoryRecord, context: StrategyContext): StoreResult;
  /** Retrieve memories by query */
  retrieve(query: string, options?: RetrieveOptions, context?: StrategyContext): MemoryRecord[];
  /** Get strategy-specific stats */
  getStats?(context: StrategyContext): StrategyStats;
}

/** Strategy registry - maps memory types to strategies */
export class StrategyRegistry {
  private strategies: Map<string, StorageStrategy> = new Map();
  private defaultStrategy: StorageStrategy;

  constructor(defaultStrategy: StorageStrategy) {
    this.defaultStrategy = defaultStrategy;
  }

  /** Register a strategy for specific memory types */
  register(strategy: StorageStrategy): void {
    for (const type of strategy.memoryTypes) {
      this.strategies.set(type, strategy);
    }
  }

  /** Resolve strategy for a memory type */
  resolve(memoryType: string): StorageStrategy {
    return this.strategies.get(memoryType) ?? this.defaultStrategy;
  }

  /** List all registered strategies */
  list(): Array<{ name: string; memoryTypes: string[] }> {
    const seen = new Set<string>();
    const result: Array<{ name: string; memoryTypes: string[] }> = [];

    for (const [, strategy] of this.strategies) {
      if (!seen.has(strategy.name)) {
        seen.add(strategy.name);
        result.push({
          name: strategy.name,
          memoryTypes: strategy.memoryTypes,
        });
      }
    }

    // Add default strategy
    if (!seen.has(this.defaultStrategy.name)) {
      result.push({
        name: this.defaultStrategy.name,
        memoryTypes: this.defaultStrategy.memoryTypes,
      });
    }

    return result;
  }

  /** Check if a memory type has a custom strategy */
  hasStrategy(memoryType: string): boolean {
    return this.strategies.has(memoryType);
  }

  /** List all registered memory types */
  listTypes(): string[] {
    return [...this.strategies.keys()];
  }
}
