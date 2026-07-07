// claw-mem v6.34.0 — ChainVisualizer (TypeScript)
//
// Transforms inference chains into human-readable formats.
// MVP: Text and JSON output only.
//
// Licensed under the Apache License, Version 2.0

import {
  InferenceChain,
  ChainOutput,
  ChainVisualizationOptions,
  InferenceStepType,
} from "./types.js";

/** Default visualization options */
const DEFAULT_VISUALIZATION_OPTIONS: Required<ChainVisualizationOptions> = {
  formats: ["text", "json"],
  showConfidence: true,
  showMemoryRefs: false,
  indentSize: 2,
};

/**
 * ChainVisualizer — renders inference chains to various formats.
 */
export class ChainVisualizer {
  /**
   * Render chain to specified formats.
   */
  render(chain: InferenceChain, options?: Partial<ChainVisualizationOptions>): ChainOutput {
    const opts = { ...DEFAULT_VISUALIZATION_OPTIONS, ...options };

    const output: ChainOutput = {
      text: "",
      json: {},
    };

    for (const format of opts.formats) {
      switch (format) {
        case "text":
          output.text = this.renderText(chain, opts);
          break;
        case "json":
          output.json = this.renderJson(chain, opts);
          break;
        case "mermaid":
          output.mermaid = this.renderMermaid(chain, opts);
          break;
      }
    }

    return output;
  }

  /**
   * Render to text format.
   */
  renderText(
    chain: InferenceChain,
    options?: Partial<ChainVisualizationOptions>
  ): string {
    const opts = { ...DEFAULT_VISUALIZATION_OPTIONS, ...options };
    const lines: string[] = [];
    const indent = " ".repeat(opts.indentSize);

    // Header
    lines.push(`Inference Chain: ${chain.chainId}`);
    lines.push(`Query: ${chain.query}`);
    lines.push(`Confidence: ${chain.confidence.toFixed(2)}`);
    lines.push("");

    // Steps
    lines.push("Steps:");
    for (let i = 0; i < chain.steps.length; i++) {
      const step = chain.steps[i];
      const stepNum = i + 1;

      lines.push(`${indent}[${stepNum}] ${step.type.toUpperCase()}: ${step.content}`);

      if (opts.showConfidence && step.confidence < 1.0) {
        lines.push(`${indent}${indent}Confidence: ${step.confidence.toFixed(2)}`);
      }

      if (opts.showMemoryRefs && step.memories.length > 0) {
        lines.push(`${indent}${indent}Memories: ${step.memories.join(", ")}`);
      }

      lines.push("");
    }

    // Result
    lines.push("Result:");
    for (const knowledge of chain.result) {
      const confStr = opts.showConfidence
        ? ` (${knowledge.confidence.toFixed(2)})`
        : "";
      lines.push(
        `${indent}- ${knowledge.subject} ${knowledge.predicate} ${knowledge.object}${confStr}`
      );
    }

    return lines.join("\n");
  }

  /**
   * Render to JSON format.
   */
  renderJson(
    chain: InferenceChain,
    options?: Partial<ChainVisualizationOptions>
  ): object {
    const opts = { ...DEFAULT_VISUALIZATION_OPTIONS, ...options };

    return {
      chainId: chain.chainId,
      query: chain.query,
      confidence: chain.confidence,
      timestamp: chain.timestamp,
      steps: chain.steps.map((step) => ({
        stepId: step.stepId,
        type: step.type,
        content: step.content,
        confidence: opts.showConfidence ? step.confidence : undefined,
        memories: opts.showMemoryRefs ? step.memories : undefined,
      })),
      result: chain.result.map((k) => ({
        id: k.id,
        type: k.type,
        subject: k.subject,
        predicate: k.predicate,
        object: k.object,
        confidence: opts.showConfidence ? k.confidence : undefined,
      })),
      version: chain.version,
    };
  }

  /**
   * Render to Mermaid flowchart format.
   */
  renderMermaid(
    chain: InferenceChain,
    options?: Partial<ChainVisualizationOptions>
  ): string {
    const opts = { ...DEFAULT_VISUALIZATION_OPTIONS, ...options };
    const lines: string[] = [];

    lines.push("```mermaid");
    lines.push("flowchart TD");

    // Query node
    const queryNode = "Q";
    lines.push(`    ${queryNode}["${this.escapeMermaid(chain.query)}"]`);

    // Step nodes
    let prevNode = queryNode;
    for (let i = 0; i < chain.steps.length; i++) {
      const step = chain.steps[i];
      const node = `S${i + 1}`;
      const label = this.formatStepLabel(step, opts.showConfidence);

      lines.push(`    ${node}["${label}"]`);
      lines.push(`    ${prevNode} --> ${node}`);

      prevNode = node;
    }

    // Result node
    if (chain.result.length > 0) {
      const resultNode = "R";
      const resultLabel = chain.result
        .map((k) => `${k.subject} ${k.predicate} ${k.object}`)
        .join("<br/>");

      lines.push(`    ${resultNode}["${this.escapeMermaid(resultLabel)}"]`);
      lines.push(`    ${prevNode} --> ${resultNode}`);

      // Styles
      lines.push("");
      lines.push(`    style ${queryNode} fill:#e1f5fe`);
      lines.push(`    style ${resultNode} fill:#c8e6c9`);
    }

    lines.push("```");
    return lines.join("\n");
  }

  // ── Private Methods ─────────────────────────────────────────────────────

  private formatStepLabel(
    step: { type: InferenceStepType; content: string; confidence: number },
    showConfidence: boolean
  ): string {
    const typeEmoji: Record<string, string> = {
      premise: "📖",
      rule: "⚙️",
      derivation: "➡️",
      conclusion: "✅",
    };

    const emoji = typeEmoji[step.type] || "•";
    let label = `${emoji} ${step.type.toUpperCase()}: ${step.content}`;

    if (showConfidence && step.confidence < 1.0) {
      label += ` (${(step.confidence * 100).toFixed(0)}%)`;
    }

    return this.escapeMermaid(label);
  }

  private escapeMermaid(text: string): string {
    return text
      .replace(/"/g, "'")
      .replace(/\n/g, "<br/>")
      .replace(/\[/g, "\\[")
      .replace(/\]/g, "\\]");
  }
}