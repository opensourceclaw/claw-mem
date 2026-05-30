// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Write Validator (MVP Version)
 *
 * Validates memory write requests, rejects unsafe content.
 * Uses rule-based pattern matching. Semantic analysis will be added
 * in future iterations.
 */

// Unsafe patterns list (English + Chinese)
const UNSAFE_PATTERNS: RegExp[] = [
  /ignore.*instruction/i,          // Ignore instructions
  /忽略.*指令/i,                    // Ignore instructions
  /override.*memory/i,              // Override memory
  /覆盖.*记忆/i,                     // Override memory
  /delete.*file/i,                  // Delete files
  /delete.*文件/i,                   // Delete files
  /execute.*code/i,                 // Execute code
  /执行.*代码/i,                     // Execute code
  /system:/i,                       // System prompt injection
  /<\|startoftext\|>/i,             // Special tokens
  /act as.*system/i,                // Role-playing attacks
  /扮演.*系统/i,                     // Role-playing attacks
];

const MAX_CONTENT_LENGTH = 10000;

export class WriteValidator {
  /**
   * Validate memory content safety.
   *
   * @param content - Memory content to validate
   * @returns `true` if content is safe, `false` otherwise
   */
  validate(content: string): boolean {
    // Check empty content
    if (!content || content.trim().length === 0) {
      return false;
    }

    // Check unsafe patterns
    for (const pattern of UNSAFE_PATTERNS) {
      if (pattern.test(content)) {
        return false;
      }
    }

    // Check length (prevent overflow)
    if (content.length > MAX_CONTENT_LENGTH) {
      return false;
    }

    return true;
  }

  /**
   * Get the rejection reason for content.
   *
   * @param content - Memory content to check
   * @returns Human-readable rejection reason
   */
  getRejectionReason(content: string): string {
    if (!content || content.trim().length === 0) {
      return "Content is empty";
    }

    for (let i = 0; i < UNSAFE_PATTERNS.length; i++) {
      if (UNSAFE_PATTERNS[i].test(content)) {
        return `Contains unsafe pattern: ${UNSAFE_PATTERNS[i].source}`;
      }
    }

    if (content.length > MAX_CONTENT_LENGTH) {
      return `Content too long (max ${MAX_CONTENT_LENGTH} characters)`;
    }

    return "Unknown reason";
  }
}
