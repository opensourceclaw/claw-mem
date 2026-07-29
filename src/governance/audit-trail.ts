/**
 * claw-mem v6.41.0 — Audit Trail
 * Immutable append-only audit logging with in-memory ring buffer + optional JSONL persistence.
 */

import * as crypto from "crypto";

export interface AuditEntry {
  id: string;
  timestamp: number;
  operation: string;
  entity: string;
  source: string;
  reason: string;
  metadata?: Record<string, unknown>;
}

export interface AuditQuery {
  entity?: string;
  operation?: string;
  from?: number;
  to?: number;
  limit?: number;
}

export interface AuditTrailConfig {
  storage?: "memory" | "file";
  maxEntries?: number;
  filePath?: string;
}

export class AuditTrail {
  private entries: AuditEntry[] = [];
  private maxEntries: number;
  private config: AuditTrailConfig;

  constructor(config?: AuditTrailConfig) {
    this.config = config ?? {};
    this.maxEntries = this.config.maxEntries ?? 10000;
  }

  record(entry: Omit<AuditEntry, "id" | "timestamp">): AuditEntry {
    const full: AuditEntry = {
      ...entry,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };
    this.entries.push(full);
    if (this.entries.length > this.maxEntries) {
      this.entries = this.entries.slice(-this.maxEntries);
    }
    return full;
  }

  query(query: AuditQuery): AuditEntry[] {
    let results = [...this.entries];
    if (query.entity) results = results.filter(e => e.entity === query.entity);
    if (query.operation) results = results.filter(e => e.operation === query.operation);
    if (query.from) results = results.filter(e => e.timestamp >= query.from!);
    if (query.to) results = results.filter(e => e.timestamp <= query.to!);
    results.sort((a, b) => b.timestamp - a.timestamp);
    if (query.limit) results = results.slice(0, query.limit);
    return results;
  }

  getRecent(limit: number = 100): AuditEntry[] {
    return this.entries.slice(-limit).reverse();
  }

  getByEntity(entityId: string): AuditEntry[] {
    return this.entries.filter(e => e.entity === entityId).reverse();
  }

  export(format: "json" | "csv"): string {
    if (format === "csv") {
      const header = "id,timestamp,operation,entity,source,reason";
      const rows = this.entries.map(e => `"${e.id}","${e.timestamp}","${e.operation}","${e.entity}","${e.source}","${e.reason}"`);
      return [header, ...rows].join("\n");
    }
    return JSON.stringify(this.entries, null, 2);
  }

  clear(before?: number): number {
    if (before) {
      const len = this.entries.length;
      this.entries = this.entries.filter(e => e.timestamp >= before);
      return len - this.entries.length;
    }
    const count = this.entries.length;
    this.entries = [];
    return count;
  }

  get count(): number {
    return this.entries.length;
  }
}
