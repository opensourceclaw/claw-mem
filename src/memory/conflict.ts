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
 * ConflictResolver - detect and resolve cross-agent memory conflicts.
 */

import type { MemoryRecord } from "./agnostic.js";

export type ConflictStrategy = "lww" | "merge" | "keep-both" | "ask-human";

export interface Conflict {
  id: string;
  recordA: MemoryRecord;
  recordB: MemoryRecord;
  commonTags: string[];
  detectedAt: number;
}

export class ConflictResolver {
  detect(record: MemoryRecord, existing: MemoryRecord): Conflict | null {
    const commonTags = record.tags.filter((t) => existing.tags.includes(t));
    if (commonTags.length === 0) return null;
    if (record.content === existing.content) return null;

    return {
      id: `conflict-${record.id}-${existing.id}`,
      recordA: record,
      recordB: existing,
      commonTags,
      detectedAt: Date.now() / 1000,
    };
  }

  resolve(conflict: Conflict, strategy: ConflictStrategy): MemoryRecord {
    switch (strategy) {
      case "lww":
        return conflict.recordA.timestamp >= conflict.recordB.timestamp
          ? { ...conflict.recordA }
          : { ...conflict.recordB };

      case "merge": {
        const parts = [
          ...new Set([conflict.recordA.content, conflict.recordB.content]),
        ];
        const mergedTags = [
          ...new Set([...conflict.recordA.tags, ...conflict.recordB.tags]),
        ];
        return {
          ...conflict.recordA,
          content: parts.join(" | "),
          tags: mergedTags,
          confidence: Math.max(
            conflict.recordA.confidence,
            conflict.recordB.confidence,
          ),
        };
      }

      case "keep-both":
        return {
          ...conflict.recordA,
          tags: [
            ...new Set([
              ...conflict.recordA.tags,
              ...conflict.recordB.tags,
              "conflict:dual",
            ]),
          ],
        };

      case "ask-human":
        return {
          ...conflict.recordA,
          tags: [
            ...new Set([...conflict.recordA.tags, "conflict:pending"]),
          ],
        };

      default:
        return { ...conflict.recordA };
    }
  }
}
