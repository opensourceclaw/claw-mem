// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.21.0 — Tag Manager (TS)
 *
 * Manages session tags with consistent format and validation.
 * Tag format: {prefix}:{type}:{sessionId}
 */

import { SESSION_TAGS } from "./types.js";
import type { SessionTag } from "./types.js";

export class TagManager {
  private prefix: string;
  private tags: Set<string>;
  private history: Array<{ tag: string; action: "add" | "remove"; timestamp: string }>;

  constructor(prefix: string = "claw") {
    this.prefix = prefix || "claw";
    this.tags = new Set();
    this.history = [];
  }

  /** Generate a tag for a given record type and session. */
  generate(recordType: keyof typeof SESSION_TAGS, sessionId: string): string {
    if (!sessionId) {
      throw new TypeError("sessionId cannot be empty");
    }

    const type = SESSION_TAGS[recordType];
    const tag = `${this.prefix}:${type}:${sessionId}`;
    this.tags.add(tag);
    this.history.push({ tag, action: "add", timestamp: new Date().toISOString() });
    return tag;
  }

  /** Validate whether a tag matches the expected format. */
  validate(tag: string): boolean {
    if (!tag || typeof tag !== "string") return false;

    const prefixMatch = tag.startsWith(`${this.prefix}:`);
    if (!prefixMatch) return false;

    const parts = tag.split(":");
    if (parts.length !== 3) return false;

    const [, type, sessionId] = parts;

    // Type must be a valid SESSION_TAGS value
    const validTypes = Object.values(SESSION_TAGS);
    if (!validTypes.includes(type as SessionTag)) return false;

    // sessionId cannot be empty
    if (!sessionId) return false;

    // Total length limit
    if (tag.length > 128) return false;

    return true;
  }

  /** Batch validate tags. */
  validateAll(tags: string[]): { valid: string[]; invalid: string[] } {
    const valid: string[] = [];
    const invalid: string[] = [];

    for (const tag of tags) {
      if (this.validate(tag)) {
        valid.push(tag);
      } else {
        invalid.push(tag);
      }
    }

    return { valid, invalid };
  }

  /** Get tag change history. */
  getHistory(): Array<{ tag: string; action: "add" | "remove"; timestamp: string }> {
    return [...this.history];
  }
}
