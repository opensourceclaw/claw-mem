// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/** claw-mem v5.0.0 — Session Summary (TS) */

export interface SessionSummary {
  sessionId: string;
  summary: string;
  topics: string[];
  keyPoints: string[];
  pendingTasks: string[];
  timestamp: string;
  messageCount: number;
  duration: string;
}

export interface SummaryOptions {
  maxSummaryLength?: number;
  minMessageCount?: number;
}

export function extractSummary(
  messages: Array<{ role: string; content: string }>,
  sessionId = "",
  opts: SummaryOptions = {},
): SessionSummary {
  const maxLen = opts.maxSummaryLength ?? 200;
  const minMsg = opts.minMessageCount ?? 1;

  if (messages.length < minMsg) {
    return createEmptySummary(sessionId);
  }

  // Simple extraction: combine first and last few messages
  const content = messages.map((m) => `${m.role}: ${m.content}`).join("\n");

  // Topics from keyword detection
  const keywords = [
    "code", "bug", "fix", "deploy", "test", "API", "auth", "database",
    "config", "error", "performance", "security", "review", "refactor",
  ];
  const topics = keywords.filter((kw) => content.toLowerCase().includes(kw.toLowerCase()));

  // Key points from first and last messages
  const keyPoints: string[] = [];
  if (messages.length > 0) keyPoints.push(messages[0].content.slice(0, 100));
  if (messages.length > 1) keyPoints.push(messages[messages.length - 1].content.slice(0, 100));

  return {
    sessionId,
    summary: topics.length
      ? `Session covered: ${topics.slice(0, 5).join(", ")}`
      : content.slice(0, maxLen),
    topics: topics.slice(0, 5),
    keyPoints,
    pendingTasks: [],
    timestamp: new Date().toISOString(),
    messageCount: messages.length,
    duration: "",
  };
}

function createEmptySummary(sessionId: string): SessionSummary {
  return {
    sessionId,
    summary: "No messages to summarize.",
    topics: [],
    keyPoints: [],
    pendingTasks: [],
    timestamp: new Date().toISOString(),
    messageCount: 0,
    duration: "",
  };
}
