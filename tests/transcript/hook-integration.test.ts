// Copyright 2026 Peter Cheng
// claw-mem v6.32.4 — Real Hook Integration Tests
// Tests message_end event handler for transcript capture

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

describe("Real Hook Integration Tests (v6.32.4)", () => {
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

  describe("message_end event handler", () => {
    it("TC-1: captures user message with string content", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      // Simulate turn start with session ID
      await turnStartHandler!({ sessionId: "test-session-123" }, {});

      // Simulate user message
      await messageEndHandler!(
        { message: { role: "user", content: "Hello, world!" } },
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

    it("TC-2: captures assistant message with string content", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      // Start turn
      await turnStartHandler!({ sessionId: "assistant-test" }, {});

      // User message
      await messageEndHandler!(
        { message: { role: "user", content: "Question" } },
        {}
      );

      // Assistant message
      await messageEndHandler!(
        { message: { role: "assistant", content: "Answer" } },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-assistant-test.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      expect(content).toContain("Question");
      expect(content).toContain("Answer");
      expect(content).toContain("[User]");
      expect(content).toContain("[Assistant]");
    });

    it("TC-3: extracts text from array content blocks", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      await turnStartHandler!({ sessionId: "array-content" }, {});

      // Message with array content (LLM format)
      await messageEndHandler!(
        {
          message: {
            role: "assistant",
            content: [
              { type: "text", text: "First part" },
              { type: "thinking", text: "internal thought" }, // Should be skipped
              { type: "text", text: "Second part" },
            ]
          }
        },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-array-content.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      expect(content).toContain("First part");
      expect(content).toContain("Second part");
      expect(content).not.toContain("internal thought"); // thinking should be skipped
    });

    it("TC-4: skips non-user/assistant roles", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      await turnStartHandler!({ sessionId: "role-filter" }, {});

      // User message
      await messageEndHandler!(
        { message: { role: "user", content: "User message" } },
        {}
      );

      // Tool result (should be skipped)
      await messageEndHandler!(
        { message: { role: "toolResult", content: "Tool output" } },
        {}
      );

      // System message (should be skipped)
      await messageEndHandler!(
        { message: { role: "system", content: "System prompt" } },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-role-filter.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      expect(content).toContain("User message");
      expect(content).not.toContain("Tool output");
      expect(content).not.toContain("System prompt");
    });

    it("TC-5: uses fallback session ID when turn_start has no sessionId", async () => {
      const messageEndHandler = eventHandlers.get("message_end");

      // No turn_start - should use fallback
      await messageEndHandler!(
        { message: { role: "user", content: "Fallback test" } },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(true);

      // Should have created a session file
      const files = fs.readdirSync(dateDir);
      expect(files.length).toBe(1);
      expect(files[0]).toMatch(/^session-session-\d{4}-\d{2}-\d{2}\.md$/);
    });

    it("TC-6: uses context sessionId when available", async () => {
      const messageEndHandler = eventHandlers.get("message_end");

      // No turn_start, but context has sessionId
      await messageEndHandler!(
        { message: { role: "user", content: "Context session" } },
        { sessionId: "ctx-session-456" }
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-ctx-session-456.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });

    it("TC-7: sanitizes sessionKey with path separators", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      await turnStartHandler!({ sessionId: "malicious/path/attempt" }, {});
      await messageEndHandler!(
        { message: { role: "user", content: "Sanitized" } },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      // Should be sanitized to "malicious_path_attempt"
      const transcriptPath = path.join(transcriptsDir, today, "session-malicious_path_attempt.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });

    it("TC-8: handles empty message gracefully", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      await turnStartHandler!({ sessionId: "empty-test" }, {});

      // Empty content
      await messageEndHandler!(
        { message: { role: "user", content: "" } },
        {}
      );

      // Should not crash, but file should exist (session started)
      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(true);
    });
  });

  describe("full conversation flow", () => {
    it("records complete conversation with multiple turns", async () => {
      const turnStartHandler = eventHandlers.get("turn_start");
      const messageEndHandler = eventHandlers.get("message_end");

      // Turn 1
      await turnStartHandler!({ sessionId: "full-conv" }, {});
      await messageEndHandler!({ message: { role: "user", content: "What is OpenClaw?" } }, {});
      await messageEndHandler!({ message: { role: "assistant", content: "OpenClaw is an AI agent framework." } }, {});

      // Turn 2
      await turnStartHandler!({ sessionId: "full-conv" }, {});
      await messageEndHandler!({ message: { role: "user", content: "Does it support TypeScript?" } }, {});
      await messageEndHandler!({ message: { role: "assistant", content: "Yes, it has first-class TypeScript support." } }, {});

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
  });
});
