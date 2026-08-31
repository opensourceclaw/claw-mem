// claw-mem v5.0.0 — Retrieval Base (TypeScript)
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

import type { MemoryRecord } from "../types.js";

/**
 * A single retrieval result from any retriever.
 */
export interface RetrievalResult {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, unknown>;
  source?: string;
  memory_type?: string;
  tags?: string[];
  timestamp?: string;
  /** v7.5.0 (ADR-002): retention score carried for three-way fusion */
  retention?: number;
}

/**
 * Document to be indexed for retrieval.
 */
export interface RetrievalDocument {
  id: string;
  text: string;
  metadata?: Record<string, unknown>;
}

/**
 * Abstract base class for all retrievers.
 */
export abstract class BaseRetriever {
  /** Search for relevant documents. */
  abstract search(query: string, limit?: number, ...args: unknown[]): RetrievalResult[];

  /** Index documents for retrieval. */
  abstract index(documents: RetrievalDocument[]): void;

  /** Clear all indexed data. Default: no-op. */
  clear(): void {
    // no-op
  }

  /** Get retriever statistics. Default: empty object. */
  getStats(): Record<string, unknown> {
    return {};
  }
}
