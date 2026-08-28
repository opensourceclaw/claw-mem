// Copyright 2026 OpenSourceClaw Contributors
// claw-mem v6.32.5 — Real Hook Integration Tests
// Tests message_received and llm_output plugin hooks for transcript capture

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import * as fs from "fs";
import * as path from "path";
import * as os from "os";

// Real import from src/
import plugin from "../../src/plugin.js";

interface MockApi {
  id: string;
  config: any;
  pluginConfig?: Record<string, unknown>;
  logger: {
    info: ReturnType<typeof vi.fn>;
    error: ReturnType<typeof vi.fn>;
    warn: ReturnType<typeof vi.fn>;
    debug?: ReturnType<typeof vi.fn>;
  };
  registerTool: ReturnType<typeof vi.fn>;
  on: ReturnType<typeof vi.fn>;
  registerService: ReturnType<typeof vi.fn>;
  registerMemoryCapability: ReturnType<typeof vi.fn>;
}

describe("Real Hook Integration Tests (v6.32.5)", () => {
  let tmpDir: string;
  let transcriptsDir: string;
  let mockApi: MockApi;
  let eventHandlers: Map<string, (event: any, ctx: any) => Promise<void>>;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "claw-mem-real-"));
    fs.writeFileSync(path.join(tmpDir, "MEMORY.md"), "# MEMORY.md\n\n", "utf-8");
    transcriptsDir = path.join(tmpDir, "transcripts");

    eventHandlers = new Map();

    mockApi = {
      id: "test-api",
      config: { workspaceDir: tmpDir },
      pluginConfig: { workspaceDir: tmpDir, topK: 10, debug: false },
      logger: {
        info: vi.fn(),
        error: vi.fn(),
        warn: vi.fn(),
        debug: vi.fn(),
      },
      registerTool: vi.fn(),
      on: vi.fn((event: string, handler: (event: any, ctx: any) => Promise<void>) => {
        eventHandlers.set(event, handler);
      }),
      registerService: vi.fn(),
      registerMemoryCapability: vi.fn(),
    };

    // Register the plugin to capture handlers
    (plugin as any).register(mockApi);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  describe("message_received hook", () => {
    it("TC-1: captures user message with content", async () => {
      const handler = eventHandlers.get("message_received");
      expect(handler).toBeDefined();

      await handler!(
        { content: "Hello, world!", sessionKey: "test-session-123" },
        {}
      );

      // Verify transcript file was created
      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-test-session-123.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);

      // Verify content
      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("Hello, world!");
      expect(content).toContain("[User]");
    });

    it("TC-2: uses fallback session ID when sessionKey missing", async () => {
      const handler = eventHandlers.get("message_received");

      await handler!(
        { content: "No session key" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(true);

      // Should have a fallback session file
      const files = fs.readdirSync(dateDir);
      expect(files.length).toBe(1);
      expect(files[0]).toMatch(/^session-session-\d{4}-\d{2}-\d{2}\.md$/);
    });

    it("TC-3: tracks runId from event", async () => {
      const handler = eventHandlers.get("message_received");

      await handler!(
        { content: "With runId", sessionKey: "runid-test", runId: "run-abc-123" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-runid-test.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });

    it("TC-4: skips empty content", async () => {
      const handler = eventHandlers.get("message_received");

      await handler!(
        { content: "", sessionKey: "empty-test" },
        {}
      );

      // Should not create session for empty content
      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(false);
    });
  });

  describe("llm_output hook", () => {
    it("TC-5: captures assistant response with assistantTexts", async () => {
      const handler = eventHandlers.get("llm_output");
      expect(handler).toBeDefined();

      await handler!(
        { assistantTexts: ["Hello! How can I help you?"], sessionId: "assistant-test" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-assistant-test.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);

      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("Hello! How can I help you?");
      expect(content).toContain("[Assistant]");
    });

    it("TC-6: joins multiple assistantTexts blocks", async () => {
      const handler = eventHandlers.get("llm_output");

      await handler!(
        {
          assistantTexts: ["First paragraph.", "Second paragraph."],
          sessionId: "multi-block"
        },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-multi-block.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      expect(content).toContain("First paragraph.");
      expect(content).toContain("Second paragraph.");
    });

    it("TC-7: filters empty strings from assistantTexts", async () => {
      const handler = eventHandlers.get("llm_output");

      await handler!(
        {
          assistantTexts: ["", "Valid text", "", "More text", ""],
          sessionId: "filter-empty"
        },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-filter-empty.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      expect(content).toContain("Valid text");
      expect(content).toContain("More text");
    });

    it("TC-8: skips empty assistantTexts array", async () => {
      const handler = eventHandlers.get("llm_output");

      await handler!(
        { assistantTexts: [], sessionId: "empty-array" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(false);
    });
  });

  describe("full conversation flow", () => {
    it("TC-9: records complete conversation with user and assistant", async () => {
      const userHandler = eventHandlers.get("message_received");
      const assistantHandler = eventHandlers.get("llm_output");

      // User message
      await userHandler!(
        { content: "What is OpenClaw?", sessionKey: "full-conv", runId: "run-1" },
        {}
      );

      // Assistant response
      await assistantHandler!(
        { assistantTexts: ["OpenClaw is an AI agent framework."], sessionId: "full-conv", runId: "run-1" },
        {}
      );

      // Second turn
      await userHandler!(
        { content: "Does it support TypeScript?", sessionKey: "full-conv", runId: "run-2" },
        {}
      );

      await assistantHandler!(
        { assistantTexts: ["Yes, it has first-class TypeScript support."], sessionId: "full-conv", runId: "run-2" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-full-conv.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      // Verify all messages present
      expect(content).toContain("What is OpenClaw?");
      expect(content).toContain("OpenClaw is an AI agent framework.");
      expect(content).toContain("Does it support TypeScript?");
      expect(content).toContain("Yes, it has first-class TypeScript support.");

      // Count User/Assistant markers
      const userCount = (content.match(/\[User\]/g) || []).length;
      const assistantCount = (content.match(/\[Assistant\]/g) || []).length;
      expect(userCount).toBe(2);
      expect(assistantCount).toBe(2);
    });

    it("TC-10: sanitizes sessionKey with path separators", async () => {
      const handler = eventHandlers.get("message_received");

      await handler!(
        { content: "Sanitized", sessionKey: "malicious/path/attempt" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      // Should be sanitized to "malicious_path_attempt"
      const transcriptPath = path.join(transcriptsDir, today, "session-malicious_path_attempt.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });
  });
});
