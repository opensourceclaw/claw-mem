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
 * PrivacyFilter - PII and sensitivity filtering for shared memory.
 */

import type { MemoryRecord } from "./agnostic.js";
import { AgentAgnosticMemory } from "./agnostic.js";

export type PrivacyLevel = "local" | "shared" | "public";

const HIGH_SENSITIVITY_KEYWORDS = [
  "password", "secret", "credential", "token", "private key",
  "certificate", "passport", "bank account", "credit card",
];

export class PrivacyFilter {
  filter(record: MemoryRecord, level: PrivacyLevel): MemoryRecord {
    if (level === "local") return { ...record };

    let content = record.content;

    if (level === "shared") {
      content = AgentAgnosticMemory._strip_pii(content);
    }

    if (level === "public") {
      content = AgentAgnosticMemory._strip_pii(content);
      const lowered = content.toLowerCase();
      for (const kw of HIGH_SENSITIVITY_KEYWORDS) {
        if (lowered.includes(kw)) {
          content = "[REDACTED]";
          break;
        }
      }
    }

    return { ...record, content };
  }

  sensitivity(record: MemoryRecord): number {
    let score = 0.1;

    // Limit input length to prevent ReDoS
    const content = record.content.slice(0, 1000);

    const piiPatterns = [
      /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/,
      /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/,
      /(?:api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\w-]+/i,
      /sk-[a-zA-Z0-9]{20,}/,
    ];

    for (const p of piiPatterns) {
      if (p.test(content)) {
        score = Math.max(score, 0.8);
        break;
      }
    }

    const lowered = content.toLowerCase();
    for (const kw of HIGH_SENSITIVITY_KEYWORDS) {
      if (lowered.includes(kw)) {
        score = Math.max(score, 0.6);
        break;
      }
    }

    return score;
  }
}
