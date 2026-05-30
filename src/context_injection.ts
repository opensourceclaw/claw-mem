// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v5.0.0 — Context Injection (TypeScript)
 *
 * Formats retrieved memories for prompt injection.
 */

export interface InjectedContext {
  formattedText: string;
  memoryCount: number;
  totalLength: number;
  layersIncluded: string[];
  truncated: boolean;
  warnings: string[];
}

export class ContextFormatter {
  static readonly DEFAULT_MAX_LENGTH = 4000;

  format(memories: Array<{ content: string; memory_type?: string; tags?: string[] }>,
         maxLength: number = ContextFormatter.DEFAULT_MAX_LENGTH): string {
    if (!memories.length) return "";
    const lines: string[] = [];
    let total = 0;

    for (const mem of memories) {
      const content = mem.content ?? "";
      if (!content) continue;
      const prefix = mem.memory_type
        ? `[${mem.memory_type.toUpperCase()}] `
        : "";
      const line = prefix + content.replace(/\n/g, " ");
      if (total + line.length > maxLength) break;
      lines.push(line);
      total += line.length;
    }
    return lines.join("\n");
  }
}

export class ContextInjector {
  formatMemories(memories: Array<Record<string, unknown>>,
                 maxTokens = 2000): InjectedContext {
    const formatter = new ContextFormatter();
    const maxLen = maxTokens * 4; // rough 4 chars/token
    const text = formatter.format(memories as Array<{ content: string }>, maxLen);
    const truncated = text.length < memories.reduce((s, m) =>
      s + String(m.content ?? "").length, 0);
    return {
      formattedText: text,
      memoryCount: memories.length,
      totalLength: text.length,
      layersIncluded: [],
      truncated,
      warnings: truncated ? ["Context truncated to fit token budget"] : [],
    };
  }
}

export function formatMemoryContext(memories: Array<Record<string, unknown>>): string {
  return new ContextFormatter().format(memories as Array<{ content: string }>);
}

export function injectMemoriesToPrompt(
  memories: Array<Record<string, unknown>>,
  maxTokens?: number,
): string {
  return new ContextInjector().formatMemories(memories, maxTokens).formattedText;
}
