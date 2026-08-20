export interface AuditEntry {
  id: string;
  timestamp: number;
  action: string;
  agent: string;
  sessionId: string;
  outcome: "success" | "failure" | "blocked";
  details: string;
  metadata: Record<string, unknown>;
}

export class AuditLog {
  record(params: Omit<AuditEntry, "id" | "timestamp">): AuditEntry;
  query(filters: {
    action?: string;
    agent?: string;
    outcome?: AuditEntry["outcome"];
    since?: number;
    limit?: number;
  }): AuditEntry[];
  getStats(): {
    total: number;
    blocked: number;
    failures: number;
    topActions: Array<{ action: string; count: number }>;
  };
  reset(): void;
}
