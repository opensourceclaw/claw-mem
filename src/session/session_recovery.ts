// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Session Recovery (TS)
 *
 * Auto-recovery of interrupted sessions using checkpoints and summaries.
 * Finds unclosed sessions, loads checkpoints, and injects context.
 */

import type { RecoveryConfig, RecoveryResult, SessionInfo } from "./types.js";
import { CheckpointManager } from "./checkpoint_manager.js";
import { SummaryExtractor } from "./summary_extractor.js";

export class SessionRecovery {
  private config: RecoveryConfig;
  private checkpointManager: CheckpointManager;
  private summaryExtractor: SummaryExtractor;

  constructor(
    config: RecoveryConfig,
    checkpointManager: CheckpointManager,
    summaryExtractor: SummaryExtractor,
  ) {
    this.config = config;
    this.checkpointManager = checkpointManager;
    this.summaryExtractor = summaryExtractor;
  }

  /** Recover the most recent session. */
  async recoverLastSession(): Promise<RecoveryResult> {
    const errors: string[] = [];

    try {
      const sessions = await this.findUnclosedSessions();

      if (sessions.length === 0) {
        return {
          success: true,
          restoredSessions: 0,
          injectedContext: "",
          errors: [],
        };
      }

      const session = sessions[0]; // Most recent
      const checkpoints = this.checkpointManager.listCheckpoints(session.sessionId);

      if (checkpoints.length === 0) {
        // No checkpoint — build context from summary if available
        const context = this.buildSummaryOnlyContext(session);
        if (context) {
          await this.injectContext(session.sessionId, context);
          return {
            success: true,
            restoredSessions: 1,
            injectedContext: context,
            errors: [],
          };
        }
        return {
          success: true,
          restoredSessions: 0,
          injectedContext: "",
          errors: ["No checkpoint or summary available"],
        };
      }

      // Use latest checkpoint
      const latest = checkpoints[checkpoints.length - 1];
      const context = this.buildRecoveryContext(session, latest.summary);
      await this.injectContext(session.sessionId, context);

      return {
        success: true,
        restoredSessions: 1,
        injectedContext: context,
        errors: [],
      };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      errors.push(msg);
      return {
        success: false,
        restoredSessions: 0,
        injectedContext: "",
        errors,
      };
    }
  }

  /** Find unclosed sessions from stored data. */
  async findUnclosedSessions(): Promise<SessionInfo[]> {
    const sessions: SessionInfo[] = [];
    const cutoff = Date.now() - this.config.maxAgeHours * 60 * 60 * 1000;

    const allCheckpoints = this.checkpointManager.listCheckpoints();

    // Deduplicate by sessionId, take latest checkpoint per session
    const sessionMap = new Map<string, SessionInfo>();

    for (const cp of allCheckpoints) {
      const cpTime = new Date(cp.timestamp).getTime();
      if (cpTime < cutoff) continue; // Expired

      const existing = sessionMap.get(cp.sessionId);
      if (!existing || new Date(cp.timestamp).getTime() > new Date(existing.lastActivity).getTime()) {
        sessionMap.set(cp.sessionId, {
          sessionId: cp.sessionId,
          lastActivity: cp.timestamp,
          messageCount: cp.metadata.messageCount,
          topic: cp.metadata.lastTopic,
          tags: cp.sessionState.tags,
        });
      }
    }

    // Sort by lastActivity descending, limit to maxSessions
    const sorted = [...sessionMap.values()]
      .sort((a, b) => new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime());

    for (let i = 0; i < Math.min(this.config.maxSessions, sorted.length); i++) {
      sessions.push(sorted[i]);
    }

    return sessions;
  }

  /** Inject context into current session. */
  async injectContext(sessionId: string, context: string): Promise<boolean> {
    if (!context) return false;

    try {
      if (this.config.injectMode === "bootstrap") {
        // Context injected via system prompt (placeholder — actual injection
        // depends on the host environment, e.g. bridge.ts or context_injection.ts)
        return true;
      }

      // ingest mode: context will be written as system message
      // (delegated to the caller via returned context string)
      return true;
    } catch {
      return false;
    }
  }

  /** Build recovery context string from checkpoint and summary. */
  private buildRecoveryContext(session: SessionInfo, summary: string): string {
    return `【会话恢复】上一会话（${session.sessionId}）于 ${session.lastActivity} 结束。
摘要：${summary || "无摘要"}
主题：${session.topic || "无"}
消息数：${session.messageCount}`;
  }

  /** Build context from session info only (no checkpoint). */
  private buildSummaryOnlyContext(session: SessionInfo): string {
    if (!session.topic && session.messageCount === 0) return "";
    return `【会话恢复】检测到未完成的会话（${session.sessionId}），最后活跃于 ${session.lastActivity}。
主题：${session.topic || "无"}
消息数：${session.messageCount}`;
  }
}
