import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { InMemoryIndex } from "../../src/storage/index";

describe("InMemoryIndex", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-idx-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("should build from memories", () => {
    const idx = new InMemoryIndex(tmpDir, 3, false);
    const entries = [
      { id: "m1", content: "Python async programming" },
      { id: "m2", content: "JavaScript event loop" },
      { id: "m3", content: "Python decorator patterns" },
    ];
    const loaded = idx.loadOrBuild(entries);
    expect(loaded).toBe(false);
    expect(idx.built).toBe(true);
    expect(idx.bm25.doc_count).toBe(3);
  });

  it("should search and return relevant IDs", () => {
    const idx = new InMemoryIndex(tmpDir, 3, false);
    idx.loadOrBuild([
      { id: "a", content: "REST API endpoint design" },
      { id: "b", content: "Database indexing strategies" },
      { id: "c", content: "API authentication with JWT" },
    ]);
    const results = idx.search("API");
    expect(results.length).toBeGreaterThan(0);
    // "a" and "c" both contain "api"
    expect(results).toContain("a");
    expect(results).toContain("c");
  });

  it("should save and load JSON index", () => {
    const idx = new InMemoryIndex(tmpDir, 3, true);
    idx.loadOrBuild([
      { id: "x", content: "Test content here" },
      { id: "y", content: "More test content" },
    ]);

    const jsonPath = path.join(tmpDir, ".claw-mem-index", "index_v5.0.0.json");
    expect(fs.existsSync(jsonPath)).toBe(true);

    // Reload
    const idx2 = new InMemoryIndex(tmpDir, 3, true);
    const loaded = idx2.loadOrBuild([]);
    expect(loaded).toBe(true);
    expect(idx2.built).toBe(true);
    expect(idx2.ngramIndex.size).toBeGreaterThan(0);
  });

  it("should add memory incrementally", () => {
    const idx = new InMemoryIndex(tmpDir, 3, false);
    idx.loadOrBuild([{ id: "init", content: "Initial memory" }]);
    idx.addMemory("New memory added", "new-id", false);
    expect(idx.bm25.doc_count).toBe(2);
    const results = idx.search("new");
    expect(results).toContain("new-id");
  });

  it("should return empty when not built", () => {
    const idx = new InMemoryIndex(tmpDir, 3, false);
    expect(idx.search("anything").length).toBe(0);
  });

  it("should limit search results", () => {
    const idx = new InMemoryIndex(tmpDir, 3, false);
    const entries = Array.from({ length: 20 }, (_, i) => ({
      id: `m${i}`,
      content: `Python async programming patterns part ${i}`,
    }));
    idx.loadOrBuild(entries);
    const results = idx.search("Python programming", 5);
    expect(results.length).toBeLessThanOrEqual(5);
  });
});
