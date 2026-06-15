// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Summary Extractor (TS)
 *
 * Extracts structured summaries from session messages.
 * Supports LLM extraction (primary) and rule-based fallback.
 */

import type { SessionMessage, SessionSummary, SummaryExtractOptions, LLMEngine } from "./types.js";

const DEFAULT_EXTRACT_TEMPLATE = `请分析以下会话消息，生成结构化摘要。

会话消息：
{messages}

请按以下 JSON 格式输出：
{
  "summary": "会话整体摘要（100-200字）",
  "topics": ["主题1", "主题2"],
  "keyPoints": ["关键决策点1", "关键决策点2"],
  "pendingTasks": ["待办1", "待办2"],
  "contextForNext": "给下个会话的上下文提示（50-100字）",
  "confidence": 0.85
}`;

export class SummaryExtractor {
  private llmEngine?: LLMEngine;
  private options: Required<SummaryExtractOptions>;

  constructor(llmEngine?: LLMEngine, options?: SummaryExtractOptions) {
    this.llmEngine = llmEngine;
    this.options = {
      maxSummaryLength: options?.maxSummaryLength ?? 200,
      minMessageCount: options?.minMessageCount ?? 1,
      llmModel: options?.llmModel ?? "gpt-4",
      customTemplate: options?.customTemplate ?? DEFAULT_EXTRACT_TEMPLATE,
    };
  }

  /** Auto-select mode: LLM if available, rule as fallback. */
  async extract(messages: SessionMessage[], sessionId: string = ""): Promise<SessionSummary> {
    if (messages.length < this.options.minMessageCount) {
      return this.createEmptySummary(sessionId);
    }

    if (this.llmEngine) {
      try {
        return await this.extractWithLLM(messages, sessionId);
      } catch {
        // Fallback to rules on LLM failure
        return this.extractWithRules(messages, sessionId);
      }
    }

    return this.extractWithRules(messages, sessionId);
  }

  /** LLM mode extraction. */
  async extractWithLLM(messages: SessionMessage[], sessionId: string = ""): Promise<SessionSummary> {
    if (!this.llmEngine) {
      return this.extractWithRules(messages, sessionId);
    }

    if (messages.length < this.options.minMessageCount) {
      return this.createEmptySummary(sessionId);
    }

    const truncated = this.truncateMessages(messages);
    const messageText = truncated
      .map((m) => `[${m.role}] ${m.content}`)
      .join("\n");

    const prompt = this.options.customTemplate.replace("{messages}", messageText);

    let lastError: Error | undefined;
    for (let attempt = 0; attempt < 2; attempt++) {
      try {
        const response = await this.llmEngine.chatSimple(prompt);
        const parsed = JSON.parse(response);
        return {
          sessionId,
          summary: (parsed.summary ?? "").slice(0, this.options.maxSummaryLength),
          topics: Array.isArray(parsed.topics) ? parsed.topics : [],
          keyPoints: Array.isArray(parsed.keyPoints) ? parsed.keyPoints : [],
          pendingTasks: Array.isArray(parsed.pendingTasks) ? parsed.pendingTasks : [],
          contextForNext: parsed.contextForNext ?? "",
          timestamp: new Date().toISOString(),
          messageCount: messages.length,
          confidence: typeof parsed.confidence === "number" ? Math.max(0, Math.min(1, parsed.confidence)) : 0.5,
          extractMethod: "llm",
          duration: "",
        };
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
      }
    }

    // Both attempts failed, fallback to rules
    return this.extractWithRules(messages, sessionId);
  }

  /** Rule-based extraction (fallback). */
  extractWithRules(messages: SessionMessage[], sessionId: string = ""): SessionSummary {
    if (messages.length < this.options.minMessageCount) {
      return this.createEmptySummary(sessionId);
    }

    const messageText = messages.map((m) => `${m.role}: ${m.content}`).join("\n");

    // Topics from keyword detection (extended list)
    const keywords = [
      "code", "bug", "fix", "deploy", "test", "api", "auth", "database",
      "config", "error", "performance", "security", "review", "refactor",
      "feature", "release", "ci", "cd", "docker", "kubernetes", "aws",
      "frontend", "backend", "typescript", "python", "react", "node",
      "database", "schema", "migration", "cache", "optimization",
    ];
    const topics = keywords.filter((kw) => messageText.toLowerCase().includes(kw.toLowerCase()));

    // Key points: messages containing decision keywords
    const decisionKeywords = ["决定", "修复", "添加", "修改", "decided", "fixed", "added", "changed"];
    const keyPoints = messages
      .filter((m) => decisionKeywords.some((kw) => m.content.toLowerCase().includes(kw)))
      .map((m) => m.content.slice(0, 100));

    // Pending tasks: messages with TODO-like keywords
    const todoKeywords = ["todo", "需要", "下一步", "待办", "next", "pending"];
    const pendingTasks = messages
      .filter((m) => todoKeywords.some((kw) => m.content.toLowerCase().includes(kw)))
      .map((m) => m.content.slice(0, 100));

    // Summary: first 3 + last 3 messages
    const summaryParts = [
      ...messages.slice(0, 3).map((m) => `${m.role}: ${m.content.slice(0, 100)}`),
      ...(messages.length > 6 ? ["..."] : []),
      ...messages.slice(-3).map((m) => `${m.role}: ${m.content.slice(0, 100)}`),
    ];
    const summary = summaryParts.join("\n").slice(0, this.options.maxSummaryLength);

    // Context: last message content
    const lastMsg = messages[messages.length - 1];
    const contextForNext = lastMsg ? lastMsg.content.slice(0, 200) : "";

    // Confidence based on message count and topic coverage
    const confidence = Math.min(0.5, (messages.length / 20) * 0.3 + (topics.length / 10) * 0.2);

    return {
      sessionId,
      summary,
      topics: topics.slice(0, 5),
      keyPoints: keyPoints.slice(0, 5),
      pendingTasks: pendingTasks.slice(0, 5),
      contextForNext,
      timestamp: new Date().toISOString(),
      messageCount: messages.length,
      confidence: Math.round(confidence * 100) / 100,
      extractMethod: "rule",
      duration: "",
    };
  }

  /** Extract with custom template. */
  async extractWithTemplate(
    messages: SessionMessage[],
    template: string,
    sessionId: string = "",
  ): Promise<SessionSummary> {
    const savedTemplate = this.options.customTemplate;
    this.options.customTemplate = template;
    try {
      return await this.extract(messages, sessionId);
    } finally {
      this.options.customTemplate = savedTemplate;
    }
  }

  /** Truncate messages to prevent overflow. */
  private truncateMessages(messages: SessionMessage[]): SessionMessage[] {
    if (messages.length <= 100) return messages;
    return [
      ...messages.slice(0, 50),
      ...messages.slice(-50),
    ];
  }

  private createEmptySummary(sessionId: string): SessionSummary {
    return {
      sessionId,
      summary: "No messages to summarize.",
      topics: [],
      keyPoints: [],
      pendingTasks: [],
      contextForNext: "",
      timestamp: new Date().toISOString(),
      messageCount: 0,
      confidence: 0,
      extractMethod: "rule",
      duration: "",
    };
  }
}
