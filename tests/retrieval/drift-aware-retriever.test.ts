// Tests for DriftAwareRetriever — claw-mem v6.3.0

import { describe, it, expect, beforeEach } from "vitest";
import {
  DriftAwareRetriever,
  DEFAULT_WEIGHT_CONFIG,
  DEFAULT_DRIFT_AWARE_CONFIG,
  type DriftDetectorLike,
  type DriftAwareResult,
} from "../../src/retrieval/drift-aware-retriever";
import type { RetrievalResult } from "../../src/retrieval/base";

function makeResult(id: string, score: number, meta?: Record<string, unknown>): RetrievalResult {
  return {
    id,
    content: `memory ${id}`,
    score,
    source: "semantic",
    metadata: meta ?? {},
  };
}

function makeMockDetector(driftScore = 0): DriftDetectorLike {
  return {
    getDriftScore: () => driftScore,
  };
}

describe("DriftAwareRetriever", () => {
  let retriever: DriftAwareRetriever;

  beforeEach(() => {
    retriever = new DriftAwareRetriever();
  });

  describe("constructor", () => {
    it("should create with default config", () => {
      expect(retriever.getMode()).toBe("auto");
      expect(retriever.getDriftScore()).toBe(0);
    });

    it("should create with drift detector", () => {
      const detector = makeMockDetector(0.5);
      const r = new DriftAwareRetriever(detector);
      expect(r.getDriftScore()).toBe(0.5);
    });
  });

  describe("adjustWeights", () => {
    it("should return normal weights for zero drift", () => {
      const w = retriever.adjustWeights(0);
      expect(w).toEqual(DEFAULT_WEIGHT_CONFIG.normal);
    });

    it("should return high drift weights for score >= 0.7", () => {
      const w = retriever.adjustWeights(0.8);
      expect(w).toEqual(DEFAULT_WEIGHT_CONFIG.highDrift);
      expect(w.recency).toBeGreaterThan(1.0);
      expect(w.frequency).toBeLessThan(1.0);
    });

    it("should blend weights for elevated drift (0.4-0.7)", () => {
      const w = retriever.adjustWeights(0.55);
      expect(w.recency).toBeGreaterThan(DEFAULT_WEIGHT_CONFIG.normal.recency);
      expect(w.recency).toBeLessThan(DEFAULT_WEIGHT_CONFIG.highDrift.recency);
    });
  });

  describe("retrieve", () => {
    it("should boost recency-weighted results on high drift", () => {
      const detector = makeMockDetector(0.8);
      const r = new DriftAwareRetriever(detector);
      const results = [
        makeResult("1", 0.5, { recency_score: 0.8, importance_score: 0.3, frequency_score: 0.3, relevance_score: 0.3 }),
        makeResult("2", 0.5, { recency_score: 0.2, importance_score: 0.3, frequency_score: 0.3, relevance_score: 0.3 }),
      ];

      const adjusted = r.retrieve("test", results);

      expect(adjusted[0].driftAdjustedScore).toBeGreaterThan(adjusted[1].driftAdjustedScore);
      expect(adjusted[0].driftLevel).toBe("high");
    });

    it("should preserve original ordering for normal drift", () => {
      const results = [
        makeResult("1", 0.8),
        makeResult("2", 0.3),
      ];

      const adjusted = retriever.retrieve("test", results);
      expect(adjusted[0].originalScore).toBeGreaterThan(adjusted[1].originalScore);
      expect(adjusted[0].driftLevel).toBe("normal");
    });

    it("should annotate results with drift metadata", () => {
      const results = [makeResult("1", 0.5)];

      const adjusted = retriever.retrieve("test", results);

      expect(adjusted[0].driftAdjustedScore).toBeDefined();
      expect(adjusted[0].originalScore).toBe(0.5);
      expect(adjusted[0].driftLevel).toBeDefined();
    });
  });

  describe("setMode / getMode", () => {
    it("should switch between auto and manual", () => {
      expect(retriever.getMode()).toBe("auto");
      retriever.setMode("manual");
      expect(retriever.getMode()).toBe("manual");
    });

    it("should use manual drift score in manual mode", () => {
      retriever.setMode("manual");
      const results = [makeResult("1", 0.5)];
      const adjusted = retriever.retrieve("test", results, { manualScore: 0.9 });
      expect(adjusted[0].driftLevel).toBe("high");
    });
  });

  describe("setDriftDetector", () => {
    it("should update drift detector", () => {
      const detector = makeMockDetector(0.6);
      retriever.setDriftDetector(detector);
      expect(retriever.getDriftScore()).toBe(0.6);
    });
  });

  describe("updateWeightConfig", () => {
    it("should partially update weight config", () => {
      retriever.updateWeightConfig({
        normal: { recency: 2.0 },
      });
      // Can't access private config directly, verify via adjustWeights
      const w = retriever.adjustWeights(0);
      expect(w.recency).toBe(2.0);
    });
  });

  describe("DEFAULT_WEIGHT_CONFIG", () => {
    it("should have highDrift.recency > normal.recency", () => {
      expect(DEFAULT_WEIGHT_CONFIG.highDrift.recency).toBeGreaterThan(
        DEFAULT_WEIGHT_CONFIG.normal.recency
      );
    });

    it("should have highDrift.frequency < normal.frequency", () => {
      expect(DEFAULT_WEIGHT_CONFIG.highDrift.frequency).toBeLessThan(
        DEFAULT_WEIGHT_CONFIG.normal.frequency
      );
    });
  });

  describe("DEFAULT_DRIFT_AWARE_CONFIG", () => {
    it("should default to auto mode", () => {
      expect(DEFAULT_DRIFT_AWARE_CONFIG.mode).toBe("auto");
    });
  });
});
