import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { GroundTruthStore } from "../../src/storage/ground_truth";

describe("GroundTruthStore", () => {
  let tmpDir: string;
  let store: GroundTruthStore;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-ts-"));
    store = new GroundTruthStore(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("should create ground_truth directory on init", () => {
    expect(fs.existsSync(path.join(tmpDir, "ground_truth"))).toBe(true);
  });

  it("should store a turn and return record_id", () => {
    const id = store.storeTurn("sess-1", [{ role: "user", content: "Hello" }]);
    expect(id).toMatch(/^gt_[a-f0-9]{16}$/);
  });

  it("should retrieve session records", () => {
    store.storeTurn("sess-1", [{ role: "user", content: "First" }]);
    store.storeTurn("sess-1", [{ role: "assistant", content: "Second" }]);
    const session = store.getSession("sess-1");
    expect(session.length).toBe(2);
    expect(session[0].session_id).toBe("sess-1");
  });

  it("storeSession should delegate to storeTurn", () => {
    const msgs = [
      { role: "user", content: "Hi" },
      { role: "assistant", content: "Hello" },
    ];
    const id = store.storeSession("batch-1", msgs);
    expect(id).toMatch(/^gt_/);
    const session = store.getSession("batch-1");
    expect(session.length).toBe(1);
  });

  it("should search by keyword", () => {
    store.storeTurn("s1", [{ role: "user", content: "Python code" }]);
    store.storeTurn("s2", [{ role: "user", content: "JavaScript code" }]);
    const results = store.search(undefined, "python");
    expect(results.length).toBeGreaterThanOrEqual(1);
  });

  it("should search by session_id", () => {
    store.storeTurn("a", [{ role: "user", content: "Topic A" }]);
    store.storeTurn("b", [{ role: "user", content: "Topic B" }]);
    const results = store.search("a");
    expect(results.length).toBeGreaterThanOrEqual(1);
    expect(results[0].session_id).toBe("a");
  });

  it("should list sessions", () => {
    store.storeTurn("x", [{ role: "user", content: "X" }]);
    store.storeTurn("y", [{ role: "user", content: "Y" }]);
    const sessions = store.listSessions();
    expect(sessions.length).toBe(2);
    expect(sessions[0]).toHaveProperty("sessionId");
    expect(sessions[0]).toHaveProperty("fileSize");
  });

  it("should count records", () => {
    store.storeTurn("c1", [{ role: "user", content: "A" }]);
    store.storeTurn("c1", [{ role: "user", content: "B" }]);
    store.storeTurn("c2", [{ role: "user", content: "C" }]);
    expect(store.countRecords()).toBe(3);
  });

  it("should return empty session for unknown id", () => {
    expect(store.getSession("nope").length).toBe(0);
  });
});
