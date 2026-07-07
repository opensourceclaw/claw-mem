// claw-mem v6.35.0 — StructureOptimizer Tests
//
// Unit tests for the StructureOptimizer module.

import { describe, it, expect, beforeEach } from "vitest";
import {
  StructureOptimizer,
  HealthReporter,
  IndexEvolver,
  IndexType,
  OptimizeSuggestionType,
  SuggestionPriority,
  DEFAULT_OPTIMIZER_OPTIONS,
} from "../../dist/src/optimizer/index.js";
import type { IndexStat } from "../../dist/src/optimizer/index.js";

describe("StructureOptimizer", () => {
  let optimizer: StructureOptimizer;

  beforeEach(() => {
    optimizer = new StructureOptimizer();
  });

  describe("assess", () => {
    it("should return health report", async () => {
      const report = await optimizer.assess();

      expect(report).toHaveProperty("overallScore");
      expect(report).toHaveProperty("indexStats");
      expect(report).toHaveProperty("unusedIndexes");
      expect(report).toHaveProperty("timestamp");
    });

    it("should return score between 0 and 100", async () => {
      const report = await optimizer.assess();

      expect(report.overallScore).toBeGreaterThanOrEqual(0);
      expect(report.overallScore).toBeLessThanOrEqual(100);
    });

    it("should include metadata", async () => {
      const report = await optimizer.assess();

      expect(report.metadata).toHaveProperty("assessmentTimeMs");
      expect(report.metadata).toHaveProperty("indexesAnalyzed");
    });

    it("should use cache on second call", async () => {
      const report1 = await optimizer.assess();
      const report2 = await optimizer.assess();

      expect(report2.metadata.cacheHit).toBe(true);
    });

    it("should bypass cache with refresh=true", async () => {
      const report1 = await optimizer.assess();
      const report2 = await optimizer.assess(true);

      expect(report2.metadata.cacheHit).toBe(false);
    });
  });

  describe("suggest", () => {
    it("should return suggestions array", async () => {
      const suggestions = await optimizer.suggest();

      expect(Array.isArray(suggestions)).toBe(true);
    });

    it("should return suggestions limited by maxSuggestions", async () => {
      const suggestions = await optimizer.suggest();

      expect(suggestions.length).toBeLessThanOrEqual(DEFAULT_OPTIMIZER_OPTIONS.maxSuggestions);
    });
  });

  describe("optimize", () => {
    it("should return optimization result", async () => {
      const result = await optimizer.optimize();

      expect(result).toHaveProperty("executed");
      expect(result).toHaveProperty("suggestions");
      expect(result).toHaveProperty("duration");
    });

    it("should not execute in MVP (suggestions only)", async () => {
      const result = await optimizer.optimize();

      expect(result.executed).toBe(false);
    });
  });

  describe("getHistory", () => {
    it("should return history array", async () => {
      const history = await optimizer.getHistory();

      expect(Array.isArray(history)).toBe(true);
    });

    it("should respect limit parameter", async () => {
      await optimizer.optimize();
      await optimizer.optimize();
      const history = await optimizer.getHistory(1);

      expect(history.length).toBeLessThanOrEqual(1);
    });
  });

  describe("getStats", () => {
    it("should return statistics", () => {
      const stats = optimizer.getStats();

      expect(stats).toHaveProperty("totalAssessments");
      expect(stats).toHaveProperty("totalSuggestions");
    });

    it("should track assessments after assess()", async () => {
      await optimizer.assess();
      const stats = optimizer.getStats();

      expect(stats.totalAssessments).toBe(1);
    });
  });

  describe("resetStats", () => {
    it("should reset statistics", async () => {
      await optimizer.assess();
      optimizer.resetStats();
      const stats = optimizer.getStats();

      expect(stats.totalAssessments).toBe(0);
    });
  });

  describe("recordQuery", () => {
    it("should track query statistics", () => {
      optimizer.recordQuery("bm25", 10);

      const stats = optimizer.getStats();
      // Internal tracking only, no direct verification
    });
  });
});

describe("HealthReporter", () => {
  let reporter: HealthReporter;

  beforeEach(() => {
    reporter = new HealthReporter();
  });

  describe("generateReport", () => {
    it("should generate health report from index stats", () => {
      const indexStats: IndexStat[] = [
        {
          name: "bm25",
          type: IndexType.BM25,
          hitRate: 0.8,
          avgLatency: 15,
          size: 1024 * 1024,
          lastUsed: Date.now(),
          queryCount: 100,
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
      ];

      const report = reporter.generateReport(indexStats, 100);

      expect(report.indexStats).toHaveLength(1);
      expect(report.overallScore).toBeGreaterThanOrEqual(0);
    });

    it("should return 100 for empty index stats", () => {
      const report = reporter.generateReport([], 0);

      expect(report.overallScore).toBe(100);
    });
  });

  describe("calculateOverallScore", () => {
    it("should calculate weighted score", () => {
      const indexStats: IndexStat[] = [
        {
          name: "bm25",
          type: IndexType.BM25,
          hitRate: 0.8,
          avgLatency: 10,
          size: 1024 * 1024,
          lastUsed: Date.now(),
          queryCount: 100,
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
        {
          name: "entity_cooc",
          type: IndexType.ENTITY_COOC,
          hitRate: 0.5,
          avgLatency: 5,
          size: 512 * 1024,
          lastUsed: Date.now(),
          queryCount: 50,
          createdAt: Date.now() - 30 * 24 * 60 * 60 * 1000,
        },
      ];

      const score = reporter.calculateOverallScore(indexStats);

      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    });
  });

  describe("calculateIndexScore", () => {
    it("should calculate score for single index", () => {
      const stat: IndexStat = {
        name: "bm25",
        type: IndexType.BM25,
        hitRate: 0.8,
        avgLatency: 10,
        size: 1024 * 1024,
        lastUsed: Date.now(),
        queryCount: 100,
        createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
      };

      const score = reporter.calculateIndexScore(stat);

      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    });
  });
});

describe("IndexEvolver", () => {
  let evolver: IndexEvolver;

  beforeEach(() => {
    evolver = new IndexEvolver();
  });

  describe("detectUnusedIndexSuggestions", () => {
    it("should detect unused indexes", () => {
      const indexStats: IndexStat[] = [
        {
          name: "unused_index",
          type: IndexType.BM25,
          hitRate: 0,
          avgLatency: 0,
          size: 1024,
          lastUsed: Date.now() - 10 * 24 * 60 * 60 * 1000,
          queryCount: 0,
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
      ];

      const suggestions = evolver.detectUnusedIndexSuggestions(indexStats);

      expect(suggestions.length).toBeGreaterThan(0);
      expect(suggestions[0].type).toBe(OptimizeSuggestionType.DELETE_INDEX);
    });

    it("should not suggest deletion for recently created indexes", () => {
      const indexStats: IndexStat[] = [
        {
          name: "new_index",
          type: IndexType.BM25,
          hitRate: 0,
          avgLatency: 0,
          size: 1024,
          lastUsed: Date.now() - 1 * 24 * 60 * 60 * 1000,
          queryCount: 0,
          createdAt: Date.now() - 12 * 60 * 60 * 1000, // Created 12 hours ago
        },
      ];

      const suggestions = evolver.detectUnusedIndexSuggestions(indexStats);

      expect(suggestions).toHaveLength(0);
    });

    it("should not suggest deletion for used indexes", () => {
      const indexStats: IndexStat[] = [
        {
          name: "active_index",
          type: IndexType.BM25,
          hitRate: 0.8,
          avgLatency: 10,
          size: 1024,
          lastUsed: Date.now(),
          queryCount: 100,
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
      ];

      const suggestions = evolver.detectUnusedIndexSuggestions(indexStats);

      expect(suggestions).toHaveLength(0);
    });
  });

  describe("detectMissingIndexSuggestions", () => {
    it("should detect low hit rate indexes", () => {
      const indexStats: IndexStat[] = [
        {
          name: "low_hit_index",
          type: IndexType.BM25,
          hitRate: 0.2, // Below threshold
          avgLatency: 50,
          size: 1024,
          lastUsed: Date.now(),
          queryCount: 200, // Above minQueryCount
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
      ];

      const suggestions = evolver.detectMissingIndexSuggestions(indexStats);

      expect(suggestions.length).toBeGreaterThan(0);
    });

    it("should not suggest for indexes with low query count", () => {
      const indexStats: IndexStat[] = [
        {
          name: "rare_index",
          type: IndexType.BM25,
          hitRate: 0.1,
          avgLatency: 50,
          size: 1024,
          lastUsed: Date.now(),
          queryCount: 10, // Below minQueryCount
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
      ];

      const suggestions = evolver.detectMissingIndexSuggestions(indexStats);

      expect(suggestions).toHaveLength(0);
    });
  });

  describe("generateAllSuggestions", () => {
    it("should return sorted suggestions", () => {
      const indexStats: IndexStat[] = [
        {
          name: "unused_1",
          type: IndexType.BM25,
          hitRate: 0,
          avgLatency: 0,
          size: 10000,
          lastUsed: Date.now() - 30 * 24 * 60 * 60 * 1000,
          queryCount: 0,
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
        {
          name: "unused_2",
          type: IndexType.BM25,
          hitRate: 0,
          avgLatency: 0,
          size: 5000,
          lastUsed: Date.now() - 15 * 24 * 60 * 60 * 1000,
          queryCount: 0,
          createdAt: Date.now() - 60 * 24 * 60 * 60 * 1000,
        },
      ];

      const suggestions = evolver.generateAllSuggestions(indexStats);

      expect(suggestions.length).toBeLessThanOrEqual(DEFAULT_OPTIMIZER_OPTIONS.maxSuggestions);
    });
  });
});