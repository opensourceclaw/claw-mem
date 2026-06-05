import { describe, it, expect, beforeEach, afterEach } from "vitest";
import {
  DriftHistoryStore,
  DEFAULT_DRIFT_HISTORY_CONFIG,
  type DriftRecord,
} from "../src/drift-history-store";
import * as fs from "fs";
import * as path from "path";

const TEST_PATH = "/tmp/test-drift-history.json";

function cleanTestFile(): void {
  try { fs.unlinkSync(TEST_PATH); } catch { /* ok */ }
}

describe("DriftHistoryStore", () => {
  beforeEach(cleanTestFile);
  afterEach(cleanTestFile);

  function makeRecord(overrides: Partial<DriftRecord> = {}): DriftRecord {
    return {
      sessionId: "session-1",
      timestamp: Date.now(),
      driftScore: 0.5,
      topicShift: ["auth", "deploy"],
      alertLevel: "medium",
      ...overrides,
    };
  }

  describe("record()", () => {
    it("stores and retrieves drift records", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ driftScore: 0.3, topicShift: ["auth"] }));

      const history = store.getHistory("session-1");
      expect(history).toHaveLength(1);
      expect(history[0].driftScore).toBe(0.3);
      expect(history[0].topicShift).toContain("auth");
    });

    it("filters by sessionId", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ sessionId: "s1", driftScore: 0.3 }));
      store.record(makeRecord({ sessionId: "s2", driftScore: 0.7 }));

      expect(store.getHistory("s1")).toHaveLength(1);
      expect(store.getHistory("s2")).toHaveLength(1);
      expect(store.getHistory()).toHaveLength(2);
    });

    it("enforces maxRecords limit", () => {
      const store = new DriftHistoryStore({
        storagePath: TEST_PATH,
        maxRecords: 5,
      });

      for (let i = 0; i < 10; i++) {
        store.record(makeRecord({ driftScore: 0.1 * i }));
      }

      expect(store.size).toBeLessThanOrEqual(5);
      expect(store.getHistory()).toHaveLength(5);
    });

    it("persists to disk", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ driftScore: 0.42 }));
      store.save();

      expect(fs.existsSync(TEST_PATH)).toBe(true);
    });
  });

  describe("recordBatch()", () => {
    it("records multiple events at once", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.recordBatch([
        makeRecord({ sessionId: "s1", driftScore: 0.3 }),
        makeRecord({ sessionId: "s2", driftScore: 0.5 }),
        makeRecord({ sessionId: "s3", driftScore: 0.8 }),
      ]);

      expect(store.getHistory()).toHaveLength(3);
    });
  });

  describe("getHistoryInRange()", () => {
    it("filters by time range", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      const now = Date.now();

      store.record(makeRecord({ timestamp: now - 10000, driftScore: 0.3 }));
      store.record(makeRecord({ timestamp: now, driftScore: 0.7 }));
      store.record(makeRecord({ timestamp: now + 10000, driftScore: 0.5 }));

      const inRange = store.getHistoryInRange(now - 5000, now + 5000);
      expect(inRange).toHaveLength(1);
      expect(inRange[0].driftScore).toBe(0.7);
    });
  });

  describe("getAverageDrift()", () => {
    it("returns 0 for empty store", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      expect(store.getAverageDrift()).toBe(0);
    });

    it("calculates average correctly", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.recordBatch([
        makeRecord({ driftScore: 0.2 }),
        makeRecord({ driftScore: 0.4 }),
        makeRecord({ driftScore: 0.6 }),
      ]);
      // Average should be ~0.4
      expect(store.getAverageDrift()).toBeCloseTo(0.4, 1);
    });
  });

  describe("getAverageDriftForSession()", () => {
    it("returns 0 for unknown session", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      expect(store.getAverageDriftForSession("unknown")).toBe(0);
    });

    it("calculates per-session average", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ sessionId: "s1", driftScore: 0.5 }));
      store.record(makeRecord({ sessionId: "s1", driftScore: 0.7 }));

      expect(store.getAverageDriftForSession("s1")).toBeCloseTo(0.6, 1);
    });
  });

  describe("getDriftTrend()", () => {
    it("returns stable for few records", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ driftScore: 0.5 }));
      store.record(makeRecord({ driftScore: 0.5 }));

      const trend = store.getDriftTrend();
      expect(trend.direction).toBe("stable");
    });

    it("detects increasing trend", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      const now = Date.now();
      for (let i = 0; i < 6; i++) {
        store.record(makeRecord({
          timestamp: now + i * 1000,
          driftScore: 0.2 + i * 0.1,
        }));
      }

      const trend = store.getDriftTrend();
      expect(trend.direction).toBe("increasing");
    });

    it("detects decreasing trend", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      const now = Date.now();
      for (let i = 0; i < 6; i++) {
        store.record(makeRecord({
          timestamp: now + i * 1000,
          driftScore: 0.8 - i * 0.1,
        }));
      }

      const trend = store.getDriftTrend();
      expect(trend.direction).toBe("decreasing");
    });
  });

  describe("getSummary()", () => {
    it("returns comprehensive summary", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ sessionId: "s1", driftScore: 0.3 }));
      store.record(makeRecord({ sessionId: "s2", driftScore: 0.8 }));

      const summary = store.getSummary();
      expect(summary.totalRecords).toBe(2);
      expect(summary.maxDrift).toBe(0.8);
      expect(summary.minDrift).toBe(0.3);
      expect(summary.sessionCount).toBe(2);
      expect(summary.lastRecorded).not.toBeNull();
    });
  });

  describe("isDriftIncreasing()", () => {
    it("returns false when drift is low and stable", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord({ driftScore: 0.2 }));
      store.record(makeRecord({ driftScore: 0.3 }));

      expect(store.isDriftIncreasing()).toBe(false);
    });
  });

  describe("persistence", () => {
    it("loads records from disk", () => {
      const store1 = new DriftHistoryStore({ storagePath: TEST_PATH });
      store1.record(makeRecord({ driftScore: 0.42 }));
      store1.save();

      const store2 = new DriftHistoryStore({ storagePath: TEST_PATH });
      expect(store2.getHistory()).toHaveLength(1);
      expect(store2.getHistory()[0].driftScore).toBe(0.42);
    });

    it("handles missing file gracefully", () => {
      const store = new DriftHistoryStore({
        storagePath: "/tmp/nonexistent-drift-file.json",
      });
      expect(store.getHistory()).toHaveLength(0);
      expect(store.getAverageDrift()).toBe(0);
    });

    it("handles corrupted file gracefully", () => {
      fs.writeFileSync(TEST_PATH, "not valid json");
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      expect(store.getHistory()).toHaveLength(0);
    });
  });

  describe("clear()", () => {
    it("removes all records", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.record(makeRecord());
      store.clear();
      expect(store.size).toBe(0);
    });
  });

  describe("cleanup", () => {
    it("removes expired records based on retentionDays", () => {
      const store = new DriftHistoryStore({
        storagePath: TEST_PATH,
        retentionDays: 1,
      });

      const oldTimestamp = Date.now() - 2 * 24 * 60 * 60 * 1000; // 2 days ago
      store.record(makeRecord({ timestamp: oldTimestamp, driftScore: 0.9 }));
      store.record(makeRecord({ driftScore: 0.3 })); // current

      // Only the recent record should remain
      expect(store.getHistory()).toHaveLength(1);
      expect(store.getHistory()[0].driftScore).toBe(0.3);
    });
  });

  describe("config", () => {
    it("uses default config values", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      const config = store.getConfig();
      expect(config.maxRecords).toBe(1000);
      expect(config.retentionDays).toBe(30);
    });

    it("updates config at runtime", () => {
      const store = new DriftHistoryStore({ storagePath: TEST_PATH });
      store.updateConfig({ maxRecords: 500 });
      expect(store.getConfig().maxRecords).toBe(500);
    });
  });
});
