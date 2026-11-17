// v7.11 — real-config tests (fixture-free): the shipped plugin manifest is
// loaded from disk and cross-checked against the real registration surface.
// Source: SWE-Bench Pro V2 "Insufficient tests" absorption §4 — fixture-only
// tests cannot catch a real-config drift (the v7.10 loader lesson).

import { describe, it, expect, afterEach } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { fileURLToPath } from "url";
import plugin from "../../src/plugin";
import { resetMemoryManager } from "../../src/memory_manager.js";
import { VERSION } from "../../src/version";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const MANIFEST_PATH = path.join(ROOT, "openclaw.plugin.json");
const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf-8")) as {
  id: string;
  version: string;
  kind: string;
  capabilities: string[];
  entry: string;
  exports: Record<string, string>;
  configSchema: { properties: Record<string, { type: string; default: unknown }> };
  contracts: { tools: string[] };
};

interface RegisteredTool {
  name: string;
  execute: (id: string, params: unknown) => Promise<unknown>;
}

function registerRealPlugin(workspaceDir: string): Map<string, RegisteredTool> {
  const tools = new Map<string, RegisteredTool>();
  const api = {
    pluginConfig: { workspaceDir },
    config: { workspaceDir },
    logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
    on: () => {},
    registerTool: (tool: RegisteredTool) => tools.set(tool.name, tool),
    registerService: () => {},
    registerMemoryCapability: () => {},
  };
  (plugin as any).register(api);
  return tools;
}

describe("real plugin config — openclaw.plugin.json (fixture-free)", () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-realcfg-"));

  afterEach(() => {
    fs.rmSync(tmp, { recursive: true, force: true });
    resetMemoryManager();
  });

  it("declares the shipped identity, kind, and memory capabilities", () => {
    expect(manifest.id).toBe("claw-mem");
    expect(manifest.kind).toBe("memory");
    expect(manifest.version).toBe(VERSION);
    expect(manifest.capabilities).toEqual([
      "memory-store",
      "memory-retrieve",
      "memory-search",
      "memory-manage",
    ]);
  });

  it("entry and exports resolve to the built plugin entry", () => {
    expect(manifest.entry).toBe("./dist/src/plugin.js");
    expect(manifest.exports["."]).toBe("./dist/src/plugin.js");
    expect(manifest.exports["./plugin"]).toBe("./dist/src/plugin.js");
    expect(manifest.exports["./types"]).toBe("./dist/src/types.d.ts");
  });

  it("configSchema defaults match the documented storage contract", () => {
    expect(manifest.configSchema.properties.storagePath).toMatchObject({
      type: "string",
      default: "~/.openclaw/memory",
    });
    expect(manifest.configSchema.properties.maxFileSize).toMatchObject({
      type: "string",
      default: "10MB",
    });
    expect(manifest.configSchema.properties.compression).toMatchObject({
      type: "boolean",
      default: true,
    });
  });

  it("every tool declared in contracts.tools is registered by the real plugin", () => {
    const registered = registerRealPlugin(tmp);
    expect(manifest.contracts.tools.length).toBeGreaterThan(0);
    for (const name of manifest.contracts.tools) {
      expect(registered.has(name), `declared tool not registered: ${name}`).toBe(true);
    }
    // The runtime surface is additive beyond the frozen contract (navigation
    // tools + error-pattern-card store). This assertion locks the current
    // surface; the additive set is reported as a config-drift observation.
    expect(registered.size).toBe(21);
    for (const name of ["memory_list", "memory_links", "memory_read", "memory_source"]) {
      expect(registered.has(name), name).toBe(true);
    }
  });
});
