export interface ReflectionMetrics {
  total_behaviors_logged: number;
  total_assessments: number;
  anomalies_detected: number;
  last_reflection: string;
}

export interface Action {
  action_type: string;
  target: string;
  parameters: Record<string, unknown>;
  context: Record<string, unknown> | null;
  timestamp: string;
}

export class SelfReflection {
  constructor(config?: Record<string, unknown>);
  getReflectionMetrics(): ReflectionMetrics;
  monitorBehavior(
    action: Action,
    result: string,
    success?: boolean,
    latencyMs?: number,
    metadata?: Record<string, unknown>,
  ): void;
}

export function createAction(
  target: string,
  type?: string,
  ctx?: Record<string, unknown> | null,
): Action;

export { AuditLog } from "./audit/audit_log";
export type { AuditEntry } from "./audit/audit_log";
