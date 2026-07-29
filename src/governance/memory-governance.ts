/**
 * claw-mem v6.41.0 — Memory Governance API
 * Policy-based memory lifecycle management (store / maintain / forget).
 */

export interface GovernedEntry {
  id: string;
  content: string;
  importanceScore: number;
  accessCount: number;
  createdAt: number;    // timestamp ms
  lastAccessedAt: number;
  size?: number;        // bytes
}

export type PolicyDecision = { store: boolean; priority?: number; reason?: string };
export type MaintainDecision = "keep" | "refresh" | "forget";

export interface GovernancePolicy {
  name: string;
  select(entry: GovernedEntry): PolicyDecision;
  maintain(entry: GovernedEntry): MaintainDecision;
  forget(entry: GovernedEntry): boolean;
}

export class MemoryGovernanceManager {
  private policies: GovernancePolicy[] = [];

  constructor(policies?: GovernancePolicy[]) {
    if (policies) this.policies = [...policies];
  }

  addPolicy(policy: GovernancePolicy): void {
    this.policies.push(policy);
  }

  removePolicy(name: string): void {
    this.policies = this.policies.filter(p => p.name !== name);
  }

  evaluate(entry: GovernedEntry): PolicyDecision {
    for (const policy of this.policies) {
      const decision = policy.select(entry);
      if (!decision.store) return decision;
    }
    return { store: true, reason: "all policies passed" };
  }

  evaluateAll(entry: GovernedEntry): PolicyDecision[] {
    return this.policies.map(p => p.select(entry));
  }

  getPolicies(): GovernancePolicy[] {
    return [...this.policies];
  }
}

export class DefaultGovernancePolicy implements GovernancePolicy {
  name = "default";
  private minImportance: number;
  private maxSize: number;
  private forgetAgeDays: number;

  constructor(options?: { minImportance?: number; maxSize?: number; forgetAgeDays?: number }) {
    this.minImportance = options?.minImportance ?? 0.3;
    this.maxSize = options?.maxSize ?? 1_000_000;
    this.forgetAgeDays = options?.forgetAgeDays ?? 180;
  }

  select(entry: GovernedEntry): PolicyDecision {
    if (entry.importanceScore < this.minImportance) {
      return { store: false, reason: "importance below threshold" };
    }
    if (entry.size && entry.size > this.maxSize) {
      return { store: false, reason: "size exceeds limit" };
    }
    return { store: true, priority: entry.importanceScore };
  }

  maintain(entry: GovernedEntry): MaintainDecision {
    const ageDays = (Date.now() - entry.createdAt) / (1000 * 60 * 60 * 24);
    if (entry.accessCount === 0 && ageDays > 30) return "forget";
    if (ageDays > 90) return "refresh";
    return "keep";
  }

  forget(entry: GovernedEntry): boolean {
    const ageDays = (Date.now() - entry.createdAt) / (1000 * 60 * 60 * 24);
    return entry.importanceScore < this.minImportance || ageDays > this.forgetAgeDays;
  }
}
