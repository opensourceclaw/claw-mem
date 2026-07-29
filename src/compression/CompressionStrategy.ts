/**
 * claw-mem v6.43.0 — Compression Strategies
 */

export interface CompressionStrategy {
  name: "truncate" | "summarize" | "compress";
  compress(content: string, targetTokens: number): Promise<string>;
  estimateResult(content: string, targetTokens: number): { estimatedTokens: number; quality: "high" | "medium" | "low" };
}

/** Keep head 10% + newest content up to target tokens. */
export class TruncateStrategy implements CompressionStrategy {
  name = "truncate" as const;

  async compress(content: string, targetTokens: number): Promise<string> {
    const lines = content.split("\n");
    const targetChars = targetTokens * 4;

    const headCount = Math.max(1, Math.floor(lines.length * 0.1));
    const head = lines.slice(0, headCount);

    const tail: string[] = [];
    let keptChars = 0;
    for (let i = lines.length - 1; i >= headCount; i--) {
      keptChars += lines[i].length + 1;
      if (keptChars >= targetChars * 0.9) break;
      tail.unshift(lines[i]);
    }

    return [...head, "", "... (truncated) ...", "", ...tail].join("\n");
  }

  estimateResult(_content: string, targetTokens: number): { estimatedTokens: number; quality: "low" } {
    return { estimatedTokens: targetTokens, quality: "low" };
  }
}

/** Simple keyword-based summarization. */
export class SummarizeStrategy implements CompressionStrategy {
  name = "summarize" as const;
  private method: "simple" | "llm";

  constructor(method: "simple" | "llm" = "simple") {
    this.method = method;
  }

  async compress(content: string, _targetTokens: number): Promise<string> {
    if (this.method === "simple") return this.simpleSummarize(content);
    return content; // LLM path: TODO
  }

  private simpleSummarize(content: string): string {
    const lines = content.split("\n");
    const keyPatterns = /```|#{1,3}\s|\*\*|important|critical|fix|release|version|task|pipeline/i;
    const keyLines = lines.filter(l => keyPatterns.test(l));
    if (keyLines.length === 0) {
      // Return last 20% of lines as fallback
      const tail = Math.max(5, Math.floor(lines.length * 0.2));
      return lines.slice(-tail).join("\n");
    }
    return keyLines.join("\n");
  }

  estimateResult(content: string, targetTokens: number): { estimatedTokens: number; quality: "medium" } {
    return { estimatedTokens: Math.min(targetTokens, Math.ceil(content.length / 8)), quality: "medium" };
  }
}
