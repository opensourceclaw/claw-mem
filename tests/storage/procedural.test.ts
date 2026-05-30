import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { ProceduralStorage } from "../../src/storage/procedural";

describe("ProceduralStorage", () => {
  let tmpDir: string;
  let storage: ProceduralStorage;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-ts-"));
    storage = new ProceduralStorage(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("should create skills directory on init", () => {
    expect(fs.existsSync(path.join(tmpDir, "memory", "skills"))).toBe(true);
  });

  it("should store and retrieve by skill name", () => {
    storage.store({
      content: "Use JWT for authentication",
      tags: ["auth", "procedural"],
      timestamp: "2026-05-29T10:00:00",
    });
    const entries = storage.getSkill("auth");
    expect(entries.length).toBe(1);
    expect(entries[0].content).toBe("Use JWT for authentication");
  });

  it("should use 'general' when no specific tag", () => {
    storage.store({
      content: "Generic skill",
      tags: ["procedural", "skill"],
      timestamp: "",
    });
    const entries = storage.getSkill("general");
    expect(entries.length).toBe(1);
  });

  it("should get all skills", () => {
    storage.store({ content: "Auth pattern", tags: ["auth"], timestamp: "" });
    storage.store({ content: "Docker pattern", tags: ["docker"], timestamp: "" });
    const all = storage.getAll();
    expect(all.length).toBe(2);
  });

  it("should search by keyword", () => {
    storage.store({ content: "JWT authentication setup", tags: ["auth"], timestamp: "" });
    storage.store({ content: "Docker container steps", tags: ["docker"], timestamp: "" });
    const results = storage.searchByKeyword("JWT");
    expect(results.length).toBe(1);
    expect(results[0].tags).toContain("auth");
  });

  it("should count correctly", () => {
    storage.store({ content: "Skill A", tags: ["deploy"], timestamp: "" });
    storage.store({ content: "Skill B", tags: ["test"], timestamp: "" });
    expect(storage.count()).toBe(2);
  });

  it("should return empty for unknown skill name", () => {
    expect(storage.getSkill("nonexistent").length).toBe(0);
  });
});
