// Copyright 2026 Peter Cheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/**
 * LLM Extractors - LLM-driven fact and concept extractors
 *
 * Supports:
 * - LLM-driven intelligent extraction
 * - Rule-based fallback extraction
 * - Dummy extractor (for testing)
 */

/** Minimal interface for a generic LLM client. */
export interface LLMClient {
  generate(prompt: string): string;
  chat?(prompt: string): string;
}

export abstract class BaseExtractor {
  abstract extractFacts(text: string): string[];
  abstract extractConcepts(text: string): string[];
}

export class DummyExtractor extends BaseExtractor {
  extractFacts(_text: string): string[] {
    return [];
  }

  extractConcepts(_text: string): string[] {
    return [];
  }
}

export class LLMExtractor extends BaseExtractor {
  private llm: LLMClient | null;

  constructor(llmClient?: LLMClient | null) {
    super();
    this.llm = llmClient ?? null;
  }

  extractFacts(text: string): string[] {
    if (!this.llm) {
      return this.extractFactsRuleBased(text);
    }
    try {
      const prompt = this.buildFactsPrompt(text);
      const response = this.callLLM(prompt);
      return this.parseLines(response);
    } catch {
      return this.extractFactsRuleBased(text);
    }
  }

  extractConcepts(text: string): string[] {
    if (!this.llm) {
      return this.extractConceptsRuleBased(text);
    }
    try {
      const prompt = this.buildConceptsPrompt(text);
      const response = this.callLLM(prompt);
      return this.parseLines(response);
    } catch {
      return this.extractConceptsRuleBased(text);
    }
  }

  generateReflection(nodes: { content: string }[]): string {
    if (!this.llm) {
      return this.generateReflectionRuleBased(nodes);
    }
    try {
      const prompt = this.buildReflectionPrompt(nodes);
      return this.callLLM(prompt);
    } catch {
      return this.generateReflectionRuleBased(nodes);
    }
  }

  private callLLM(prompt: string): string {
    if (!this.llm) {
      throw new Error("No LLM client available");
    }
    if (typeof (this.llm as any).generate === "function") {
      return (this.llm as any).generate(prompt);
    } else if (typeof (this.llm as any).chat === "function") {
      return (this.llm as any).chat(prompt);
    } else {
      throw new Error("LLM client must have 'generate' or 'chat' method");
    }
  }

  private parseLines(response: string): string[] {
    return response
      .trim()
      .split("\n")
      .map((line) => line.trim().replace(/^[-*]\s*/, "").trim())
      .filter((line) => line.length > 0);
  }

  private buildFactsPrompt(text: string): string {
    return `Extract key facts from the following text.

Requirements:
1. One fact per line
2. Only extract objective facts, do not infer
3. Keep it concise

Text:
${text}

Fact list:`;
  }

  private buildConceptsPrompt(text: string): string {
    return `Extract core concepts from the following text.

Requirements:
1. One concept per line
2. Extract keywords, topics, entities
3. Keep it concise

Text:
${text}

Concept list:`;
  }

  private buildReflectionPrompt(nodes: { content: string }[]): string {
    const contents = nodes
      .slice(0, 10)
      .map((n) => `- ${n.content}`)
      .join("\n");
    return `Generate a brief reflection summary based on the following memory nodes:

${contents}

Reflection:`;
  }

  /** Rule-based fact extraction (fallback). Split text by sentences. */
  extractFactsRuleBased(text: string): string[] {
    const sentences = text.split(/[.!?！。？\n]+/);
    const facts: string[] = [];
    for (const s of sentences) {
      const trimmed = s.trim();
      if (trimmed.length > 5 && trimmed.length < 200) {
        facts.push(trimmed);
      }
    }
    return facts.slice(0, 5);
  }

  /** Rule-based concept extraction (fallback). */
  extractConceptsRuleBased(text: string): string[] {
    const chinese = text.match(/[\u4e00-\u9fa5]{2,4}/g) ?? [];
    const english = text.match(/[a-zA-Z]{3,}/g) ?? [];
    const seen = new Set<string>();
    const concepts: string[] = [];
    for (const w of [...chinese, ...english]) {
      if (!seen.has(w)) {
        seen.add(w);
        concepts.push(w);
      }
    }
    return concepts.slice(0, 10);
  }

  /** Rule-based reflection generation (fallback). */
  generateReflectionRuleBased(nodes: { content: string }[]): string {
    if (nodes.length === 0) {
      return "Not enough information to generate reflection";
    }
    const latest = nodes[nodes.length - 1];
    return `Review: ${latest.content.slice(0, 100)}`;
  }
}

export class KeywordExtractor extends BaseExtractor {
  private stopwords: Set<string>;

  constructor() {
    super();
    this.stopwords = new Set([
      "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
      "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
      "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
    ]);
  }

  extractFacts(text: string): string[] {
    return new LLMExtractor().extractFactsRuleBased(text);
  }

  extractConcepts(text: string): string[] {
    const chinese = text.match(/[\u4e00-\u9fa5]{2,4}/g) ?? [];
    const english = text.match(/[a-zA-Z]{3,}/g) ?? [];
    const seen = new Set<string>();
    const concepts: string[] = [];
    for (const w of [...chinese, ...english]) {
      if (!this.stopwords.has(w) && !seen.has(w)) {
        seen.add(w);
        concepts.push(w);
      }
    }
    return concepts.slice(0, 10);
  }
}
