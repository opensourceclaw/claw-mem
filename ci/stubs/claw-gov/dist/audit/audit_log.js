"use strict";
let auditIdCounter = 0;
class AuditLog {
  constructor() {
    this.entries = [];
    this.maxEntries = 10000;
  }
  record(params) {
    const entry = Object.assign({ id: `audit-${++auditIdCounter}`, timestamp: Date.now() }, params);
    this.entries.push(entry);
    if (this.entries.length > this.maxEntries) this.entries = this.entries.slice(-this.maxEntries);
    return entry;
  }
  query(filters) {
    let results = this.entries;
    if (filters.action) results = results.filter((e) => e.action === filters.action);
    if (filters.agent) results = results.filter((e) => e.agent === filters.agent);
    if (filters.outcome) results = results.filter((e) => e.outcome === filters.outcome);
    if (filters.since != null) results = results.filter((e) => e.timestamp >= filters.since);
    return results.slice(-(filters.limit ?? 50));
  }
  getStats() {
    const actionCounts = new Map();
    let blocked = 0;
    let failures = 0;
    for (const e of this.entries) {
      if (e.outcome === "blocked") blocked++;
      if (e.outcome === "failure") failures++;
      actionCounts.set(e.action, (actionCounts.get(e.action) ?? 0) + 1);
    }
    const topActions = [...actionCounts.entries()]
      .map(([action, count]) => ({ action, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
    return { total: this.entries.length, blocked, failures, topActions };
  }
  reset() {
    this.entries = [];
  }
}
module.exports = { AuditLog };
