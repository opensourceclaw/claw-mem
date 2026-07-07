// claw-mem v6.34.0 — KnowledgeDeriver (TypeScript)
//
// Implements derivation rules to extract new knowledge from memories.
// MVP: Transitive derivation only (A → B, B → C ⇒ A → C)
//
// Licensed under the Apache License, Version 2.0

import * as crypto from "crypto";
import {
  InferenceStep,
  InferenceStepType,
  DerivedKnowledge,
  DerivationType,
} from "./types.js";
import type { MemoryForInference, MemoryId } from "./engine.js";

/** Relation triple extracted from memory */
interface RelationTriple {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
  memoryId: MemoryId;
}

/** Transitive derivation result */
interface TransitiveResult {
  knowledge: DerivedKnowledge[];
  steps: InferenceStep[];
}

/** Relation graph for transitive derivation */
interface RelationGraph {
  vertices: Set<string>;
  edges: Map<string, EdgeInfo[]>;
}

/** Edge information in relation graph */
interface EdgeInfo {
  to: string;
  predicate: string;
  confidence: number;
  memoryIds: MemoryId[];
}

/** Common relation predicates for transitive derivation */
const TRANSITIVE_PREDICATES = [
  "knows",
  "relates_to",
  "connected_to",
  "associated_with",
  "linked_to",
  "depends_on",
  "follows",
  "precedes",
  "parent_of",
  "child_of",
  "认识",
  "关联",
  "连接",
  "依赖",
  "跟随",
];

/**
 * KnowledgeDeriver — applies derivation rules to memories.
 */
export class KnowledgeDeriver {
  /**
   * Derive knowledge using transitive rule.
   * If A → B and B → C, then A → C.
   */
  deriveTransitive(memories: MemoryForInference[]): TransitiveResult {
    const knowledge: DerivedKnowledge[] = [];
    const steps: InferenceStep[] = [];

    if (memories.length === 0) {
      return { knowledge, steps };
    }

    // Extract relation triples
    const triples = this.extractTriples(memories);

    if (triples.length === 0) {
      return { knowledge, steps };
    }

    // Build relation graph
    const graph = this.buildRelationGraph(triples);

    // Add premise steps
    for (const triple of triples) {
      steps.push({
        stepId: crypto.randomUUID(),
        type: InferenceStepType.PREMISE,
        content: `${triple.subject} ${triple.predicate} ${triple.object}`,
        memories: [triple.memoryId],
        confidence: triple.confidence,
        timestamp: Date.now(),
      });
    }

    // Find transitive chains
    const transitiveRelations = this.findTransitiveChains(graph);

    // Add rule application step
    steps.push({
      stepId: crypto.randomUUID(),
      type: InferenceStepType.RULE,
      content: "TRANSITIVE_DERIVATION: A → B, B → C ⇒ A → C",
      memories: [],
      confidence: 1.0,
      timestamp: Date.now(),
    });

    // Create derived knowledge
    for (const relation of transitiveRelations) {
      const derivedK: DerivedKnowledge = {
        id: crypto.randomUUID(),
        type: DerivationType.TRANSITIVE,
        subject: relation.subject,
        predicate: relation.predicate,
        object: relation.object,
        confidence: relation.confidence,
        chainId: "", // Set by caller
        sourceMemoryIds: relation.memoryIds,
        timestamp: Date.now(),
      };
      knowledge.push(derivedK);

      // Add derivation step
      steps.push({
        stepId: crypto.randomUUID(),
        type: InferenceStepType.DERIVATION,
        content: `Derived: ${relation.subject} ${relation.predicate} ${relation.object}`,
        memories: relation.memoryIds,
        confidence: relation.confidence,
        timestamp: Date.now(),
      });
    }

    // Add conclusion step if knowledge found
    if (knowledge.length > 0) {
      const topK = knowledge[0];
      steps.push({
        stepId: crypto.randomUUID(),
        type: InferenceStepType.CONCLUSION,
        content: `${topK.subject} may ${topK.predicate} ${topK.object}`,
        memories: topK.sourceMemoryIds,
        confidence: topK.confidence,
        timestamp: Date.now(),
      });
    }

    return { knowledge, steps };
  }

  // ── Private Methods ─────────────────────────────────────────────────────

  /**
   * Extract relation triples from memory content.
   */
  private extractTriples(memories: MemoryForInference[]): RelationTriple[] {
    const triples: RelationTriple[] = [];

    for (const memory of memories) {
      const content = memory.content;

      // Pattern 1: "A knows B" or "A 认识 B"
      for (const predicate of TRANSITIVE_PREDICATES) {
        const pattern = new RegExp(`(\\w+)\\s+${predicate}\\s+(\\w+)`, "gi");
        const matches = content.matchAll(pattern);

        for (const match of matches) {
          const subject = match[1];
          const object = match[2];

          triples.push({
            subject,
            predicate,
            object,
            confidence: memory.confidence ?? 0.8,
            memoryId: memory.id,
          });
        }
      }

      // Pattern 2: "A → B" style relations
      const arrowPattern = /(\w+)\s*→\s*(\w+)/g;
      const arrowMatches = content.matchAll(arrowPattern);
      for (const match of arrowMatches) {
        triples.push({
          subject: match[1],
          predicate: "relates_to",
          object: match[2],
          confidence: memory.confidence ?? 0.8,
          memoryId: memory.id,
        });
      }
    }

    return triples;
  }

  /**
   * Build directed relation graph from triples.
   */
  private buildRelationGraph(triples: RelationTriple[]): RelationGraph {
    const vertices = new Set<string>();
    const edges = new Map<string, EdgeInfo[]>();

    for (const triple of triples) {
      vertices.add(triple.subject);
      vertices.add(triple.object);

      const existing = edges.get(triple.subject);
      if (existing) {
        existing.push({
          to: triple.object,
          predicate: triple.predicate,
          confidence: triple.confidence,
          memoryIds: [triple.memoryId],
        });
      } else {
        edges.set(triple.subject, [{
          to: triple.object,
          predicate: triple.predicate,
          confidence: triple.confidence,
          memoryIds: [triple.memoryId],
        }]);
      }
    }

    return { vertices, edges };
  }

  /**
   * Find transitive chains in the relation graph.
   * A → B, B → C ⇒ A → C
   */
  private findTransitiveChains(graph: RelationGraph): Array<{
    subject: string;
    predicate: string;
    object: string;
    confidence: number;
    memoryIds: MemoryId[];
  }> {
    const results: Array<{
      subject: string;
      predicate: string;
      object: string;
      confidence: number;
      memoryIds: MemoryId[];
    }> = [];

    // For each vertex A
    for (const [a, aEdges] of graph.edges) {
      // For each edge A → B
      for (const aEdge of aEdges) {
        const b = aEdge.to;
        const bEdges = graph.edges.get(b);

        if (!bEdges) continue;

        // For each edge B → C
        for (const bEdge of bEdges) {
          const c = bEdge.to;

          // Skip self-loops
          if (a === c) continue;

          // Skip if direct edge A → C exists
          if (this.hasDirectEdge(graph, a, c)) continue;

          // Calculate confidence (minimum of both edges, decayed)
          const confidence = Math.min(aEdge.confidence, bEdge.confidence) * 0.85;

          // Combine memory IDs
          const memoryIds = [...aEdge.memoryIds, ...bEdge.memoryIds];

          // Use predicate from A → B edge
          results.push({
            subject: a,
            predicate: aEdge.predicate,
            object: c,
            confidence,
            memoryIds,
          });
        }
      }
    }

    return results;
  }

  /**
   * Check if direct edge exists between two vertices.
   */
  private hasDirectEdge(graph: RelationGraph, from: string, to: string): boolean {
    const edges = graph.edges.get(from);
    if (!edges) return false;
    return edges.some((e) => e.to === to);
  }
}