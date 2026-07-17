// Copyright 2026 Peter Cheng
// Licensed under the Apache License, Version 2.0

/**
 * claw-mem v6.40.0 — MemoryEntityManager
 *
 * Entity management with deletion propagation and audit trail.
 * Uses claw-gov AuditLog for tracking.
 */

// Direct import from claw-gov dist (subpath exports not configured)
import { AuditLog } from "claw-gov/dist/audit/audit_log";
import type { AuditEntry } from "claw-gov/dist/audit/audit_log";

// Re-export for convenience
export type { AuditEntry };

/**
 * MemoryEntityManager — Manages entity-memory relationships with audit trail.
 */
export class MemoryEntityManager {
  private auditLog: AuditLog;
  private entityRelations: Map<string, Set<string>>; // entityId -> memoryIds

  constructor() {
    this.auditLog = new AuditLog();
    this.entityRelations = new Map();
  }

  /**
   * Register memory-entity relationship.
   * @param memoryId - Memory ID
   * @param entityId - Entity ID
   */
  linkEntity(memoryId: string, entityId: string): void {
    if (!this.entityRelations.has(entityId)) {
      this.entityRelations.set(entityId, new Set());
    }
    this.entityRelations.get(entityId)!.add(memoryId);
  }

  /**
   * Unregister memory-entity relationship.
   * @param memoryId - Memory ID
   * @param entityId - Entity ID
   */
  unlinkEntity(memoryId: string, entityId: string): void {
    const memories = this.entityRelations.get(entityId);
    if (memories) {
      memories.delete(memoryId);
      if (memories.size === 0) {
        this.entityRelations.delete(entityId);
      }
    }
  }

  /**
   * Delete entity and propagate to related memories.
   * @param entityId - Entity to delete
   * @returns List of affected memory IDs
   */
  deleteEntity(entityId: string): string[] {
    const affectedMemories = this.entityRelations.get(entityId);

    // Record to audit trail
    this.auditLog.record({
      action: "delete_entity",
      agent: "MemoryEntityManager",
      sessionId: "system",
      outcome: "success",
      details: `Deleted entity ${entityId}`,
      metadata: { entityId, affectedCount: affectedMemories?.size ?? 0 }
    });

    this.entityRelations.delete(entityId);
    return affectedMemories ? [...affectedMemories] : [];
  }

  /**
   * Get memories linked to an entity.
   * @param entityId - Entity ID
   * @returns Array of memory IDs
   */
  getEntityMemories(entityId: string): string[] {
    const memories = this.entityRelations.get(entityId);
    return memories ? [...memories] : [];
  }

  /**
   * Get entity count.
   */
  getEntityCount(): number {
    return this.entityRelations.size;
  }

  /**
   * Get audit trail for entity operations.
   * @param limit - Maximum entries to return
   */
  getEntityAuditLog(limit?: number): AuditEntry[] {
    return this.auditLog.query({ action: "delete_entity", limit });
  }

  /**
   * Get full audit log.
   * @param filters - Query filters
   */
  queryAuditLog(filters?: {
    action?: string;
    agent?: string;
    outcome?: AuditEntry["outcome"];
    since?: number;
    limit?: number;
  }): AuditEntry[] {
    return this.auditLog.query(filters ?? {});
  }

  /**
   * Get audit statistics.
   */
  getAuditStats(): {
    total: number;
    blocked: number;
    failures: number;
    topActions: Array<{ action: string; count: number }>;
  } {
    return this.auditLog.getStats();
  }
}
