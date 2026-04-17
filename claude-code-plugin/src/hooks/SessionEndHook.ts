import { ClawMemBridge } from '../bridge.js';

export interface SessionEndContext {
  duration: number;
  messageCount: number;
  toolUseCount: number;
  errors?: string[];
}

export interface SessionEndResult {
  summarized: boolean;
  memoriesCreated?: number;
}

/**
 * SessionEndHook: Summarize session and store episodic memory
 * 
 * This hook runs at the end of a Claude Code session.
 * It creates a session summary and stores it as episodic memory.
 */
export async function SessionEndHook(
  context: SessionEndContext
): Promise<SessionEndResult> {
  const bridge = new ClawMemBridge();

  // Create session summary
  const summary = createSessionSummary(context);

  // Store as episodic memory
  const result = await bridge.store({
    content: summary,
    layer: 'episodic',
    metadata: {
      type: 'session_summary',
      duration: context.duration,
      messageCount: context.messageCount,
      toolUseCount: context.toolUseCount,
      errorCount: context.errors?.length || 0,
      timestamp: new Date().toISOString()
    }
  });

  return {
    summarized: result.success,
    memoriesCreated: result.success ? 1 : 0
  };
}

/**
 * Create a session summary
 */
function createSessionSummary(context: SessionEndContext): string {
  const duration = Math.round(context.duration / 60000); // minutes
  const parts: string[] = [];

  parts.push(`Claude Code session ended after ${duration} minutes`);
  parts.push(`${context.messageCount} messages exchanged`);
  parts.push(`${context.toolUseCount} tools used`);

  if (context.errors && context.errors.length > 0) {
    parts.push(`${context.errors.length} errors encountered`);
  }

  return parts.join('. ');
}
