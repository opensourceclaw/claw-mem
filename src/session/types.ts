// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Session Continuity Type Definitions (TS)
 */

// ── Session Summary ──────────────────────────────────────────────

/** 会话摘要 */
export interface SessionSummary {
  sessionId: string;
  summary: string;
  topics: string[];
  keyPoints: string[];
  pendingTasks: string[];
  contextForNext: string;
  timestamp: string;
  messageCount: number;
  confidence: number;
  extractMethod: "llm" | "rule";
  duration: string;
}

/** 摘要提取选项 */
export interface SummaryExtractOptions {
  maxSummaryLength?: number;
  minMessageCount?: number;
  llmModel?: string;
  customTemplate?: string;
}

// ── Checkpoint ───────────────────────────────────────────────────

/** 会话消息 */
export interface SessionMessage {
  role: string;
  content: string;
  timestamp: string;
}

/** 会话状态 */
export interface SessionState {
  sessionId: string;
  status: "active" | "closed" | "recovered";
  lastActivity: string;
  topic: string;
  tags: string[];
  metadata: Record<string, unknown>;
}

/** Checkpoint 数据 */
export interface CheckpointData {
  checkpointId: string;
  sessionId: string;
  timestamp: string;
  status: "created" | "saved" | "restored";
  messages: SessionMessage[];
  sessionState: SessionState;
  summary: string;
  metadata: {
    messageCount: number;
    tokenCount: number;
    lastTopic: string;
  };
}

/** Checkpoint 管理器选项 */
export interface CheckpointOptions {
  maxMessages?: number;
  intervalMinutes?: number;
  maxCheckpoints?: number;
  storageDir?: string;
}

// ── Tags ─────────────────────────────────────────────────────────

/** 统一标签常量 */
export const SESSION_TAGS = {
  SUMMARY: "session_summary",
  CONTINUITY: "session_continuity",
  PENDING: "session_pending",
  CONTEXT: "session_context",
} as const;

export type SessionTag = (typeof SESSION_TAGS)[keyof typeof SESSION_TAGS];

// ── Recovery ─────────────────────────────────────────────────────

/** 自动恢复配置 */
export interface RecoveryConfig {
  enabled: boolean;
  maxAgeHours: number;
  maxSessions: number;
  injectMode: "bootstrap" | "ingest";
}

/** 会话信息 */
export interface SessionInfo {
  sessionId: string;
  lastActivity: string;
  messageCount: number;
  topic: string;
  tags: string[];
}

/** 恢复结果 */
export interface RecoveryResult {
  success: boolean;
  restoredSessions: number;
  injectedContext: string;
  errors: string[];
}

/** 会话连续性总配置 */
export interface SessionContinuityConfig {
  summary: {
    enabled: boolean;
    method: "llm" | "rule" | "auto";
    maxMessages: number;
    llmModel?: string;
  };
  checkpoint: {
    enabled: boolean;
    maxMessages: number;
    intervalMinutes: number;
    maxCheckpoints: number;
  };
  recovery: {
    enabled: boolean;
    maxAgeHours: number;
    maxSessions: number;
    injectMode: "bootstrap" | "ingest";
  };
  tags: {
    prefix: string;
  };
}

/** LLM 引擎接口 */
export interface LLMEngine {
  model: string;
  chat(
    messages: Array<{ role: string; content: string }>,
    opts?: Record<string, unknown>,
  ): Promise<{ content: string; model: string }>;
  chatSimple(prompt: string, opts?: Record<string, unknown>): Promise<string>;
}
