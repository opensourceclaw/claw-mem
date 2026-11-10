import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { EpisodicStorage } from "../../src/storage/episodic";

describe("EpisodicStorage", () => {
  let tmpDir: string;
  let storage: EpisodicStorage;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-ts-"));
    storage = new EpisodicStorage(tmpDir, 7);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("should create memory directory on init", () => {
    // Memory directory is the workspace itself (workspace = memory directory)
    expect(fs.existsSync(tmpDir)).toBe(true);
  });

  it("should store and retrieve memory", () => {
    storage.store({
      content: "User prefers Python over JavaScript",
      tags: ["preference"],
      timestamp: "2026-05-29T10:00:00",
    });
    const all = storage.getAll();
    expect(all.length).toBe(1);
    expect(all[0].content).toBe("User prefers Python over JavaScript");
    expect(all[0].tags).toContain("preference");
  });

  it("should store multiple records", () => {
    storage.store({ content: "Record 1", tags: [], timestamp: "" });
    storage.store({ content: "Record 2", tags: [], timestamp: "" });
    expect(storage.count()).toBe(2);
  });

  it("should parse metadata comment with session_id", () => {
    storage.store({
      content: "Test content",
      tags: ["a", "b"],
      session_id: "sess-001",
      timestamp: "2026-05-29T12:00:00",
    });
    const all = storage.getAll();
    expect(all[0].session_id).toBe("sess-001");
    expect(all[0].tags.length).toBe(2);
    expect(all[0].type).toBe("episodic");
  });

  it("should get recent entries", () => {
    for (let i = 0; i < 10; i++) {
      storage.store({ content: `Item ${i}`, tags: [], timestamp: "" });
    }
    expect(storage.getRecent(5).length).toBe(5);
  });

  it("should return empty for non-existent date", () => {
    expect(storage.getByDate("2020-01-01").length).toBe(0);
  });

  it("should soft-delete expired files into _archive (no physical delete)", () => {
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 40);
    const oldDateStr = oldDate.toISOString().slice(0, 10);
    const memoryDir = path.join(tmpDir, "memory");
    const oldFile = path.join(memoryDir, `${oldDateStr}.md`);
    fs.mkdirSync(memoryDir, { recursive: true });
    fs.writeFileSync(oldFile, `Old memory <!-- ts:${oldDateStr}T00:00:00.000Z -->\n`, "utf-8");

    const archived = storage.cleanupExpired();
    expect(archived).toBe(1);
    // Active layer no longer serves it…
    expect(fs.existsSync(oldFile)).toBe(false);
    expect(storage.getByDate(oldDateStr)).toEqual([]);
    // …but the bytes survive in the archive and remain queryable on disk.
    const archivedFile = path.join(memoryDir, "_archive", `${oldDateStr}.md`);
    expect(fs.existsSync(archivedFile)).toBe(true);
    expect(fs.readFileSync(archivedFile, "utf-8")).toContain("Old memory");
  });

  it("keeps files within the TTL in the active layer", () => {
    storage.store({ content: "Recent", tags: [], timestamp: "" });
    expect(storage.cleanupExpired()).toBe(0);
    expect(storage.count()).toBe(1);
  });

  it("append-only: storing a new record never rewrites existing bytes", () => {
    storage.store({ content: "First", tags: [], timestamp: "2026-01-01T00:00:00.000Z" });
    const today = new Date().toISOString().slice(0, 10);
    const filePath = path.join(tmpDir, "memory", `${today}.md`);
    const before = fs.readFileSync(filePath, "utf-8");

    storage.store({ content: "Second", tags: [], timestamp: "2026-01-01T00:00:01.000Z" });
    const after = fs.readFileSync(filePath, "utf-8");

    // The previous snapshot is an exact byte prefix of the new file.
    expect(after.startsWith(before)).toBe(true);
    expect(after).toContain("First");
    expect(after).toContain("Second");
  });

  it("should count total records", () => {
    expect(storage.count()).toBe(0);
    storage.store({ content: "A", tags: [], timestamp: "" });
    storage.store({ content: "B", tags: [], timestamp: "" });
    expect(storage.count()).toBe(2);
  });

  // ── v6.27.2: Timestamp Format ───────────────────────────────────────

  describe("v6.27.2 timestamp format", () => {
    it("writes new format with trailing timestamp", () => {
      storage.store({
        content: "episodic memory content",
        tags: ["daily"],
        timestamp: "2026-06-29T10:00:00.000Z",
        session_id: "sess-test",
      });

      const files = fs.readdirSync(path.join(tmpDir, "memory"));
      const file = fs.readFileSync(path.join(tmpDir, "memory", files[0]), "utf-8");

      // Should have new format
      expect(file).toMatch(/episodic memory content <!-- ts:2026-06-29T10:00:00\.000Z -->/);
      // Should NOT have old format
      expect(file).not.toMatch(/\n\[2026-06-29/);
    });

    it("reads old format with leading timestamp", () => {
      const today = new Date().toISOString().slice(0, 10);
      const oldFormat = `<!-- session: sess-old; tags: legacy -->
[2026-06-28T10:00:00.000Z] old episodic content
`;
      fs.mkdirSync(path.join(tmpDir, "memory"), { recursive: true });
      fs.writeFileSync(path.join(tmpDir, "memory", `${today}.md`), oldFormat, "utf-8");

      const newStorage = new EpisodicStorage(tmpDir, 7);
      const entries = newStorage.getAll();

      expect(entries.length).toBe(1);
      expect(entries[0].content).toBe("old episodic content");
      expect(entries[0].timestamp).toBe("2026-06-28T10:00:00.000Z");
      expect(entries[0].session_id).toBe("sess-old");
      expect(entries[0].tags).toContain("legacy");
    });

    it("reads mixed format file", () => {
      const today = new Date().toISOString().slice(0, 10);
      const mixed = `<!-- session: s1; tags: old -->
[2026-06-01T00:00:00.000Z] old episodic entry
<!-- session: s2; tags: new -->
new episodic entry <!-- ts:2026-06-02T00:00:00.000Z -->
`;
      fs.mkdirSync(path.join(tmpDir, "memory"), { recursive: true });
      fs.writeFileSync(path.join(tmpDir, "memory", `${today}.md`), mixed, "utf-8");

      const newStorage = new EpisodicStorage(tmpDir, 7);
      const entries = newStorage.getAll();

      expect(entries.length).toBe(2);
      expect(entries[0].content).toBe("old episodic entry");
      expect(entries[1].content).toBe("new episodic entry");
    });
  });
});
