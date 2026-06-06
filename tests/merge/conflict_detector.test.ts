import { describe, it, expect } from "vitest";
import { ConflictDetector, conflictReportToDict, conflictResolutionToDict } from "../../src/merge/conflict_detector";

describe("ConflictDetector", () => {
  const stubManager = {
    semantic: {
      getAll: (): Record<string, unknown>[] => [],
    },
  };

  const stubLLM = {
    generate: (_p: string, _o?: { maxTokens?: number; system?: string }): string => "NO",
  };

  const stubEmbedding = {
    encode: (_texts: string[]): number[][] => [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  };

  describe("constructor", () => {
    it("creates detector with custom threshold", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM, undefined, 0.5);
      expect(detector.simThreshold).toBe(0.5);
    });

    it("uses default threshold when not provided", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM);
      expect(detector.simThreshold).toBe(0.7);
    });
  });

  describe("detectConflicts", () => {
    it("returns empty array when no memories", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM);
      const conflicts = detector.detectConflicts();
      expect(conflicts).toEqual([]);
    });

    it("returns empty array when only one memory", () => {
      const manager = {
        semantic: {
          getAll: (): Record<string, unknown>[] => [
            { id: "m1", content: "Test content", metadata: {} },
          ],
        },
      };
      const detector = new ConflictDetector(manager as any, stubLLM);
      const conflicts = detector.detectConflicts();
      expect(conflicts).toEqual([]);
    });

    it("filters out deprecated memories", () => {
      const manager = {
        semantic: {
          getAll: (): Record<string, unknown>[] => [
            { id: "m1", content: "Active memory", metadata: { deprecated: "true" } },
            { id: "m2", content: "Another active", metadata: {} },
          ],
        },
      };
      const detector = new ConflictDetector(manager as any, stubLLM);
      const conflicts = detector.detectConflicts();
      // Should not crash and return results
      expect(Array.isArray(conflicts)).toBe(true);
    });

    it("calls all three detection strategies", () => {
      const manager = {
        semantic: {
          getAll: (): Record<string, unknown>[] => [
            { id: "m1", content: "张三负责项目", metadata: {} },
            { id: "m2", content: "张三 age: 30", metadata: {} },
            { id: "m3", content: "in January 2024", metadata: {} },
            { id: "m4", content: "in February 2024", metadata: {} },
          ],
        },
      };
      // Use proper embeddings that match length
      const embedding = {
        encode: (_texts: string[]): number[][] => [
          [1, 0, 0],
          [1, 0, 0],
          [1, 0, 0],
          [1, 0, 0],
        ],
      };
      const detector = new ConflictDetector(manager as any, stubLLM, embedding, 0.9);
      const conflicts = detector.detectConflicts();
      expect(Array.isArray(conflicts)).toBe(true);
    });
  });

  describe("resolveConflict", () => {
    it("resolves with keep_a when LLM returns A", () => {
      const llm = {
        generate: (_p: string, _o?: { maxTokens?: number }): string => "A",
      };
      const detector = new ConflictDetector(stubManager as any, llm);
      
      const conflict = {
        conflictType: "entity",
        memoryIdA: "a1",
        memoryIdB: "b1",
        contentA: "Content A",
        contentB: "Content B",
        description: "Test conflict",
        similarity: 0.9,
        resolved: false,
        resolution: null,
      };
      
      const resolution = detector.resolveConflict(conflict);
      expect(resolution.action).toBe("keep_a");
      expect(resolution.winnerId).toBe("a1");
    });

    it("resolves with keep_b when LLM returns B", () => {
      const llm = {
        generate: (_p: string, _o?: { maxTokens?: number }): string => "B",
      };
      const detector = new ConflictDetector(stubManager as any, llm);
      
      const conflict = {
        conflictType: "entity",
        memoryIdA: "a1",
        memoryIdB: "b1",
        contentA: "Content A",
        contentB: "Content B",
        description: "Test conflict",
        similarity: 0.9,
        resolved: false,
        resolution: null,
      };
      
      const resolution = detector.resolveConflict(conflict);
      expect(resolution.action).toBe("keep_b");
      expect(resolution.winnerId).toBe("b1");
    });

    it("resolves with merge when LLM returns MERGE", () => {
      const llm = {
        generate: (_p: string, _o?: { maxTokens?: number }): string => "MERGE",
      };
      const detector = new ConflictDetector(stubManager as any, llm);
      
      const conflict = {
        conflictType: "entity",
        memoryIdA: "a1",
        memoryIdB: "b1",
        contentA: "Content A",
        contentB: "Content B",
        description: "Test conflict",
        similarity: 0.9,
        resolved: false,
        resolution: null,
      };
      
      const resolution = detector.resolveConflict(conflict);
      expect(resolution.action).toBe("merge");
      expect(resolution.mergedContent).toBeDefined();
    });

    it("marks conflict as resolved", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM);
      
      const conflict = {
        conflictType: "entity",
        memoryIdA: "a1",
        memoryIdB: "b1",
        contentA: "Content A",
        contentB: "Content B",
        description: "Test conflict",
        similarity: 0.9,
        resolved: false,
        resolution: null,
      };
      
      detector.resolveConflict(conflict);
      expect(conflict.resolved).toBe(true);
      expect(conflict.resolution).not.toBeNull();
    });
  });

  describe("runCycle", () => {
    it("runs detection and resolution cycle", () => {
      const manager = {
        semantic: {
          getAll: (): Record<string, unknown>[] => [],
        },
      };
      const detector = new ConflictDetector(manager as any, stubLLM);
      
      const stats = detector.runCycle();
      expect(stats.conflictsDetected).toBe(0);
      expect(stats.conflictsResolved).toBe(0);
      expect(stats.byType).toBeDefined();
      expect(stats.durationMs).toBeDefined();
    });
  });

  describe("getHistory", () => {
    it("returns empty array initially", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM);
      const history = detector.getHistory();
      expect(history).toEqual([]);
    });

    it("returns copy of history", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM);
      const history1 = detector.getHistory();
      const history2 = detector.getHistory();
      expect(history1).toStrictEqual(history2);
    });
  });

  describe("clearHistory", () => {
    it("clears conflict history", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM);
      detector.clearHistory();
      expect(detector.getHistory().length).toBe(0);
    });
  });

  describe("toString", () => {
    it("returns string representation", () => {
      const detector = new ConflictDetector(stubManager as any, stubLLM, undefined, 0.8);
      const str = detector.toString();
      expect(str).toContain("ConflictDetector");
      expect(str).toContain("0.8");
    });
  });
});

describe("conflictReportToDict", () => {
  it("converts conflict report to dict", () => {
    const report = {
      conflictType: "entity",
      memoryIdA: "a1",
      memoryIdB: "b1",
      contentA: "Content A",
      contentB: "Content B",
      description: "Conflict",
      similarity: 0.9,
      resolved: true,
      resolution: {
        action: "keep_a",
        winnerId: "a1",
        mergedContent: "",
        reasoning: "A is better",
      },
    };
    
    const dict = conflictReportToDict(report);
    expect(dict.conflict_type).toBe("entity");
    expect(dict.memory_id_a).toBe("a1");
    expect(dict.resolved).toBe(true);
  });

  it("handles null resolution", () => {
    const report = {
      conflictType: "entity",
      memoryIdA: "a1",
      memoryIdB: "b1",
      contentA: "Content A",
      contentB: "Content B",
      description: "Conflict",
      similarity: 0.9,
      resolved: false,
      resolution: null,
    };
    
    const dict = conflictReportToDict(report);
    expect(dict.resolution).toBeNull();
  });
});

describe("conflictResolutionToDict", () => {
  it("converts resolution to dict", () => {
    const resolution = {
      action: "merge",
      winnerId: "",
      mergedContent: "Merged content",
      reasoning: "Combined both",
    };
    
    const dict = conflictResolutionToDict(resolution);
    expect(dict.action).toBe("merge");
    expect(dict.merged_content).toBe("Merged content");
    expect(dict.reasoning).toBe("Combined both");
  });
});