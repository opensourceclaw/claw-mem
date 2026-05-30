import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { SemanticStorage } from "../../src/storage/semantic";

describe("SemanticStorage", () => {
  let tmpDir: string;
  let storage: SemanticStorage;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-ts-"));
    storage = new SemanticStorage(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("should create MEMORY.md on init", () => {
    expect(fs.existsSync(path.join(tmpDir, "MEMORY.md"))).toBe(true);
  });

  it("should store and retrieve semantic memory", () => {
    storage.store({
      content: "User prefers Python",
      tags: ["preference"],
      timestamp: "2026-05-29T10:00:00",
      id: "abc12345",
    });
    const all = storage.getAll();
    expect(all.length).toBe(1);
    expect(all[0].id).toBe("abc12345");
    expect(all[0].content).toBe("User prefers Python");
    expect(all[0].tags).toContain("preference");
  });

  it("should auto-generate IDs when not provided", () => {
    storage.store({ content: "No ID provided", tags: [], timestamp: "" });
    const all = storage.getAll();
    expect(all[0].id).toBeTruthy();
    expect(all[0].id!.length).toBe(8);
  });

  it("should search by tag", () => {
    storage.store({ content: "Python is great", tags: ["python", "tech"], timestamp: "", id: "1" });
    storage.store({ content: "FastAPI is fast", tags: ["python", "web"], timestamp: "", id: "2" });
    storage.store({ content: "Docker basics", tags: ["devops"], timestamp: "", id: "3" });
    const result = storage.searchByTag("python");
    expect(result.length).toBe(2);
  });

  it("should update memory content by ID", () => {
    storage.store({ content: "Old content", tags: [], timestamp: "", id: "mem-001" });
    const updated = storage.update("mem-001", "New content");
    expect(updated).toBe(true);
    const all = storage.getAll();
    expect(all[0].content).toBe("New content");
  });

  it("should return false when updating non-existent ID", () => {
    expect(storage.update("nope", "whatever")).toBe(false);
  });

  it("should count correctly", () => {
    expect(storage.count()).toBe(0);
    storage.store({ content: "One", tags: [], timestamp: "" });
    storage.store({ content: "Two", tags: [], timestamp: "" });
    expect(storage.count()).toBe(2);
  });
});
