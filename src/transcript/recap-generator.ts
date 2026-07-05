// claw-mem v6.33.0 — Recap Generator
// Generates user-friendly 40-word session summaries

import type { TranscriptEntry } from './formatter.js';

/**
 * Recap summary for a session
 */
export interface Recap {
  /** What we were doing in this session */
  whatWereWeDoing: string;
  /** What is the next step */
  whatIsNext: string;
  /** When the recap was generated */
  timestamp: number;
  /** Session identifier */
  sessionId: string;
}

/**
 * Configuration for RecapGenerator
 */
export interface RecapGeneratorConfig {
  /** Maximum words in summary (default: 40) */
  maxWords?: number;
  /** Number of recent messages to analyze (default: 10) */
  recentMessageCount?: number;
}

const DEFAULT_CONFIG: Required<RecapGeneratorConfig> = {
  maxWords: 40,
  recentMessageCount: 10,
};

/**
 * Generates user-friendly session summaries
 */
export class RecapGenerator {
  private config: Required<RecapGeneratorConfig>;

  constructor(config?: RecapGeneratorConfig) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Generate a recap from transcript entries
   */
  async generate(sessionId: string, entries: TranscriptEntry[]): Promise<Recap> {
    return this.generateSync(sessionId, entries);
  }

  /**
   * Generate a recap synchronously from transcript entries
   * v6.33.0: Added for use in synchronous contexts like endSession.
   */
  generateSync(sessionId: string, entries: TranscriptEntry[]): Recap {
    if (entries.length === 0) {
      return {
        whatWereWeDoing: "No activity in this session",
        whatIsNext: "Start a new conversation",
        timestamp: Date.now(),
        sessionId,
      };
    }

    // Get recent entries
    const recentEntries = entries.slice(-this.config.recentMessageCount);

    // Extract what we were doing
    const whatWereWeDoing = this.extractWhatWeWereDoing(recentEntries);

    // Extract what is next
    const whatIsNext = this.extractWhatIsNext(recentEntries);

    return {
      whatWereWeDoing,
      whatIsNext,
      timestamp: Date.now(),
      sessionId,
    };
  }

  /**
   * Extract "what we were doing" from recent messages
   */
  private extractWhatWeWereDoing(entries: TranscriptEntry[]): string {
    // Find user messages to understand intent
    const userMessages = entries.filter(e => e.role === 'user');

    if (userMessages.length === 0) {
      return "Reviewing conversation";
    }

    // Get the last user message as the main activity
    const lastUserMessage = userMessages[userMessages.length - 1].content;
    return this.truncateToMaxWords(lastUserMessage);
  }

  /**
   * Extract "what is next" from recent messages
   */
  private extractWhatIsNext(entries: TranscriptEntry[]): string {
    // Find assistant messages for next steps
    const assistantMessages = entries.filter(e => e.role === 'assistant');

    if (assistantMessages.length === 0) {
      return "Continue the conversation";
    }

    // Look for action items or next steps in the last assistant message
    const lastAssistantMessage = assistantMessages[assistantMessages.length - 1].content;

    // Check for explicit next steps
    const nextStepMatch = lastAssistantMessage.match(/(?:next step|todo|pending|remaining|still need)[:\s]+([^\n]+)/i);
    if (nextStepMatch) {
      return this.truncateToMaxWords(nextStepMatch[1]);
    }

    // Default to continuing
    return "Continue with current task";
  }

  /**
   * Truncate text to max words
   */
  private truncateToMaxWords(text: string): string {
    const words = text.split(/\s+/);
    if (words.length <= this.config.maxWords) {
      return text;
    }
    return words.slice(0, this.config.maxWords).join(' ') + '...';
  }
}
