// claw-mem v6.34.0 — ContradictionDetector (TypeScript)
//
// Detects contradictions in stored memories.
// MVP: Direct contradiction detection only.
//
// Licensed under the Apache License, Version 2.0

import * as crypto from "crypto";
import {
  ContradictionReport,
  ContradictionType,
  ContradictionSeverity,
  ConflictItem,
  ContradictionSuggestion,
} from "./types.js";
import type { MemoryForInference, MemoryId } from "./engine.js";

/** Attribute value extracted from memory */
interface AttributeValue {
  raw: string;
  normalized: string;
  memoryId: MemoryId;
  content: string;
  confidence: number;
  timestamp: number;
}

/**
 * ContradictionDetector — detects contradictions in memories.
 */
export class ContradictionDetector {
  /**
   * Detect direct contradictions.
   * A direct contradiction occurs when two memories claim different values
   * for the same attribute of the same entity.
   */
  detectDirect(memories: MemoryForInference[]): ContradictionReport[] {
    const reports: ContradictionReport[] = [];

    if (memories.length < 2) {
      return reports;
    }

    // Group memories by (subject, attribute)
    const attributeGroups = this.groupBySubjectAttribute(memories);

    for (const [key, values] of attributeGroups) {
      // Parse key: "subject:attribute"
      const [subject, attribute] = key.split(":");

      // Check for conflicting values
      const uniqueValues = new Set(values.map((v) => v.normalized));

      if (uniqueValues.size <= 1) continue; // No conflict

      // Create conflict items
      const conflicts: ConflictItem[] = values.map((v) => ({
        memoryId: v.memoryId,
        content: v.content,
        claim: `${attribute}: ${v.raw}`,
        confidence: v.confidence,
        timestamp: v.timestamp,
      }));

      // Calculate confidence
      const confidence = this.calculateContradictionConfidence(values);

      // Determine severity
      const severity = this.getSeverity(confidence);

      // Create report
      reports.push({
        id: crypto.randomUUID(),
        type: ContradictionType.DIRECT,
        severity,
        description: `'${subject}' has conflicting values for '${attribute}'`,
        conflicts,
        confidence,
        timestamp: Date.now(),
      });
    }

    return reports;
  }

  /**
   * Generate resolution suggestions for a contradiction.
   */
  generateSuggestions(report: ContradictionReport): ContradictionSuggestion[] {
    const suggestions: ContradictionSuggestion[] = [];

    if (report.conflicts.length < 2) {
      return suggestions;
    }

    // Sort by timestamp (newest first)
    const sorted = [...report.conflicts].sort((a, b) => b.timestamp - a.timestamp);

    // Suggestion 1: Keep newer
    suggestions.push({
      type: "keep_newer",
      explanation: `Keep the most recent memory`,
      preferredMemoryId: sorted[0].memoryId,
      confidence: 0.8,
    });

    // Suggestion 2: Keep higher confidence
    const byConfidence = [...report.conflicts].sort((a, b) => b.confidence - a.confidence);
    suggestions.push({
      type: "keep_higher_confidence",
      explanation: `Keep the memory with highest confidence`,
      preferredMemoryId: byConfidence[0].memoryId,
      confidence: 0.7,
    });

    // Suggestion 3: Ask user
    suggestions.push({
      type: "ask_user",
      explanation: "User should manually resolve this contradiction",
      confidence: 0.9,
    });

    return suggestions;
  }

  // ── Private Methods ─────────────────────────────────────────────────────

  /**
   * Group memories by (subject, attribute).
   */
  private groupBySubjectAttribute(
    memories: MemoryForInference[]
  ): Map<string, AttributeValue[]> {
    const groups = new Map<string, AttributeValue[]>();

    for (const memory of memories) {
      const attributes = this.extractAttributes(memory);

      for (const attr of attributes) {
        // Use string key instead of object key for proper Map comparison
        const key = `${attr.subject}:${attr.attribute}`;

        const value: AttributeValue = {
          raw: attr.value,
          normalized: this.normalizeValue(attr.value),
          memoryId: memory.id,
          content: memory.content,
          confidence: memory.confidence ?? 0.8,
          timestamp: memory.timestamp ?? Date.now(),
        };

        const existing = groups.get(key);
        if (existing) {
          existing.push(value);
        } else {
          groups.set(key, [value]);
        }
      }
    }

    return groups;
  }

  /**
   * Extract (subject, attribute, value) from memory content.
   */
  private extractAttributes(memory: MemoryForInference): Array<{
    subject: string;
    attribute: string;
    value: string;
  }> {
    const attributes: Array<{
      subject: string;
      attribute: string;
      value: string;
    }> = [];
    const content = memory.content;

    // Pattern 1: "Person lives in City" or "Person 居住 City"
    // Match: "Peter lives in Shanghai"
    const livesInPattern = /(\w+)\s+lives\s+in\s+(\w+)/gi;
    let match;
    while ((match = livesInPattern.exec(content)) !== null) {
      attributes.push({
        subject: match[1],
        attribute: "lives_in",
        value: match[2],
      });
    }

    // Pattern 1b: Chinese "居住"
    const livesCnPattern = /(\w+)(?:居住于|居住在|住在)\s*(\w+)/g;
    while ((match = livesCnPattern.exec(content)) !== null) {
      attributes.push({
        subject: match[1],
        attribute: "lives_in",
        value: match[2],
      });
    }

    // Pattern 2: "Person's age is X" or "Person 年龄 X"
    const agePattern = /(\w+)(?:'s)?\s*(?:age|年龄)\s*(?:is\s+)?(\d+)/gi;
    while ((match = agePattern.exec(content)) !== null) {
      attributes.push({
        subject: match[1],
        attribute: "age",
        value: match[2],
      });
    }

    // Pattern 3: "Person is Status" (excluding common verbs)
    const statusPattern = /(\w+)\s+is\s+(\w+)(?!\s+(?:a|an|the|in|at|on|to|for|with|and|or|but|lives|works|knows|has|have))/gi;
    while ((match = statusPattern.exec(content)) !== null) {
      attributes.push({
        subject: match[1],
        attribute: "status",
        value: match[2],
      });
    }

    // Pattern 4: "Person's role is X"
    const rolePattern = /(\w+)(?:'s)?\s+(?:role|job|职位|工作)\s+(?:is\s+)?(\w+)/gi;
    const roleMatches = content.matchAll(rolePattern);
    for (const match of roleMatches) {
      attributes.push({
        subject: match[1],
        attribute: "role",
        value: match[2],
      });
    }

    return attributes;
  }

  /**
   * Normalize a value for comparison.
   */
  private normalizeValue(value: string): string {
    return value.toLowerCase().trim();
  }

  /**
   * Calculate contradiction confidence.
   */
  private calculateContradictionConfidence(values: AttributeValue[]): number {
    if (values.length < 2) return 0;

    // Average confidence of conflicting values
    const avgConfidence = values.reduce((sum, v) => sum + v.confidence, 0) / values.length;

    // More conflicting values = higher certainty
    const conflictFactor = Math.min(values.length / 3, 1.0);

    // Distinctness factor
    const uniqueValues = new Set(values.map((v) => v.normalized));
    const distinctnessFactor = Math.min(uniqueValues.size / 2, 1.0);

    return avgConfidence * conflictFactor * distinctnessFactor * 1.1;
  }

  /**
   * Determine severity from confidence.
   */
  private getSeverity(confidence: number): ContradictionSeverity {
    if (confidence >= 0.9) return ContradictionSeverity.HIGH;
    if (confidence >= 0.75) return ContradictionSeverity.MEDIUM;
    return ContradictionSeverity.LOW;
  }
}