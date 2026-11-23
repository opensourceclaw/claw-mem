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

/**
 * Explicit reconciliation exemptions. Every entry must be an EXPERIMENTAL or
 * INTERNAL tool that is registered at runtime but intentionally absent from
 * the published contract; the receipt must justify each one. Empty today:
 * all 21 registered tools are expected public surface.
 */
const INTERNAL_TOOL_EXEMPTIONS: readonly string[] = [];

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

  it("declared tools ∪ explicit exemptions reconcile with the runtime surface", () => {
    const registered = registerRealPlugin(tmp);
    const declared = manifest.contracts.tools;

    // No duplicate declarations, no double classification.
    expect(new Set(declared).size, "declared tools must be unique").toBe(declared.length);
    expect(new Set(INTERNAL_TOOL_EXEMPTIONS).size).toBe(INTERNAL_TOOL_EXEMPTIONS.length);
    for (const name of INTERNAL_TOOL_EXEMPTIONS) {
      expect(declared, `exempted tool must not also be declared: ${name}`).not.toContain(name);
    }

    // Reconciliation (not a one-way subset): every declared/registered tool is
    // accounted for on exactly one side.
    expect([...declared, ...INTERNAL_TOOL_EXEMPTIONS].sort()).toEqual([...registered.keys()].sort());
    expect(registered.size).toBe(21);
  });

  it("the reconciliation is not vacuous (dropping a declaration breaks it)", () => {
    const registered = registerRealPlugin(tmp);
    const declaredMinusOne = manifest.contracts.tools.slice(1);
    expect([...declaredMinusOne, ...INTERNAL_TOOL_EXEMPTIONS].sort()).not.toEqual(
      [...registered.keys()].sort(),
    );
  });
});
