import { describe, it, expect, vi } from "vitest";
import { SummaryExtractor } from "../../src/session/summary_extractor.js";
import type { SessionMessage, LLMEngine } from "../../src/session/types.js";

function makeMessages(count: number): SessionMessage[] {
  const msgs: SessionMessage[] = [];
  for (let i = 0; i < count; i++) {
    msgs.push({
      role: i % 2 === 0 ? "user" : "assistant",
      content: `Message number ${i}`,
      timestamp: new Date().toISOString(),
    });
  }
  return msgs;
}

describe("SummaryExtractor", () => {
  describe("rule-based extraction", () => {
    it("should extract summary from messages using rules", () => {
      const extractor = new SummaryExtractor();
      const messages = makeMessages(10);
      const result = extractor.extractWithRules(messages, "sess_001");

      expect(result.sessionId).toBe("sess_001");
      expect(result.summary).toBeTruthy();
      expect(result.messageCount).toBe(10);
      expect(result.extractMethod).toBe("rule");
      expect(result.confidence).toBeGreaterThanOrEqual(0);
      expect(result.confidence).toBeLessThanOrEqual(1);
    });

    it("should return empty summary for empty messages", () => {
      const extractor = new SummaryExtractor(undefined, { minMessageCount: 1 });
      const result = extractor.extractWithRules([], "sess_001");

      expect(result.messageCount).toBe(0);
      expect(result.summary).toBe("No messages to summarize.");
      expect(result.confidence).toBe(0);
    });

    it("should return empty summary when messages below min count", () => {
      const extractor = new SummaryExtractor(undefined, { minMessageCount: 5 });
      const result = extractor.extractWithRules(makeMessages(2), "sess_001");

      expect(result.messageCount).toBe(0);
      expect(result.confidence).toBe(0);
    });

    it("should detect keywords in messages", () => {
      const extractor = new SummaryExtractor();
      const messages: SessionMessage[] = [
        { role: "user", content: "We need to fix the bug in the API", timestamp: new Date().toISOString() },
        { role: "assistant", content: "Found the issue in the database config", timestamp: new Date().toISOString() },
      ];
      const result = extractor.extractWithRules(messages, "sess_002");

      expect(result.topics.length).toBeGreaterThan(0);
      expect(result.topics.some((t) => t.toLowerCase().includes("bug") || t.includes("api"))).toBe(true);
    });

    it("should handle mixed CJK and English messages", () => {
      const extractor = new SummaryExtractor();
      const messages: SessionMessage[] = [
        { role: "user", content: "修复了数据库连接池的bug", timestamp: new Date().toISOString() },
        { role: "assistant", content: "Good, the fix is deployed", timestamp: new Date().toISOString() },
      ];
      const result = extractor.extractWithRules(messages);

      expect(result.summary).toBeTruthy();
      expect(result.messageCount).toBe(2);
    });
  });

  describe("LLM extraction", () => {
    it("should fallback to rules when LLM fails", async () => {
      const mockLLM: LLMEngine = {
        model: "test",
        chat: vi.fn().mockRejectedValue(new Error("LLM unavailable")),
        chatSimple: vi.fn().mockRejectedValue(new Error("LLM unavailable")),
      };
      const extractor = new SummaryExtractor(mockLLM);
      const result = await extractor.extract(makeMessages(5), "sess_003");

      expect(result.extractMethod).toBe("rule");
      expect(result.messageCount).toBe(5);
    });

    it("should use LLM when available", async () => {
      const mockLLM: LLMEngine = {
        model: "test",
        chat: vi.fn(),
        chatSimple: vi.fn().mockResolvedValue(JSON.stringify({
          summary: "Test summary",
          topics: ["topic1"],
          keyPoints: ["key point"],
          pendingTasks: [],
          contextForNext: "context hint",
          confidence: 0.9,
        })),
      };
      const extractor = new SummaryExtractor(mockLLM);
      const result = await extractor.extract(makeMessages(5), "sess_004");

      expect(result.extractMethod).toBe("llm");
      expect(result.summary).toBe("Test summary");
      expect(result.topics).toContain("topic1");
      expect(result.confidence).toBe(0.9);
    });

    it("should use rules when no LLM engine provided", async () => {
      const extractor = new SummaryExtractor();
      const result = await extractor.extract(makeMessages(5), "sess_005");

      expect(result.extractMethod).toBe("rule");
    });
  });

  describe("custom template", () => {
    it("should use custom template for extraction", async () => {
      const mockLLM: LLMEngine = {
        model: "test",
        chat: vi.fn(),
        chatSimple: vi.fn().mockResolvedValue(JSON.stringify({
          summary: "Custom summary",
          topics: [],
          keyPoints: [],
          pendingTasks: [],
          contextForNext: "",
          confidence: 0.5,
        })),
      };
      const extractor = new SummaryExtractor(mockLLM);
      const result = await extractor.extractWithTemplate(
        makeMessages(3),
        "Custom template {messages}",
        "sess_006",
      );

      expect(result.summary).toBe("Custom summary");
    });
  });
});
