// Copyright 2026 Peter Cheng
// claw-mem v6.32.1 — Real Hook Integration Tests
// Tests lazy session detection by importing actual plugin.ts and invoking real handlers

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

describe("Real Hook Integration Tests", () => {
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

  describe("user_message hook", () => {
    it("TC-1: creates transcript file on first user_message with sessionKey", async () => {
      const handler = eventHandlers.get("user_message");
      expect(handler).toBeDefined();

      await handler!(
        { content: "Hello, world!", sessionKey: "test-session-123", channel: "webchat" },
        {}
      );

      // Verify transcript file was created
      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-test-session-123.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);

      // Verify content
      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("test-session-123");
      expect(content).toContain("Hello, world!");
      expect(content).toContain("[User]");
    });

    it("TC-2: does not restart session on same sessionKey", async () => {
      const handler = eventHandlers.get("user_message");

      // First message
      await handler!(
        { content: "First message", sessionKey: "same-session" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-same-session.md");

      // Get file modification time
      const stat1 = fs.statSync(transcriptPath);

      // Wait a bit and send second message
      await new Promise(r => setTimeout(r, 10));

      await handler!(
        { content: "Second message", sessionKey: "same-session" },
        {}
      );

      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("First message");
      expect(content).toContain("Second message");

      // File should still exist (not recreated)
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });

    it("TC-3: new sessionKey triggers new transcript file", async () => {
      const handler = eventHandlers.get("user_message");

      // First session
      await handler!(
        { content: "Session A content", sessionKey: "session-a" },
        {}
      );

      // Second session
      await handler!(
        { content: "Session B content", sessionKey: "session-b" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const pathA = path.join(transcriptsDir, today, "session-session-a.md");
      const pathB = path.join(transcriptsDir, today, "session-session-b.md");

      expect(fs.existsSync(pathA)).toBe(true);
      expect(fs.existsSync(pathB)).toBe(true);

      const contentA = fs.readFileSync(pathA, "utf-8");
      const contentB = fs.readFileSync(pathB, "utf-8");

      expect(contentA).toContain("Session A content");
      expect(contentA).not.toContain("Session B content");
      expect(contentB).toContain("Session B content");
    });

    it("TC-4: missing sessionKey does not create transcript file", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        { content: "No session key" },
        {}
      );

      // transcripts directory exists (created by TsBridge constructor)
      // but no date subdirectory should be created
      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(false);
    });

    it("TC-5: uses sessionId as fallback when sessionKey missing", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        { content: "Using sessionId", sessionId: "fallback-id" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-fallback-id.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);

      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("Using sessionId");
    });

    it("TC-6: sanitizeSessionKey removes path separators", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        { content: "Test path sanitization", sessionKey: "malicious/path/attempt" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      // Should be sanitized to "malicious_path_attempt"
      const transcriptPath = path.join(transcriptsDir, today, "session-malicious_path_attempt.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });

    it("TC-7: sanitizes backslashes in sessionKey", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        { content: "Test backslash", sessionKey: "back\\slash\\key" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-back_slash_key.md");
      expect(fs.existsSync(transcriptPath)).toBe(true);
    });
  });

  describe("content extraction fallbacks", () => {
    it("extracts from event.text when content missing", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        { text: "Text field content", sessionKey: "text-field-test" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-text-field-test.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("Text field content");
    });

    it("extracts from event.messages array", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        {
          messages: [{ role: "user", content: "Array message content" }],
          sessionKey: "array-content-test"
        },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-array-content-test.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("Array message content");
    });

    it("extracts from nested message.content", async () => {
      const handler = eventHandlers.get("user_message");

      await handler!(
        {
          message: { content: "Nested content" },
          sessionKey: "nested-content-test"
        },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-nested-content-test.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("Nested content");
    });
  });

  describe("assistant_message hook", () => {
    it("appends to existing session from user_message", async () => {
      const userHandler = eventHandlers.get("user_message");
      const assistantHandler = eventHandlers.get("assistant_message");

      // User message first (starts session)
      await userHandler!(
        { content: "User question", sessionKey: "conv-session" },
        {}
      );

      // Assistant message (should append)
      await assistantHandler!(
        { content: "Assistant response", sessionKey: "conv-session" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-conv-session.md");
      const content = fs.readFileSync(transcriptPath, "utf-8");

      expect(content).toContain("User question");
      expect(content).toContain("[User]");
      expect(content).toContain("Assistant response");
      expect(content).toContain("[Assistant]");
    });

    it("defensively starts session when assistant_message fires first", async () => {
      const assistantHandler = eventHandlers.get("assistant_message");

      // Assistant message fires first (edge case)
      await assistantHandler!(
        { content: "First response", sessionKey: "defensive-session" },
        {}
      );

      const today = new Date().toISOString().slice(0, 10);
      const transcriptPath = path.join(transcriptsDir, today, "session-defensive-session.md");

      expect(fs.existsSync(transcriptPath)).toBe(true);
      const content = fs.readFileSync(transcriptPath, "utf-8");
      expect(content).toContain("First response");
    });

    it("does nothing without sessionKey and no active session", async () => {
      const assistantHandler = eventHandlers.get("assistant_message");

      await assistantHandler!(
        { content: "Orphan message" },
        {}
      );

      // transcripts directory exists (created by TsBridge constructor)
      // but no date subdirectory should be created
      const today = new Date().toISOString().slice(0, 10);
      const dateDir = path.join(transcriptsDir, today);
      expect(fs.existsSync(dateDir)).toBe(false);
    });
  });

  describe("full conversation flow", () => {
    it("records complete conversation with multiple turns", async () => {
      const userHandler = eventHandlers.get("user_message");
      const assistantHandler = eventHandlers.get("assistant_message");

      // Turn 1
      await userHandler!({ content: "What is OpenClaw?", sessionKey: "full-conv" }, {});
      await assistantHandler!({ content: "OpenClaw is an AI agent framework.", sessionKey: "full-conv" }, {});

      // Turn 2
      await userHandler!({ content: "Does it support TypeScript?", sessionKey: "full-conv" }, {});
      await assistantHandler!({ content: "Yes, it has first-class TypeScript support.", sessionKey: "full-conv" }, {});

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
