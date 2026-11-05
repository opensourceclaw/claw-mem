// Regression tests from the v7.8.0 OpenClaw trial findings
// (devclaw/docs/bugs/2026-11-05-openclaw-trial-findings.md):
// BUG-1 index lazy-load deadlock, BUG-3 hybrid keyword leg + semantic
// degradation, BUG-4 CJK bigram recall, BUG-5 manifest entry.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { MemoryManager } from "../../src/memory_manager";

const REPO_ROOT = path.resolve(import.meta.dirname, "../..");
const settle = () => new Promise((r) => setTimeout(r, 80));

describe("v7.8.0 trial findings", () => {
  let tmpDir: string;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-trial-"));
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("BUG-1: a second instance with a cached index builds eagerly and finds Chinese memory", async () => {
    const first = new MemoryManager({ workspace: tmpDir });
    await settle();
    first.store("Peter 的猫叫 Mochi，是一只三岁的橘猫", "episodic", ["pet"]);

    const second = new MemoryManager({ workspace: tmpDir });
    await settle();

    expect(second.getStats().indexBuilt).toBe(true);

    second.store("舰队成员：Vision 是舰队统领", "episodic", ["team"]);
    const results = second.search("舰队有谁", undefined, 3);

    expect(results.length).toBeGreaterThan(0);
    expect(String(results[0].content)).toContain("舰队");
  });

  it("BUG-4: CJK bigram recall beats the old trigram-only miss", async () => {
    const mm = new MemoryManager({ workspace: tmpDir });
    await settle();
    mm.store("舰队成员：Vision 是舰队统领", "episodic", ["team"]);

    const results = mm.search("舰队有谁", undefined, 3);
    expect(results.length).toBeGreaterThan(0);
    expect(String(results[0].content)).toContain("舰队成员");
  });

  it("BUG-4: Chinese preference outranks the cat memory for a preference query", async () => {
    const mm = new MemoryManager({ workspace: tmpDir });
    await settle();
    mm.store("Peter 的猫叫 Mochi，是一只三岁的橘猫", "episodic", ["pet"]);
    mm.store("Peter 喜欢简洁直接的汇报，不要冗长", "semantic", ["preference"]);

    const results = mm.search("Peter 喜欢什么样的汇报", undefined, 3);
    expect(results.length).toBeGreaterThan(0);
    expect(String(results[0].content)).toContain("汇报");
  });

  it("BUG-3: hybridSearch uses the keyword leg out of the box and reports semantic degradation", async () => {
    const mm = new MemoryManager({ workspace: tmpDir });
    await settle();
    mm.store("TypeScript 事件循环与微任务队列", "episodic", ["dev"]);

    const result = mm.hybridSearch("事件循环", { topK: 5 });

    expect(result.results.length).toBeGreaterThan(0);
    expect(result.metadata.keywordCount).toBeGreaterThan(0);
    expect(result.metadata.semanticDisabled).toBe("no embedding config");
  });

  it("BUG-2: storagePath is honoured as a workspace alias", async () => {
    const storagePath = path.join(tmpDir, "custom-store");
    const mm = new MemoryManager({ storagePath });
    expect(mm.workspace).toBe(storagePath);
    mm.store("alias path memory", "episodic");
    expect(fs.existsSync(path.join(storagePath, ".claw-mem-index"))).toBe(true);
    await settle();
  });

  it("BUG-5: plugin manifest points at build output", () => {
    const manifest = JSON.parse(
      fs.readFileSync(path.join(REPO_ROOT, "openclaw.plugin.json"), "utf-8"),
    ) as { entry: string; exports: Record<string, string> };
    expect(manifest.entry).toMatch(/^\.\/dist\//);
    expect(fs.existsSync(path.join(REPO_ROOT, manifest.entry))).toBe(true);
    for (const target of Object.values(manifest.exports)) {
      expect(target).toMatch(/^\.\/dist\//);
      expect(fs.existsSync(path.join(REPO_ROOT, target))).toBe(true);
    }
  });

  it("F-1: a startup-window miss does not outlive the index build", async () => {
    const mm = new MemoryManager({ workspace: tmpDir });
    mm.store("Peter 的猫叫 Mochi，是一只三岁的橘猫", "episodic", ["pet"]);
    mm.search("Peter 家里养的动物", undefined, 3); // may miss and be cached
    await settle();
    const after = mm.search("Peter 家里养的动物", undefined, 3);
    expect(after.length).toBeGreaterThan(0);
    expect(String(after[0].content)).toContain("Mochi");
  });

  it("F-1: store invalidates a cached miss (write-after-read)", async () => {
    const mm = new MemoryManager({ workspace: tmpDir });
    await settle();
    const before = mm.search("舰队有谁", undefined, 3);
    expect(before).toEqual([]);
    mm.store("舰队成员：Vision 是舰队统领", "episodic", ["team"]);
    const after = mm.search("舰队有谁", undefined, 3);
    expect(after.length).toBeGreaterThan(0);
  });

  it("F-2: procedural records written before the index build are searchable", async () => {
    const mm = new MemoryManager({ workspace: tmpDir });
    mm.store("舰队成员：Vision 是舰队统领", "procedural", ["team"]);
    await settle();
    expect(mm.getStats().indexBuilt).toBe(true);
    const results = mm.search("舰队有谁", undefined, 3);
    expect(results.length).toBeGreaterThan(0);
    expect(String(results[0].content)).toContain("舰队成员");
  });
});
