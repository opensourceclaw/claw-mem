// OpenClaw trial bug: every plugin tool must return an MCP-style envelope
// (`content: [{ type: "text", text }]`). The raw bridge payload has no
// `content` field, so OpenClaw rejected every agent-facing tool result.

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const { handleRequestMock } = vi.hoisted(() => ({
  handleRequestMock: vi.fn(),
}));

vi.mock("../../src/bridge", () => ({
  handleRequest: handleRequestMock,
}));

import plugin, { toToolResult } from "../../src/plugin";

describe("MCP tool-result envelope", () => {
  let tmpDir: string;
  let tools: Map<string, any>;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-mcp-"));
    tools = new Map();
    const api = {
      pluginConfig: { workspaceDir: tmpDir },
      config: { workspaceDir: tmpDir },
      logger: { info: () => {}, warn: () => {}, error: () => {}, debug: () => {} },
      on: () => {},
      registerTool: (tool: any) => tools.set(tool.name, tool),
      registerService: () => {},
      registerMemoryCapability: () => {},
    };
    (plugin as any).register(api);
    handleRequestMock.mockReset();
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  it("wraps a successful bridge payload", async () => {
    handleRequestMock.mockResolvedValue({ result: { results: [{ id: "m1" }] } });

    const res = await tools.get("memory_search").execute("id", { query: "x" });

    expect(Array.isArray(res.content)).toBe(true);
    expect(res.content[0].type).toBe("text");
    expect(JSON.parse(res.content[0].text)).toEqual({ results: [{ id: "m1" }] });
  });

  it("wraps a bridge error in the same envelope", async () => {
    handleRequestMock.mockResolvedValue({ error: { message: "boom" } });

    const res = await tools.get("memory_search").execute("id", { query: "x" });

    expect(Array.isArray(res.content)).toBe(true);
    expect(res.content[0].type).toBe("text");
    expect(JSON.parse(res.content[0].text)).toEqual({ error: "boom" });
  });

  it("wraps early-return tools", async () => {
    for (const name of ["memory_get", "memory_forget"]) {
      const res = await tools.get(name).execute("id", { id: "x" });
      expect(Array.isArray(res.content), name).toBe(true);
      expect(res.content[0].type, name).toBe("text");
    }
  });

  it("every registered tool returns an envelope", async () => {
    handleRequestMock.mockResolvedValue({ result: { ok: true } });

    for (const [name, tool] of tools) {
      const res = await tool.execute("id", { query: "x", text: "y", id: "z" });
      expect(Array.isArray(res.content), name).toBe(true);
      expect(res.content[0].type, name).toBe("text");
    }
  });

  it("toToolResult handles empty payloads", () => {
    expect(JSON.parse(toToolResult(undefined).content[0].text)).toEqual({});
    expect(JSON.parse(toToolResult(null).content[0].text)).toEqual({});
  });
});
