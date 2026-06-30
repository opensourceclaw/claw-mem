// Entity Index Persistence Unit Tests (v6.31.0)

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { EntityIndex } from "../../src/entity/entity-index.js";

describe("EntityIndex Persistence", () => {
  let tmpDir: string;
  let indexDir: string;
  let entityIndex: EntityIndex;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-entity-persist-"));
    indexDir = path.join(tmpDir, ".claw-mem-index");
    entityIndex = new EntityIndex();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("enables persistence with directory path", () => {
    entityIndex.enablePersistence(indexDir);
    expect(fs.existsSync(indexDir)).toBe(true);
  });

  it("saves entity index to disk", () => {
    entityIndex.enablePersistence(indexDir);
    entityIndex.index("Working on claw-mem with TypeScript", "mem_1");
    entityIndex.save();

    const filePath = path.join(indexDir, "entity_index_v1.0.0.json");
    expect(fs.existsSync(filePath)).toBe(true);

    const content = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    expect(content.version).toBe("1.0.0");
    expect(content.entityMap.length).toBeGreaterThan(0);
  });

  it("loads entity index from disk", () => {
    // Create and save
    entityIndex.enablePersistence(indexDir);
    entityIndex.index("Working on claw-mem with TypeScript", "mem_1");
    entityIndex.save();

    // Create new index and load
    const newIndex = new EntityIndex();
    newIndex.enablePersistence(indexDir);
    const loaded = newIndex.load();

    expect(loaded).toBe(true);

    const result = newIndex.search("clawmem");
    expect(result).not.toBeNull();
    expect(result?.entity.name).toBe("clawmem");
  });

  it("returns false when no persisted index exists", () => {
    entityIndex.enablePersistence(indexDir);
    const loaded = entityIndex.load();
    expect(loaded).toBe(false);
  });

  it("handles corrupted index file gracefully", () => {
    entityIndex.enablePersistence(indexDir);

    // Write corrupted JSON
    const filePath = path.join(indexDir, "entity_index_v1.0.0.json");
    fs.writeFileSync(filePath, "{ invalid json }", "utf-8");

    const loaded = entityIndex.load();
    expect(loaded).toBe(false);
  });
});