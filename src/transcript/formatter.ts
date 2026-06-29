// claw-mem v6.28.0 — Transcript Formatter
// Formats conversation messages as Markdown

export interface TranscriptEntry {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;  // ISO 8601
}

export interface TranscriptMetadata {
  session: string;    // sessionId
  started: string;    // ISO 8601
  channel: string;    // 'webchat' | 'cli' | 'api'
}

export class TranscriptFormatter {
  /**
   * Format a message entry as Markdown.
   */
  formatMessage(entry: TranscriptEntry): string {
    const time = new Date(entry.timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    const role = entry.role === 'user' ? 'User' : 'Assistant';
    return `## ${time} [${role}]\n\n${entry.content}\n`;
  }

  /**
   * Build file header with metadata.
   */
  buildHeader(metadata: TranscriptMetadata): string {
    return `<!-- session: ${metadata.session} -->
<!-- started: ${metadata.started} -->
<!-- channel: ${metadata.channel} -->

`;
  }

  /**
   * Format full transcript file.
   */
  formatTranscript(metadata: TranscriptMetadata, entries: TranscriptEntry[]): string {
    const header = this.buildHeader(metadata);
    const body = entries.map((e) => this.formatMessage(e)).join('\n');
    return header + body;
  }
}
