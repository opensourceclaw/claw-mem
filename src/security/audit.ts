// Copyright 2026 Peter Cheng
// Licensed under Apache-2.0

/**
 * Audit Logger (MVP Version)
 *
 * Records all memory operations for auditing and debugging.
 * Appends JSONL entries to a log file in the workspace.
 */

import * as fs from "fs";
import * as path from "path";

export interface AuditEntry {
  timestamp: string;
  action: string;
  details: Record<string, unknown>;
}

export class AuditLogger {
  private workspace: string;
  private logFile: string;

  /**
   * @param workspace - Workspace directory path
   */
  constructor(workspace: string) {
    this.workspace = workspace;
    this.logFile = path.join(workspace, ".audit_log.jsonl");
  }

  /**
   * Log an audit entry.
   *
   * @param action  - Action type
   * @param details - Action details
   */
  log(action: string, details: Record<string, unknown>): void {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      action,
      details,
    };

    const dir = path.dirname(this.logFile);
    fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(this.logFile, JSON.stringify(entry) + "\n", "utf-8");
  }

  /**
   * Retrieve audit logs, optionally filtered by action type.
   *
   * @param actionFilter - Optional action type to filter by
   * @param limit        - Maximum number of entries to return (default 100)
   */
  getLogs(actionFilter?: string, limit: number = 100): AuditEntry[] {
    const logs: AuditEntry[] = [];

    if (!fs.existsSync(this.logFile)) {
      return logs;
    }

    const lines = fs.readFileSync(this.logFile, "utf-8").split("\n");
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        const entry: AuditEntry = JSON.parse(line);
        if (actionFilter === undefined || entry.action === actionFilter) {
          logs.push(entry);
          if (logs.length >= limit) break;
        }
      } catch {
        // skip malformed lines
      }
    }

    return logs;
  }

  /**
   * Clear the audit log file.
   */
  clear(): void {
    if (fs.existsSync(this.logFile)) {
      fs.unlinkSync(this.logFile);
    }
  }
}
