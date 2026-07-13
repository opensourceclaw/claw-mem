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
 * Graph Edges - Concept-mediated graph edge types
 *
 * Based on GAAMA paper's five edge types:
 * - NEXT: Episode sequence (Episode -> Episode)
 * - DERIVED_FROM: Fact origin (Fact -> Episode)
 * - SYNTHESIZED_FROM: Reflection origin (Reflection -> Episode/Fact)
 * - RELATED_TO: Related relationship (between any nodes)
 * - HAS_CONCEPT: Concept association (Any node -> Concept)
 */

export enum EdgeType {
  NEXT = "NEXT",
  DERIVED_FROM = "DERIVED_FROM",
  SYNTHESIZED_FROM = "SYNTHESIZED_FROM",
  RELATED_TO = "RELATED_TO",
  HAS_CONCEPT = "HAS_CONCEPT",
}

/** Helper: whether an edge type is directed. */
export function isEdgeDirected(edgeType: EdgeType): boolean {
  return edgeType !== EdgeType.RELATED_TO;
}

/** Edge dictionary for serialization. */
export interface EdgeDict {
  source_id: string;
  target_id: string;
  type: string;
  weight: number;
  metadata: Record<string, unknown>;
  created_at: string | null;
}

export class Edge {
  source_id: string;
  target_id: string;
  type: EdgeType;
  weight: number;
  metadata: Record<string, unknown>;
  created_at: Date;

  constructor(
    source_id: string,
    target_id: string,
    type: EdgeType,
    weight: number = 1.0,
    metadata?: Record<string, unknown>,
    created_at?: Date,
  ) {
    this.source_id = source_id;
    this.target_id = target_id;
    this.type = type;
    this.weight = weight;
    this.metadata = metadata ?? {};
    this.created_at = created_at ?? new Date();
  }

  toDict(): EdgeDict {
    return {
      source_id: this.source_id,
      target_id: this.target_id,
      type: this.type,
      weight: this.weight,
      metadata: this.metadata,
      created_at: this.created_at ? this.created_at.toISOString() : null,
    };
  }

  static fromDict(data: EdgeDict): Edge {
    const created_at = data.created_at ? new Date(data.created_at) : new Date();
    return new Edge(
      data.source_id,
      data.target_id,
      data.type as EdgeType,
      data.weight ?? 1.0,
      data.metadata ?? {},
      created_at,
    );
  }
}

export class NextEdge extends Edge {
  constructor(source_id: string, target_id: string, extra?: Record<string, unknown>) {
    super(
      source_id,
      target_id,
      EdgeType.NEXT,
      (extra?.weight as number) ?? 1.0,
      (extra?.metadata as Record<string, unknown>) ?? {},
    );
  }
}

export class DerivedFromEdge extends Edge {
  constructor(source_id: string, target_id: string, extra?: Record<string, unknown>) {
    super(
      source_id,
      target_id,
      EdgeType.DERIVED_FROM,
      (extra?.weight as number) ?? 1.0,
      (extra?.metadata as Record<string, unknown>) ?? {},
    );
  }
}

export class SynthesizedFromEdge extends Edge {
  source_node_ids: string[];

  constructor(
    source_id: string,
    target_id: string,
    source_node_ids: string[] = [],
    extra?: Record<string, unknown>,
  ) {
    super(
      source_id,
      target_id,
      EdgeType.SYNTHESIZED_FROM,
      (extra?.weight as number) ?? 1.0,
      (extra?.metadata as Record<string, unknown>) ?? {},
    );
    this.source_node_ids = source_node_ids;
  }
}

export class RelatedToEdge extends Edge {
  constructor(source_id: string, target_id: string, extra?: Record<string, unknown>) {
    super(
      source_id,
      target_id,
      EdgeType.RELATED_TO,
      (extra?.weight as number) ?? 1.0,
      (extra?.metadata as Record<string, unknown>) ?? {},
    );
  }
}

export class HasConceptEdge extends Edge {
  constructor(source_id: string, target_id: string, extra?: Record<string, unknown>) {
    super(
      source_id,
      target_id,
      EdgeType.HAS_CONCEPT,
      (extra?.weight as number) ?? 1.0,
      (extra?.metadata as Record<string, unknown>) ?? {},
    );
  }
}

export type AnyEdge = Edge | NextEdge | DerivedFromEdge | SynthesizedFromEdge | RelatedToEdge | HasConceptEdge;

/**
 * Factory function: create edge.
 *
 * Example:
 *   const edge = createEdge(EdgeType.NEXT, "ep_1", "ep_2");
 */
export function createEdge(
  edgeType: EdgeType,
  source_id: string,
  target_id: string,
  extra?: Record<string, unknown>,
): Edge {
  switch (edgeType) {
    case EdgeType.NEXT:
      return new NextEdge(source_id, target_id, extra);
    case EdgeType.DERIVED_FROM:
      return new DerivedFromEdge(source_id, target_id, extra);
    case EdgeType.SYNTHESIZED_FROM:
      return new SynthesizedFromEdge(
        source_id,
        target_id,
        (extra?.source_node_ids as string[]) ?? [],
        extra,
      );
    case EdgeType.RELATED_TO:
      return new RelatedToEdge(source_id, target_id, extra);
    case EdgeType.HAS_CONCEPT:
      return new HasConceptEdge(source_id, target_id, extra);
    default:
      throw new Error(`Unknown edge type: ${edgeType}`);
  }
}
