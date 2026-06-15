import { describe, it, expect } from "vitest";
import * as fs from "fs";
import * as path from "path";
import { CheckpointManager } from "../../src/session/checkpoint_manager.js";
import type { SessionMessage } from "../../src/session/types.js";

function makeMessages(count: number): SessionMessage[] {
  const msgs: SessionMessage[] = [];
  for (let i = 0; i < count; i++) {
    msgs.push({
      role: i % 2 === 0 ? "user" : "assistant",
      content: `Message ${i}`,
      timestamp: new Date().toISOString(),
    });
  }
  return msgs;
}

describe("CheckpointManager", () => {
  describe("create", () => {
    it("should create a checkpoint with correct structure", () => {
      const mgr = new CheckpointManager();
      const messages = makeMessages(3);
      const cp = mgr.create("sess_001", { messages });

      expect(cp.checkpointId).toContain("sess_001");
      expect(cp.sessionId).toBe("sess_001");
      expect(cp.status).toBe("created");
      expect(cp.messages).toHaveLength(3);
      expect(cp.metadata.messageCount).toBe(3);
    });

    it("should throw on empty sessionId", () => {
      const mgr = new CheckpointManager();
      expect(() => mgr.create("", {})).toThrow(TypeError);
    });
  });

  describe("listCheckpoints", () => {
    it("should list checkpoints filtered by session", () => {
      const mgr = new CheckpointManager();
      mgr.create("sess_001", { messages: makeMessages(2) });
      mgr.create("sess_001", { messages: makeMessages(3) });
      mgr.create("sess_002", { messages: makeMessages(1) });

      const sess1 = mgr.listCheckpoints("sess_001");
      expect(sess1).toHaveLength(2);

      const all = mgr.listCheckpoints();
      expect(all).toHaveLength(3);
    });
  });

  describe("FIFO eviction", () => {
    it("should evict oldest checkpoints when over maxCheckpoints", () => {
      const mgr = new CheckpointManager({ maxCheckpoints: 2 });
      mgr.create("sess_001", { messages: makeMessages(1) });
      mgr.create("sess_001", { messages: makeMessages(2) });
      mgr.create("sess_001", { messages: makeMessages(3) });

      const list = mgr.listCheckpoints("sess_001");
      expect(list).toHaveLength(2);
      expect(list[0].metadata.messageCount).toBe(2);
      expect(list[1].metadata.messageCount).toBe(3);
    });
  });

  describe("save/restore", () => {
    it("should save checkpoint to disk and restore it", () => {
      const tmpDir = fs.mkdtempSync("cp-test-");
      const mgr = new CheckpointManager({ storageDir: tmpDir });

      const cp = mgr.create("sess_001", { messages: makeMessages(2) });
      const saved = mgr.save("sess_001");
      expect(saved).toBe(true);

      // Restore by checkpointId from disk
      const restored = mgr.restore(cp.checkpointId);
      expect(restored).not.toBeNull();
      expect(restored!.status).toBe("restored");
      expect(restored!.sessionId).toBe("sess_001");

      // Clean up
      fs.rmSync(tmpDir, { recursive: true, force: true });
    });
  });

  describe("rollback", () => {
    it("should rollback to a specific checkpoint", () => {
      const mgr = new CheckpointManager();
      mgr.create("sess_001", { messages: makeMessages(2) });
      const cp2 = mgr.create("sess_001", { messages: makeMessages(5) });
      mgr.create("sess_001", { messages: makeMessages(10) });

      const result = mgr.rollback(cp2.checkpointId);
      expect(result).toBe(true);

      const list = mgr.listCheckpoints("sess_001");
      expect(list).toHaveLength(2);
    });
  });

  describe("cleanup", () => {
    it("should keep recent checkpoints with large maxAgeHours", () => {
      const mgr = new CheckpointManager();
      mgr.create("sess_001", { messages: makeMessages(2) });
      mgr.create("sess_002", { messages: makeMessages(3) });

      // 100 hours = keep everything created in the last 100 hours
      const removed = mgr.cleanup(100);
      expect(removed).toBe(0);
      expect(mgr.listCheckpoints()).toHaveLength(2);
    });
  });
});
