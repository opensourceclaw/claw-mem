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
 * Graph Nodes - Concept-mediated graph node types
 *
 * Based on GAAMA paper's four node types:
 * - Episode: conversation segments, event sequences
 * - Fact: extracted facts, knowledge
 * - Reflection: summaries, insights, patterns
 * - Concept: abstract concepts, themes
 */

export enum NodeType {
  EPISODE = "episode",
  FACT = "fact",
  REFLECTION = "reflection",
  CONCEPT = "concept",
}

/** A generic node dictionary used for serialization round-trips. */
export interface NodeDict {
  id: string;
  type: string;
  content: string;
  embedding?: number[] | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at?: string | null;
  // Episode-specific
  sequence_id?: number;
  speaker?: string | null;
  timestamp?: string | null;
  session_id?: string | null;
  // Fact-specific
  confidence?: number;
  source_episode?: string | null;
  verified?: boolean;
  // Reflection-specific
  summary_type?: string;
  source_node_ids?: string[];
  importance?: number;
  // Concept-specific
  category?: string;
  frequency?: number;
  aliases?: string[];
}

export class Node {
  id: string;
  type: NodeType;
  content: string;
  embedding?: number[] | null;
  metadata: Record<string, unknown>;
  created_at: Date;
  updated_at?: Date | null;

  constructor(
    id: string,
    type: NodeType,
    content: string,
    embedding?: number[] | null,
    metadata?: Record<string, unknown>,
    created_at?: Date,
    updated_at?: Date | null,
  ) {
    this.id = id;
    this.type = type;
    this.content = content;
    this.embedding = embedding ?? null;
    this.metadata = metadata ?? {};
    this.created_at = created_at ?? new Date();
    this.updated_at = updated_at ?? null;
  }

  toDict(): NodeDict {
    return {
      id: this.id,
      type: this.type,
      content: this.content,
      embedding: this.embedding,
      metadata: this.metadata,
      created_at: this.created_at ? this.created_at.toISOString() : null,
      updated_at: this.updated_at ? this.updated_at.toISOString() : null,
    };
  }

  static fromDict(data: NodeDict): Node {
    const created_at = data.created_at ? new Date(data.created_at) : new Date();
    const updated_at = data.updated_at ? new Date(data.updated_at) : null;
    return new Node(
      data.id,
      data.type as NodeType,
      data.content,
      data.embedding ?? null,
      data.metadata ?? {},
      created_at,
      updated_at,
    );
  }
}

export class EpisodeNode {
  id: string;
  content: string;
  sequence_id: number;
  speaker?: string | null;
  timestamp?: Date | null;
  session_id?: string | null;
  embedding?: number[] | null;
  metadata: Record<string, unknown>;
  created_at: Date;
  updated_at?: Date | null;

  get type(): NodeType {
    return NodeType.EPISODE;
  }

  constructor(
    id: string,
    content: string,
    sequence_id: number = 0,
    speaker?: string | null,
    timestamp?: Date | null,
    session_id?: string | null,
    embedding?: number[] | null,
    metadata?: Record<string, unknown>,
    created_at?: Date,
    updated_at?: Date | null,
  ) {
    this.id = id;
    this.content = content;
    this.sequence_id = sequence_id;
    this.speaker = speaker ?? null;
    this.timestamp = timestamp ?? null;
    this.session_id = session_id ?? null;
    this.embedding = embedding ?? null;
    this.metadata = metadata ?? {};
    this.created_at = created_at ?? new Date();
    this.updated_at = updated_at ?? null;
  }

  toDict(): NodeDict {
    return {
      id: this.id,
      type: this.type,
      content: this.content,
      sequence_id: this.sequence_id,
      speaker: this.speaker,
      timestamp: this.timestamp ? this.timestamp.toISOString() : null,
      session_id: this.session_id,
      embedding: this.embedding,
      metadata: this.metadata,
      created_at: this.created_at ? this.created_at.toISOString() : null,
      updated_at: this.updated_at ? this.updated_at.toISOString() : null,
    };
  }

  static fromDict(data: NodeDict): EpisodeNode {
    const created_at = data.created_at ? new Date(data.created_at) : new Date();
    const timestamp = data.timestamp ? new Date(data.timestamp) : null;
    return new EpisodeNode(
      data.id,
      data.content,
      data.sequence_id ?? 0,
      data.speaker ?? null,
      timestamp,
      data.session_id ?? null,
      data.embedding ?? null,
      data.metadata ?? {},
      created_at,
    );
  }
}

export class FactNode {
  id: string;
  content: string;
  confidence: number;
  source_episode?: string | null;
  verified: boolean;
  embedding?: number[] | null;
  metadata: Record<string, unknown>;
  created_at: Date;
  updated_at?: Date | null;

  get type(): NodeType {
    return NodeType.FACT;
  }

  constructor(
    id: string,
    content: string,
    confidence: number = 1.0,
    source_episode?: string | null,
    verified: boolean = false,
    embedding?: number[] | null,
    metadata?: Record<string, unknown>,
    created_at?: Date,
    updated_at?: Date | null,
  ) {
    this.id = id;
    this.content = content;
    this.confidence = confidence;
    this.source_episode = source_episode ?? null;
    this.verified = verified;
    this.embedding = embedding ?? null;
    this.metadata = metadata ?? {};
    this.created_at = created_at ?? new Date();
    this.updated_at = updated_at ?? null;
  }

  toDict(): NodeDict {
    return {
      id: this.id,
      type: this.type,
      content: this.content,
      confidence: this.confidence,
      source_episode: this.source_episode,
      verified: this.verified,
      embedding: this.embedding,
      metadata: this.metadata,
      created_at: this.created_at ? this.created_at.toISOString() : null,
      updated_at: this.updated_at ? this.updated_at.toISOString() : null,
    };
  }

  static fromDict(data: NodeDict): FactNode {
    const created_at = data.created_at ? new Date(data.created_at) : new Date();
    return new FactNode(
      data.id,
      data.content,
      data.confidence ?? 1.0,
      data.source_episode ?? null,
      data.verified ?? false,
      data.embedding ?? null,
      data.metadata ?? {},
      created_at,
    );
  }
}

export class ReflectionNode {
  id: string;
  content: string;
  summary_type: string;
  source_node_ids: string[];
  importance: number;
  embedding?: number[] | null;
  metadata: Record<string, unknown>;
  created_at: Date;
  updated_at?: Date | null;

  get type(): NodeType {
    return NodeType.REFLECTION;
  }

  constructor(
    id: string,
    content: string,
    summary_type: string = "general",
    source_node_ids: string[] = [],
    importance: number = 0.5,
    embedding?: number[] | null,
    metadata?: Record<string, unknown>,
    created_at?: Date,
    updated_at?: Date | null,
  ) {
    this.id = id;
    this.content = content;
    this.summary_type = summary_type;
    this.source_node_ids = source_node_ids;
    this.importance = importance;
    this.embedding = embedding ?? null;
    this.metadata = metadata ?? {};
    this.created_at = created_at ?? new Date();
    this.updated_at = updated_at ?? null;
  }

  toDict(): NodeDict {
    return {
      id: this.id,
      type: this.type,
      content: this.content,
      summary_type: this.summary_type,
      source_node_ids: this.source_node_ids,
      importance: this.importance,
      embedding: this.embedding,
      metadata: this.metadata,
      created_at: this.created_at ? this.created_at.toISOString() : null,
      updated_at: this.updated_at ? this.updated_at.toISOString() : null,
    };
  }

  static fromDict(data: NodeDict): ReflectionNode {
    const created_at = data.created_at ? new Date(data.created_at) : new Date();
    return new ReflectionNode(
      data.id,
      data.content,
      data.summary_type ?? "general",
      data.source_node_ids ?? [],
      data.importance ?? 0.5,
      data.embedding ?? null,
      data.metadata ?? {},
      created_at,
    );
  }
}

export class ConceptNode {
  id: string;
  content: string;
  category: string;
  frequency: number;
  aliases: string[];
  embedding?: number[] | null;
  metadata: Record<string, unknown>;
  created_at: Date;
  updated_at?: Date | null;

  get type(): NodeType {
    return NodeType.CONCEPT;
  }

  constructor(
    id: string,
    content: string,
    category: string = "general",
    frequency: number = 1,
    aliases: string[] = [],
    embedding?: number[] | null,
    metadata?: Record<string, unknown>,
    created_at?: Date,
    updated_at?: Date | null,
  ) {
    this.id = id;
    this.content = content;
    this.category = category;
    this.frequency = frequency;
    this.aliases = aliases;
    this.embedding = embedding ?? null;
    this.metadata = metadata ?? {};
    this.created_at = created_at ?? new Date();
    this.updated_at = updated_at ?? null;
  }

  toDict(): NodeDict {
    return {
      id: this.id,
      type: this.type,
      content: this.content,
      category: this.category,
      frequency: this.frequency,
      aliases: this.aliases,
      embedding: this.embedding,
      metadata: this.metadata,
      created_at: this.created_at ? this.created_at.toISOString() : null,
      updated_at: this.updated_at ? this.updated_at.toISOString() : null,
    };
  }

  static fromDict(data: NodeDict): ConceptNode {
    const created_at = data.created_at ? new Date(data.created_at) : new Date();
    return new ConceptNode(
      data.id,
      data.content,
      data.category ?? "general",
      data.frequency ?? 1,
      data.aliases ?? [],
      data.embedding ?? null,
      data.metadata ?? {},
      created_at,
    );
  }
}

export type AnyNode = Node | EpisodeNode | FactNode | ReflectionNode | ConceptNode;

/** Generate a unique node id using timestamp + random. */
function generateNodeId(type: string): string {
  const ts = Date.now() * 1000 + Math.floor(Math.random() * 1000);
  return `${type}_${ts}`;
}

/**
 * Factory function: create node.
 *
 * Example:
 *   const node = createNode(NodeType.EPISODE, "User said: Hello", { speaker: "user" });
 */
export function createNode(
  nodeType: NodeType,
  content: string,
  extra?: Record<string, unknown>,
): AnyNode {
  const id = (extra?.id as string) ?? generateNodeId(nodeType);
  switch (nodeType) {
    case NodeType.EPISODE:
      return new EpisodeNode(
        id,
        content,
        (extra?.sequence_id as number) ?? 0,
        (extra?.speaker as string) ?? null,
        (extra?.timestamp as Date) ?? null,
        (extra?.session_id as string) ?? null,
        (extra?.embedding as number[]) ?? null,
        (extra?.metadata as Record<string, unknown>) ?? {},
      );
    case NodeType.FACT:
      return new FactNode(
        id,
        content,
        (extra?.confidence as number) ?? 1.0,
        (extra?.source_episode as string) ?? null,
        (extra?.verified as boolean) ?? false,
        (extra?.embedding as number[]) ?? null,
        (extra?.metadata as Record<string, unknown>) ?? {},
      );
    case NodeType.REFLECTION:
      return new ReflectionNode(
        id,
        content,
        (extra?.summary_type as string) ?? "general",
        (extra?.source_node_ids as string[]) ?? [],
        (extra?.importance as number) ?? 0.5,
        (extra?.embedding as number[]) ?? null,
        (extra?.metadata as Record<string, unknown>) ?? {},
      );
    case NodeType.CONCEPT:
      return new ConceptNode(
        id,
        content,
        (extra?.category as string) ?? "general",
        (extra?.frequency as number) ?? 1,
        (extra?.aliases as string[]) ?? [],
        (extra?.embedding as number[]) ?? null,
        (extra?.metadata as Record<string, unknown>) ?? {},
      );
    default:
      throw new Error(`Unknown node type: ${nodeType}`);
  }
}
