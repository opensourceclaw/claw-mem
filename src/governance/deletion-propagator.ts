/**
 * claw-mem v6.41.0 — Deletion Propagator
 * Cascade-delete with relationship graph, cycle detection, and audit logging.
 */

import type { AuditTrail } from "./audit-trail.js";

export interface EntityNode {
  id: string;
  type: string;
}

export interface EntityLink {
  source: string;
  target: string;
  type: string;
}

export interface CascadeOptions {
  maxDepth?: number;
  dryRun?: boolean;
  audit?: boolean;
}

export interface DeletionResult {
  deleted: string[];
  skipped: string[];
  errors: Array<{ entity: string; reason: string }>;
  cycleWarnings: string[];
}

export class EntityRelationshipGraph {
  private children = new Map<string, Set<string>>();
  private parents = new Map<string, Set<string>>();
  private entities = new Map<string, EntityNode>();

  addEntity(entity: EntityNode): void {
    this.entities.set(entity.id, entity);
    if (!this.children.has(entity.id)) this.children.set(entity.id, new Set());
    if (!this.parents.has(entity.id)) this.parents.set(entity.id, new Set());
  }

  addRelation(relation: EntityLink): void {
    if (!this.children.has(relation.source)) this.children.set(relation.source, new Set());
    this.children.get(relation.source)!.add(relation.target);
    if (!this.parents.has(relation.target)) this.parents.set(relation.target, new Set());
    this.parents.get(relation.target)!.add(relation.source);
  }

  getChildren(entityId: string): EntityLink[] {
    const links = this.children.get(entityId);
    if (!links) return [];
    return Array.from(links).map(target => ({ source: entityId, target, type: "related" }));
  }

  getParents(entityId: string): EntityLink[] {
    const links = this.parents.get(entityId);
    if (!links) return [];
    return Array.from(links).map(source => ({ source, target: entityId, type: "related" }));
  }

  detectCycles(): string[] {
    const visited = new Set<string>();
    const path = new Set<string>();
    const cycles: string[] = [];

    const dfs = (node: string): void => {
      visited.add(node);
      path.add(node);
      const children = this.children.get(node);
      if (children) {
        for (const child of children) {
          if (path.has(child)) {
            cycles.push(`${node} -> ${child}`);
          } else if (!visited.has(child)) {
            dfs(child);
          }
        }
      }
      path.delete(node);
    };

    for (const node of this.entities.keys()) {
      if (!visited.has(node)) dfs(node);
    }
    return cycles;
  }
}

export class DeletionPropagator {
  private graph: EntityRelationshipGraph;
  private auditTrail: AuditTrail;

  constructor(graph: EntityRelationshipGraph, audit: AuditTrail) {
    this.graph = graph;
    this.auditTrail = audit;
  }

  async propagate(entityId: string, options?: CascadeOptions): Promise<DeletionResult> {
    const maxDepth = options?.maxDepth ?? 5;
    const dryRun = options?.dryRun ?? false;
    const audit = options?.audit ?? true;

    const result: DeletionResult = { deleted: [], skipped: [], errors: [], cycleWarnings: [] };

    const cycles = this.graph.detectCycles();
    if (cycles.length > 0) {
      result.cycleWarnings = cycles;
    }

    const toDelete = new Set<string>();
    const queue: Array<{ id: string; depth: number }> = [{ id: entityId, depth: 0 }];

    while (queue.length > 0) {
      const { id, depth } = queue.shift()!;
      if (toDelete.has(id)) continue;
      if (depth > maxDepth) {
        result.skipped.push(id);
        continue;
      }
      toDelete.add(id);

      for (const child of this.graph.getChildren(id)) {
        if (!toDelete.has(child.target)) {
          queue.push({ id: child.target, depth: depth + 1 });
        }
      }
    }

    if (!dryRun) {
      for (const id of toDelete) {
        try {
          result.deleted.push(id);
          if (audit) {
            this.auditTrail.record({
              operation: "delete",
              entity: id,
              source: "DeletionPropagator",
              reason: `cascade from ${entityId}`,
            });
          }
        } catch (err) {
          result.errors.push({ entity: id, reason: err instanceof Error ? err.message : "unknown" });
        }
      }
    } else {
      result.deleted = Array.from(toDelete);
    }

    return result;
  }

  async preview(entityId: string): Promise<EntityNode[]> {
    const result = await this.propagate(entityId, { dryRun: true });
    return result.deleted.map(id => ({ id, type: "unknown" }));
  }
}
