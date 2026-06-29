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

  // ── v6.27.2: Timestamp Format ───────────────────────────────────────

  describe("v6.27.2 timestamp format", () => {
    it("writes new format with trailing timestamp", () => {
      storage.store({
        content: "test memory content",
        tags: ["core"],
        timestamp: "2026-06-29T10:00:00.000Z",
        id: "test-001",
      });
      const file = fs.readFileSync(path.join(tmpDir, "MEMORY.md"), "utf-8");
      // Should have new format: content <!-- ts:timestamp -->
      expect(file).toMatch(/test memory content <!-- ts:2026-06-29T10:00:00\.000Z -->/);
      // Should NOT have old format: [timestamp] content
      expect(file).not.toMatch(/\n\[2026-06-29/);
    });

    it("reads old format with leading timestamp", () => {
      // Write old format directly
      const oldFormat = `# MEMORY.md

<!-- Core Memory - Permanent Storage -->

<!-- tags: legacy; id: old-001 -->
[2026-06-28T10:00:00.000Z] old memory content

`;
      fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), oldFormat, "utf-8");

      // Create new storage instance to read
      const newStorage = new SemanticStorage(tmpDir);
      const entries = newStorage.getAll();

      expect(entries.length).toBe(1);
      expect(entries[0].content).toBe("old memory content");
      expect(entries[0].timestamp).toBe("2026-06-28T10:00:00.000Z");
      expect(entries[0].tags).toContain("legacy");
      expect(entries[0].id).toBe("old-001");
    });

    it("reads mixed format file", () => {
      const mixed = `# MEMORY.md

<!-- Core Memory - Permanent Storage -->

<!-- tags: old; id: entry-1 -->
[2026-06-01T00:00:00.000Z] old format entry

<!-- tags: new; id: entry-2 -->
new format entry <!-- ts:2026-06-02T00:00:00.000Z -->

`;
      fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), mixed, "utf-8");

      const newStorage = new SemanticStorage(tmpDir);
      const entries = newStorage.getAll();

      expect(entries.length).toBe(2);
      expect(entries[0].content).toBe("old format entry");
      expect(entries[0].timestamp).toBe("2026-06-01T00:00:00.000Z");
      expect(entries[1].content).toBe("new format entry");
      expect(entries[1].timestamp).toBe("2026-06-02T00:00:00.000Z");
    });

    it("rewriteFile outputs new format", () => {
      // Store in old format
      const oldFormat = `# MEMORY.md

<!-- Core Memory - Permanent Storage -->

<!-- tags: original; id: orig-001 -->
[2026-06-01T00:00:00.000Z] original content

`;
      fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), oldFormat, "utf-8");

      // Trigger update (which calls rewriteFile)
      const newStorage = new SemanticStorage(tmpDir);
      newStorage.update("orig-001", "updated content");

      const file = fs.readFileSync(path.join(tmpDir, "MEMORY.md"), "utf-8");
      // After rewrite, should be in new format
      expect(file).toMatch(/updated content <!-- ts:/);
      expect(file).not.toMatch(/\n\[2026-06-01/);
    });
  });
});
