// claw-mem v6.34.0 — InferenceEngine (TypeScript)
//
// Main orchestrator for knowledge inference operations.
// Coordinates retrieval, derivation, contradiction detection, and visualization.
//
// Licensed under the Apache License, Version 2.0

import * as crypto from "crypto";
import {
  InferenceStep,
  InferenceStepType,
  InferenceChain,
  DerivedKnowledge,
  DeriveOptions,
  DEFAULT_DERIVE_OPTIONS,
  DeriveResult,
  ContradictionOptions,
  DEFAULT_CONTRADICTION_OPTIONS,
  ContradictionReport,
  ChainOutput,
  DerivationType,
  ContradictionType,
  ContradictionSeverity,
} from "./types.js";
import { KnowledgeDeriver } from "./knowledge-deriver.js";
import { ContradictionDetector } from "./contradiction-detector.js";
import { ChainVisualizer } from "./chain-visualizer.js";

/** Memory identifier type */
export type MemoryId = string;

/** Memory entry for inference */
export interface MemoryForInference {
  id: MemoryId;
  content: string;
  metadata?: Record<string, unknown>;
  timestamp?: number;
  confidence?: number;
}

/** InferenceEngine constructor options */
export interface InferenceEngineOptions {
  /** Enable result caching (default: true) */
  enableCache?: boolean;
  /** Cache TTL in milliseconds (default: 3600000) */
  cacheTtlMs?: number;
  /** Search function for retrieving memories */
  searchFn?: (query: string, limit: number) => MemoryForInference[];
}

/** Cached derivation result */
interface CachedDerivation {
  result: DeriveResult;
  timestamp: number;
  ttl: number;
}

/** InferenceEngine statistics */
export interface InferenceEngineStats {
  totalDerivations: number;
  totalContradictionChecks: number;
  cacheHits: number;
  cacheMisses: number;
  avgDerivationTimeMs: number;
  totalKnowledgeItems: number;
  totalContradictions: number;
}

/**
 * InferenceEngine — orchestrates knowledge inference operations.
 *
 * Usage:
 *   const engine = new InferenceEngine({ searchFn: mySearchFn });
 *   const result = await engine.derive("User preferences");
 */
export class InferenceEngine {
  private options: Required<InferenceEngineOptions>;
  private knowledgeDeriver: KnowledgeDeriver;
  private contradictionDetector: ContradictionDetector;
  private chainVisualizer: ChainVisualizer;
  private derivationCache: Map<string, CachedDerivation> = new Map();
  private stats: InferenceEngineStats = {
    totalDerivations: 0,
    totalContradictionChecks: 0,
    cacheHits: 0,
    cacheMisses: 0,
    avgDerivationTimeMs: 0,
    totalKnowledgeItems: 0,
    totalContradictions: 0,
  };
  private totalDerivationTime = 0;

  constructor(options?: InferenceEngineOptions) {
    this.options = {
      enableCache: options?.enableCache ?? true,
      cacheTtlMs: options?.cacheTtlMs ?? 3600000,
      searchFn: options?.searchFn ?? (() => []),
    };
    this.knowledgeDeriver = new KnowledgeDeriver();
    this.contradictionDetector = new ContradictionDetector();
    this.chainVisualizer = new ChainVisualizer();
  }

  /**
   * Derive new knowledge from memories.
   */
  async derive(query: string, options?: DeriveOptions): Promise<DeriveResult> {
    const startTime = Date.now();
    const opts = { ...DEFAULT_DERIVE_OPTIONS, ...options };

    // Check cache
    if (this.options.enableCache && opts.useCache) {
      const cacheKey = this.generateCacheKey(query, opts);
      const cached = this.getFromCache(cacheKey);
      if (cached) {
        return cached;
      }
    }

    // Retrieve memories
    const memories = this.retrieveMemories(query, opts.maxMemories);

    // Build inference chain
    const chainId = crypto.randomUUID();
    const steps: InferenceStep[] = [];
    const derivedKnowledge: DerivedKnowledge[] = [];

    // Add query as first step
    steps.push({
      stepId: crypto.randomUUID(),
      type: InferenceStepType.PREMISE,
      content: `Query: ${query}`,
      memories: [],
      confidence: 1.0,
      timestamp: Date.now(),
    });

    // Apply derivation rules (MVP: only transitive)
    for (const derivationType of opts.derivationTypes) {
      if (derivationType === DerivationType.TRANSITIVE) {
        const transitiveResult = this.knowledgeDeriver.deriveTransitive(memories);

        for (const k of transitiveResult.knowledge) {
          k.chainId = chainId;
          derivedKnowledge.push(k);
        }

        steps.push(...transitiveResult.steps);
      }
    }

    // Filter by confidence threshold
    const filteredKnowledge = derivedKnowledge.filter(
      (k) => k.confidence >= opts.confidenceThreshold
    );

    // Calculate overall confidence
    const confidence = this.calculateConfidence(filteredKnowledge);

    // Build chain
    const chain: InferenceChain = {
      chainId,
      query,
      steps,
      result: filteredKnowledge,
      confidence,
      timestamp: Date.now(),
      version: "1.0.0",
    };

    // Calculate processing time
    const processingTimeMs = Date.now() - startTime;

    // Build result
    const result: DeriveResult = {
      knowledge: filteredKnowledge,
      chain,
      confidence,
      cacheHit: false,
      processingTimeMs,
    };

    // Add visualization if requested
    if (opts.visualize) {
      result.visualization = this.chainVisualizer.render(chain, {
        formats: opts.visualizationFormats ?? ["text", "json"],
        showConfidence: true,
      });
    }

    // Cache result
    if (this.options.enableCache && opts.useCache) {
      const cacheKey = this.generateCacheKey(query, opts);
      this.addToCache(cacheKey, result);
    }

    // Update stats
    this.stats.totalDerivations++;
    this.totalDerivationTime += processingTimeMs;
    this.stats.avgDerivationTimeMs = this.totalDerivationTime / this.stats.totalDerivations;
    this.stats.totalKnowledgeItems += filteredKnowledge.length;

    return result;
  }

  /**
   * Detect contradictions in memories.
   */
  async detectContradictions(
    memories: MemoryForInference[],
    options?: ContradictionOptions
  ): Promise<ContradictionReport[]> {
    const startTime = Date.now();
    const opts = { ...DEFAULT_CONTRADICTION_OPTIONS, ...options };

    const reports: ContradictionReport[] = [];

    // MVP: Only direct contradiction detection
    if (opts.types.includes(ContradictionType.DIRECT)) {
      const directReports = this.contradictionDetector.detectDirect(memories);
      reports.push(...directReports);
    }

    // Filter by confidence
    const filtered = reports
      .filter((r) => r.confidence >= opts.minConfidence)
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, opts.maxResults);

    // Add suggestions if requested
    if (opts.includeSuggestions) {
      for (const report of filtered) {
        report.suggestions = this.contradictionDetector.generateSuggestions(report);
      }
    }

    // Update stats
    this.stats.totalContradictionChecks++;
    this.stats.totalContradictions += filtered.length;

    return filtered;
  }

  /**
   * Get inference chain by ID.
   * Note: In MVP, chains are not persisted. Returns null.
   */
  async getChain(_chainId: string): Promise<InferenceChain | null> {
    // MVP: No chain persistence
    return null;
  }

  /**
   * Get engine statistics.
   */
  getStats(): InferenceEngineStats {
    return { ...this.stats };
  }

  /**
   * Clear cache.
   */
  clearCache(): void {
    this.derivationCache.clear();
  }

  // ── Private Methods ─────────────────────────────────────────────────────

  private retrieveMemories(query: string, limit: number): MemoryForInference[] {
    if (this.options.searchFn) {
      return this.options.searchFn(query, limit);
    }
    return [];
  }

  private generateCacheKey(query: string, options: DeriveOptions): string {
    const types = (options.derivationTypes ?? []).sort().join(",");
    return `${query}:${types}:${options.maxSteps}:${options.confidenceThreshold}`;
  }

  private getFromCache(key: string): DeriveResult | null {
    const cached = this.derivationCache.get(key);
    if (!cached) {
      this.stats.cacheMisses++;
      return null;
    }

    if (Date.now() - cached.timestamp > cached.ttl) {
      this.derivationCache.delete(key);
      this.stats.cacheMisses++;
      return null;
    }

    this.stats.cacheHits++;
    return cached.result;
  }

  private addToCache(key: string, result: DeriveResult): void {
    this.derivationCache.set(key, {
      result,
      timestamp: Date.now(),
      ttl: this.options.cacheTtlMs,
    });

    // Evict old entries if cache is too large
    if (this.derivationCache.size > 1000) {
      this.evictOldestEntries(100);
    }
  }

  private evictOldestEntries(count: number): void {
    const entries = [...this.derivationCache.entries()]
      .sort((a, b) => a[1].timestamp - b[1].timestamp);

    for (let i = 0; i < Math.min(count, entries.length); i++) {
      this.derivationCache.delete(entries[i][0]);
    }
  }

  private calculateConfidence(knowledge: DerivedKnowledge[]): number {
    if (knowledge.length === 0) return 0;

    const sum = knowledge.reduce((acc, k) => acc + k.confidence, 0);
    return sum / knowledge.length;
  }
}
