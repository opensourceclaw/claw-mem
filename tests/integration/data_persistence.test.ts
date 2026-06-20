// Copyright 2026 Peter Cheng
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { EpisodicStorage } from "../../src/storage/episodic";
import { SemanticStorage } from "../../src/storage/semantic";
import { ProceduralStorage } from "../../src/storage/procedural";

describe("Data Persistence (Python compatibility)", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-dp-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("TS-written episodic data is readable", () => {
    const ep = new EpisodicStorage(tmpDir);
    ep.store({ content: "Test entry", tags: ["test"], timestamp: "2026-05-30T10:00:00" });

    const entries = ep.getAll();
    expect(entries.length).toBe(1);
    expect(entries[0].content).toBe("Test entry");
    expect(entries[0].tags).toContain("test");

    // Verify the file exists in memory/YYYY-MM-DD.md format
    const today = new Date().toISOString().slice(0, 10);
    const fp = path.join(tmpDir, `${today}.md`);
    expect(fs.existsSync(fp)).toBe(true);

    // Read raw content to verify Markdown format
    const raw = fs.readFileSync(fp, "utf-8");
    expect(raw).toContain("[2026-05-30");
    expect(raw).toContain("Test entry");
  });

  it("TS-written semantic data is readable and updatable", () => {
    const sem = new SemanticStorage(tmpDir);
    sem.store({ content: "Fact one", tags: ["fact"], timestamp: "2026-05-01T00:00:00", id: "f001" });

    const all = sem.getAll();
    expect(all.length).toBe(1);
    expect(all[0].id).toBe("f001");

    // Update
    const updated = sem.update("f001", "Fact one (revised)");
    expect(updated).toBe(true);
    const all2 = sem.getAll();
    expect(all2[0].content).toBe("Fact one (revised)");
  });

  it("TS-written procedural data has correct file structure", () => {
    const proc = new ProceduralStorage(tmpDir);
    proc.store({ content: "Docker deploy steps", tags: ["docker", "procedural"], timestamp: "" });

    const skillPath = path.join(tmpDir, "skills", "docker.md");
    expect(fs.existsSync(skillPath)).toBe(true);

    const entries = proc.getSkill("docker");
    expect(entries.length).toBe(1);
    expect(entries[0].content).toBe("Docker deploy steps");
  });

  it("round-trip: write → read → append → read", () => {
    const ep = new EpisodicStorage(tmpDir);
    ep.store({ content: "Entry A", tags: [], timestamp: "2026-01-01T00:00:00" });
    expect(ep.count()).toBe(1);
    ep.store({ content: "Entry B", tags: [], timestamp: "2026-01-01T01:00:00" });
    expect(ep.count()).toBe(2);

    const all = ep.getAll();
    expect(all.length).toBe(2);
  });
});
