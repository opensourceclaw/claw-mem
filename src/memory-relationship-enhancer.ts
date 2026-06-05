// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * MemoryRelationshipEnhancer — Entity chaining, decision lineage, and causal
 * graph for claw-mem v6.8.0.
 *
 * Enriches memory graphs with long-horizon relationship tracking across
 * multiple sessions, enabling cross-session context injection and
 * dependency-aware memory retrieval.
 */

// ── Types ─────────────────────────────────────────────────────────────────

export interface EntityNode {
  id: string;
  name: string;
  type: "person" | "tool" | "concept" | "file" | "project" | "event" | "decision" | "other";
  firstSeen: number;
  lastSeen: number;
  sessions: string[];
  metadata: Record<string, string>;
}

export interface EntityLink {
  source: string;
  target: string;
  type: "co_occurrence" | "causal" | "dependency" | "lineage";
  weight: number;
  sessions: string[];
  timestamp: number;
}

export interface DecisionRecord {
  id: string;
  description: string;
  sessionId: string;
  timestamp: number;
  context: string;
  entitiesInvolved: string[];
  parentDecision?: string;
  outcome?: string;
}

export interface LineageChain {
  rootId: string;
  decisions: DecisionRecord[];
  depth: number;
}

export interface CausalEvent {
  id: string;
  description: string;
  sessionId: string;
  timestamp: number;
  type: "cause" | "effect" | "both";
}

export interface CausalLink {
  cause: CausalEvent;
  effect: CausalEvent;
  confidence: number;
  sessionId: string;
  timestamp: number;
}

// ── EntityChaining ───────────────────────────────────────────────────────

export class EntityChaining {
  private entities = new Map<string, EntityNode>();
  private links: EntityLink[] = [];

  /** Register or update an entity across sessions. */
  linkEntities(e1: string, e2: string, sessionId?: string): void {
    const now = Date.now();
    this.ensureEntity(e1, sessionId ?? "", now);
    this.ensureEntity(e2, sessionId ?? "", now);

    // Add bidirectional link
    const existing = this.links.find(
      (l) =>
        (l.source === e1 && l.target === e2) ||
        (l.source === e2 && l.target === e1),
    );

    if (existing) {
      existing.weight++;
      if (sessionId && !existing.sessions.includes(sessionId)) {
        existing.sessions.push(sessionId);
      }
    } else {
      this.links.push({
        source: e1,
        target: e2,
        type: "co_occurrence",
        weight: 1,
        sessions: sessionId ? [sessionId] : [],
        timestamp: now,
      });
    }
  }

  /** Get the entity chain for a given entity (connected component). */
  getEntityChain(entityName: string): EntityNode[] {
    const visited = new Set<string>();
    const result: EntityNode[] = [];
    const queue = [entityName];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);

      const node = this.entities.get(current);
      if (node) result.push(node);

      // Follow all links
      for (const link of this.links) {
        if (link.source === current && !visited.has(link.target)) {
          queue.push(link.target);
        } else if (link.target === current && !visited.has(link.source)) {
          queue.push(link.source);
        }
      }
    }

    return result;
  }

  /** Get all links for a given entity. */
  getEntityLinks(entityName: string): EntityLink[] {
    return this.links.filter(
      (l) => l.source === entityName || l.target === entityName,
    );
  }

  /** Get cross-session entities related to the given entity. */
  getCrossSessionRelated(entityName: string): EntityNode[] {
    const chain = this.getEntityChain(entityName);
    const targetSessions = new Set(
      this.entities.get(entityName)?.sessions ?? [],
    );
    return chain.filter((node) =>
      node.sessions.some((s) => !targetSessions.has(s)),
    );
  }

  /** Reset all entity data. */
  reset(): void {
    this.entities.clear();
    this.links = [];
  }

  /** Get stats. */
  getStats(): { entityCount: number; linkCount: number } {
    return { entityCount: this.entities.size, linkCount: this.links.length };
  }

  private ensureEntity(name: string, sessionId: string, now: number): void {
    let node = this.entities.get(name);
    if (!node) {
      node = {
        id: `ent-${this.entities.size}`,
        name,
        type: "concept",
        firstSeen: now,
        lastSeen: now,
        sessions: [],
        metadata: {},
      };
      this.entities.set(name, node);
    }
    node.lastSeen = now;
    if (sessionId && !node.sessions.includes(sessionId)) {
      node.sessions.push(sessionId);
    }
  }
}

// ── DecisionLineage ──────────────────────────────────────────────────────

export class DecisionLineage {
  private decisions: DecisionRecord[] = [];
  private chains = new Map<string, LineageChain>();

  /** Track a decision with its context and involved entities. */
  trackDecision(
    decision: DecisionRecord,
    context: string,
  ): void {
    const record: DecisionRecord = {
      ...decision,
      context,
      timestamp: decision.timestamp || Date.now(),
    };
    this.decisions.push(record);

    // Update or create lineage chain
    if (decision.parentDecision) {
      let chain = this.chains.get(decision.parentDecision);
      if (!chain) {
        const parent = this.decisions.find(
          (d) => d.id === decision.parentDecision,
        );
        chain = {
          rootId: decision.parentDecision,
          decisions: parent ? [parent] : [],
          depth: parent ? 1 : 0,
        };
      }
      chain.decisions.push(record);
      chain.depth++;
      this.chains.set(chain.rootId, chain);
    } else {
      // New root decision
      this.chains.set(record.id, {
        rootId: record.id,
        decisions: [record],
        depth: 1,
      });
    }
  }

  /** Get the full decision history ordered by time. */
  getDecisionHistory(): DecisionRecord[] {
    return [...this.decisions].sort((a, b) => a.timestamp - b.timestamp);
  }

  /** Get the lineage chain for a root decision. */
  getLineage(rootDecisionId: string): LineageChain | undefined {
    return this.chains.get(rootDecisionId);
  }

  /** Query decisions by involved entity. */
  getDecisionsByEntity(entityName: string): DecisionRecord[] {
    return this.decisions.filter((d) =>
      d.entitiesInvolved.includes(entityName),
    );
  }

  /** Reset all data. */
  reset(): void {
    this.decisions = [];
    this.chains.clear();
  }

  /** Get stats. */
  getStats(): { totalDecisions: number; chains: number; avgDepth: number } {
    const chains = [...this.chains.values()];
    return {
      totalDecisions: this.decisions.length,
      chains: chains.length,
      avgDepth: chains.length > 0
        ? chains.reduce((s, c) => s + c.depth, 0) / chains.length
        : 0,
    };
  }
}

// ── CausalGraph ──────────────────────────────────────────────────────────

export class CausalGraph {
  private events = new Map<string, CausalEvent>();
  private links: CausalLink[] = [];

  /** Add a causal link between two events. */
  addCausalLink(cause: CausalEvent, effect: CausalEvent, sessionId?: string): void {
    this.events.set(cause.id, {
      ...cause,
      type: this.events.has(cause.id)
        ? "both"
        : "cause",
    });
    this.events.set(effect.id, {
      ...effect,
      type: this.events.has(effect.id)
        ? "both"
        : "effect",
    });

    this.links.push({
      cause,
      effect,
      confidence: 0.85,
      sessionId: sessionId ?? "",
      timestamp: Date.now(),
    });
  }

  /** Query causal relationships for an event (both as cause and effect). */
  queryCausality(eventId: string): CausalLink[] {
    return this.links.filter(
      (l) => l.cause.id === eventId || l.effect.id === eventId,
    );
  }

  /** Get the causal chain starting from an event (transitive closure). */
  getCausalChain(eventId: string): CausalLink[] {
    const visited = new Set<string>();
    const result: CausalLink[] = [];
    const queue = [eventId];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);

      const related = this.queryCausality(current);
      for (const link of related) {
        if (!result.includes(link)) result.push(link);
        if (link.cause.id === current && !visited.has(link.effect.id)) {
          queue.push(link.effect.id);
        }
      }
    }

    return result;
  }

  /** Get events that could be root causes (no incoming causal links). */
  getRootCauses(): CausalEvent[] {
    const hasIncoming = new Set<string>();
    for (const link of this.links) {
      hasIncoming.add(link.effect.id);
    }
    return [...this.events.values()].filter((e) => !hasIncoming.has(e.id));
  }

  /** Reset all data. */
  reset(): void {
    this.events.clear();
    this.links = [];
  }

  /** Get stats. */
  getStats(): { eventCount: number; causalLinkCount: number } {
    return { eventCount: this.events.size, causalLinkCount: this.links.length };
  }
}

// ── MemoryRelationshipEnhancer (facade) ──────────────────────────────────

export class MemoryRelationshipEnhancer {
  readonly entityChaining: EntityChaining;
  readonly decisionLineage: DecisionLineage;
  readonly causalGraph: CausalGraph;

  constructor() {
    this.entityChaining = new EntityChaining();
    this.decisionLineage = new DecisionLineage();
    this.causalGraph = new CausalGraph();
  }

  /** Enhance memory records with relationship metadata. */
  enhance(memories: Array<{ id: string; text: string; tags?: string[] }>): void {
    const keywords = memories.flatMap((m) =>
      (m.tags ?? []).concat(this.extractEntities(m.text)),
    );

    // Link co-occurring entities
    for (let i = 0; i < keywords.length; i++) {
      for (let j = i + 1; j < keywords.length; j++) {
        if (keywords[i] !== keywords[j]) {
          this.entityChaining.linkEntities(keywords[i], keywords[j]);
        }
      }
    }
  }

  /** Reset all subsystems. */
  reset(): void {
    this.entityChaining.reset();
    this.decisionLineage.reset();
    this.causalGraph.reset();
  }

  private extractEntities(text: string): string[] {
    // Extract potential entity names (capitalized words, technical terms)
    const words = text.match(/\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b/g) ?? [];
    const techTerms = text.match(
      /\b(?:TypeScript|JavaScript|Python|Rust|Go|React|Node\.js|SQL|Docker|Kubernetes|openclaw|claw-mem|claw-ctx)\b/gi,
    ) ?? [];
    return [...new Set([...words, ...techTerms.map((t) => t.toLowerCase())])];
  }
}
