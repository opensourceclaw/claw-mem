// Copyright 2026 OpenSourceClaw Contributors
// v7.10.0 (ADR-008): read-only navigation tools — surface lock (20→21),
// config switch, list/links/read/source behavior, and legacy tool regression.

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import plugin from "../../src/plugin";
import { getMemoryManager, resetMemoryManager, type MemoryManager } from "../../src/memory_manager.js";

interface RegisteredTool {
  name: string;
  execute: (id: string, params: any) => Promise<any>;
}

const ORIGINAL_TOOLS = [
  "memory_search",
  "memory_store",
  "memory_error_pattern_card_store",
  "memory_get",
  "memory_forget",
  "memory_failure_classify",
  "memory_get_constitution",
  "memory_promote_constitution_rule",
  "memory_delete_constitution_rule",
  "memory_transcript_get",
  "memory_transcript_search",
  "memory_session_snapshot",
  "memory_session_get_latest",
  "memory_entity_search",
  "memory_entity_list",
  "memory_get_preference",
  "memory_rollback_preference",
];

const NAVIGATION_TOOLS = ["memory_list", "memory_links", "memory_read", "memory_source"];

function registerPlugin(tmpDir: string, pluginConfig: Record<string, unknown> = {}): Map<string, RegisteredTool> {
  const tools = new Map<string, RegisteredTool>();
  const api = {
    pluginConfig: { workspaceDir: tmpDir, ...pluginConfig },
    config: { workspaceDir: tmpDir },
    logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
    on: () => {},
    registerTool: (tool: RegisteredTool) => tools.set(tool.name, tool),
    registerService: () => {},
    registerMemoryCapability: () => {},
  };
  (plugin as any).register(api);
  return tools;
}

async function call(tools: Map<string, RegisteredTool>, name: string, params: any = {}): Promise<any> {
  const result = await tools.get(name)!.execute("id", params);
  return JSON.parse(result.content[0].text);
}

describe("ADR-008 navigation tool surface", () => {
  let tmpDir: string;
  let manager: MemoryManager;
  let tools: Map<string, RegisteredTool>;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-nav-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    resetMemoryManager();
    tools = registerPlugin(tmpDir);
    // The plugin's TsBridge constructs the singleton; use that exact instance
    // (getMemoryManager(opts) would replace it).
    manager = getMemoryManager();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("locks the 21-tool surface: original 17 + four navigation tools", () => {
    expect(tools.size).toBe(21);
    for (const name of ORIGINAL_TOOLS) expect(tools.has(name), name).toBe(true);
    for (const name of NAVIGATION_TOOLS) expect(tools.has(name), name).toBe(true);
  });

  it("tools.navigation=false keeps the original 17-tool surface", () => {
    const disabled = registerPlugin(tmpDir, { tools: { navigation: false } });
    expect(disabled.size).toBe(17);
    for (const name of ORIGINAL_TOOLS) expect(disabled.has(name), name).toBe(true);
    for (const name of NAVIGATION_TOOLS) expect(disabled.has(name), name).toBe(false);
  });

  it("memory_list returns metadata only, with layer/prefix/limit filters", async () => {
    manager.store("List title one", "episodic", ["t1"], {}, { eventTime: "2026-01-01" });
    manager.store("Semantic title", "semantic", ["t2"]);
    manager.store("dark", "preference", [], { pref_key: "theme" });

    const episodic = await call(tools, "memory_list", { layer: "episodic" });
    expect(episodic.items).toHaveLength(1);
    const row = episodic.items[0];
    expect(row.title).toBe("List title one");
    expect(row.time).toBe("2026-01-01");
    expect(row.tags).toContain("t1");
    expect(row).not.toHaveProperty("text");

    const prefs = await call(tools, "memory_list", { layer: "preference" });
    expect(prefs.items).toHaveLength(1);
    expect(prefs.items[0].id).toBe("pref:theme");
    expect(prefs.items[0].title).toBe("theme");

    const prefixed = await call(tools, "memory_list", { prefix: "List", limit: 1 });
    expect(prefixed.items).toHaveLength(1);
    expect(prefixed.items[0].title).toBe("List title one");
  });

  it("memory_read/memory_get support 1-based inclusive line ranges", async () => {
    // Storage formats are single-line; exercise the range logic at the record
    // layer where a long, multi-line record is faithfully represented.
    (manager as any)._episodic.getAll = () => [
      {
        id: "multi-line",
        content: "L1\nL2\nL3\nL4",
        timestamp: "2026-11-16T00:00:00.000Z",
        tags: ["multi"],
        metadata: {},
      },
    ];

    const ranged = await call(tools, "memory_read", { id: "multi-line", lines: [2, 3] });
    expect(ranged.text).toBe("L2\nL3");
    expect(ranged.lineRange).toEqual([2, 3]);
    expect(ranged.totalLines).toBe(4);

    const full = await call(tools, "memory_get", { id: "multi-line" });
    expect(full.text).toBe("L1\nL2\nL3\nL4");
    expect(full.lineRange).toBeUndefined();

    const clamped = await call(tools, "memory_read", { id: "multi-line", lines: [3, 99] });
    expect(clamped.text).toBe("L3\nL4");
    expect(clamped.lineRange).toEqual([3, 4]);

    const missing = await call(tools, "memory_read", { id: "no-such-record" });
    expect(missing.error).toContain("memory not found");
  });

  it("memory_links derives out refs and shared-evidence backlinks", async () => {
    manager.startTranscriptSession("link-session", "api");
    manager.appendTranscriptMessage({
      role: "user",
      content: "shared source",
      timestamp: "2026-11-16T00:00:00.000Z",
    });
    manager.endTranscriptSession();

    manager.store("record A cites evidence", "episodic", [], {}, {
      evidence: [{ span: "cites", sourceRefs: ["link-session"] }],
    });
    manager.store("record B cites same evidence", "episodic", [], {}, {
      evidence: [{ span: "same", sourceRefs: ["link-session"] }],
    });
    manager.store("record C has no evidence", "episodic");

    const listed = await call(tools, "memory_list", { layer: "episodic" });
    const idA = listed.items.find((i: any) => i.title === "record A cites evidence").id;
    const idB = listed.items.find((i: any) => i.title === "record B cites same evidence").id;
    const idC = listed.items.find((i: any) => i.title === "record C has no evidence").id;

    const linksA = await call(tools, "memory_links", { id: idA });
    expect(linksA.out).toEqual([{ ref: "link-session", type: "transcript" }]);
    expect(linksA.in.map((x: any) => x.id)).toContain(idB);
    expect(linksA.in.map((x: any) => x.id)).not.toContain(idC);

    const linksC = await call(tools, "memory_links", { id: idC });
    expect(linksC.out).toEqual([]);
    expect(linksC.in).toEqual([]);
  });

  it("memory_source resolves transcripts/paths and enforces 10-ref / 2KB caps", async () => {
    manager.startTranscriptSession("source-session", "api");
    manager.appendTranscriptMessage({
      role: "user",
      content: "x".repeat(3000),
      timestamp: "2026-11-16T00:00:00.000Z",
    });
    manager.endTranscriptSession();
    fs.writeFileSync(path.join(tmpDir, "note.md"), "note body", "utf-8");

    const refs = [
      "source-session",
      "note.md",
      "missing-ref",
      ...Array.from({ length: 10 }, (_, i) => `missing-${i}`),
    ];
    const out = await call(tools, "memory_source", { refs });

    expect(out.requested).toBe(13);
    expect(out.returned).toBe(10);
    expect(out.maxRefsPerCall).toBe(10);
    expect(out.maxCharsPerItem).toBe(2048);

    expect(out.sources[0]).toMatchObject({ ref: "source-session", type: "transcript", found: true, truncated: true });
    expect(out.sources[0].text).toHaveLength(2048);
    expect(out.sources[1]).toMatchObject({ ref: "note.md", type: "path", found: true });
    expect(out.sources[1].text).toBe("note body");
    expect(out.sources[2]).toMatchObject({ ref: "missing-ref", found: false });
  });

  it("leaves the original memory_search behavior intact", async () => {
    manager.store("searchable old tool record", "episodic");
    const out = await call(tools, "memory_search", { query: "searchable" });
    expect(out.results.length).toBeGreaterThan(0);
    expect(String(out.results[0].content)).toContain("searchable");
  });
});
