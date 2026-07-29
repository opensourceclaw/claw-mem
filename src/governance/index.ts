export { MemoryGovernanceManager, GovernancePolicy, DefaultGovernancePolicy } from "./memory-governance.js";
export type { GovernedEntry, PolicyDecision, MaintainDecision } from "./memory-governance.js";
export { DeletionPropagator, EntityRelationshipGraph } from "./deletion-propagator.js";
export type { EntityNode, EntityLink, CascadeOptions, DeletionResult } from "./deletion-propagator.js";
export { AuditTrail } from "./audit-trail.js";
export type { AuditEntry, AuditQuery, AuditTrailConfig } from "./audit-trail.js";
