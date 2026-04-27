# Architecture Decision Record 001

**Title:** Memory System Architecture: Skill vs Plugin  
**Status:** ✅ Accepted (Skill for v1.0, Plugin under evaluation for v2.0)  
**Date:** 2026-03-24  
**Author:** Friday (with Peter Cheng)  
**Project:** claw-mem → NeoMem  
**License:** Apache-2.0  
**Documentation Standard:** 100% English (Apache International Open Source Standard)  

---

## Executive Summary

This document records the architectural decision to implement claw-mem's memory system as an **AgentSkill** rather than an **OpenClaw Plugin**, including the rationale, trade-offs, and future migration considerations.

**Key Insight:**
> Skill architecture was appropriate for v1.0 (rapid iteration, independence), but Plugin architecture should be evaluated for v2.0 as memory is core infrastructure, not a feature extension.

---

## 1. Context

### 1.1 Decision Timing

- **Decision Date:** 2026-03-18 (initial implementation)
- **Review Date:** 2026-03-24 (architectural discussion with Peter)
- **Project Phase:** claw-mem v0.8.0 → NeoMem v1.0 planning

### 1.2 Technical Environment

| Component | Version/State |
|-----------|---------------|
| OpenClaw | 2026.3.22 (Plugin architecture recently upgraded) |
| AgentSkills | Stable, well-documented |
| claw-mem | v0.8.0 (Skill-based implementation) |

### 1.3 Core Question

> Should claw-mem's memory system be implemented as:
> - **Option A:** AgentSkill (external module, loaded on-demand)
> - **Option B:** OpenClaw Plugin (core-integrated, always resident)

---

## 2. Decision: Skill Architecture for v1.0

### 2.1 Rationale (Why Skill?)

#### 2.1.1 Development Timing & Maturity

- **Plugin architecture was still evolving** when claw-mem development started (2026-03-18)
- **AgentSkills specification was stable** with clear SKILL.md standards
- **Rapid iteration** possible without waiting for core architecture stabilization

#### 2.1.2 Independence & Portability

- Skill is a **self-contained module**, can be tested and deployed independently
- **Easy migration to other AI systems** (not bound to OpenClaw kernel)
- Aligns with **"loose coupling"** design principle

#### 2.1.3 Security & Permission Boundaries

- Skill runs in **sandboxed environment** with restricted permissions
- Memory involves sensitive data; **isolation was considered safer** at the time
- Avoids accidental damage to core system

#### 2.1.4 Community Ecosystem

- AgentSkills is the **recommended extension mechanism** by OpenClaw
- Skills on ClawHub are published in Skill format
- Easier for others to **reuse and contribute**

---

## 3. Trade-offs & Limitations

### 3.1 Skill Architecture Pain Points

| Issue | Description | Impact |
|-------|-------------|--------|
| **Lifecycle Management** | Skill is temporarily loaded, state not persistent | Memory needs persistent connection |
| **Performance Overhead** | Each call requires loading Skill context | Increased latency, affects UX |
| **Deep Integration** | Cannot directly access OpenClaw kernel APIs | Some features require workarounds |
| **Event Response** | Passive invocation, cannot actively listen to system events | Cannot respond to memory-related events in real-time |
| **Resource Competition** | Multiple Skills may load same dependencies repeatedly | Wastes resources |

### 3.2 Core Insight from Peter

> "Memory, as a core capability component, should theoretically work closely with OpenClaw's kernel, not as a skill extension."

**Assessment:** This insight is **correct from a long-term architectural perspective**.

---

## 4. Plugin Architecture Analysis

### 4.1 Advantages

| Advantage | Description |
|-----------|-------------|
| **Lifecycle Alignment** | Loaded at boot, resident in memory |
| **Direct Kernel API Access** | No intermediate layer required |
| **Event-Driven** | Can subscribe to system events (session creation, message sending) |
| **Resource Sharing** | Share connection pools, caches with other Plugins |
| **Unified Configuration** | Configured in `config.yml` centrally |

### 4.2 Conceptual Positioning

Memory should be treated as **infrastructure**, similar to:
- File system
- Network stack
- Session management

**Not** as a "feature extension".

---

## 5. Future Evolution Path

### 5.1 Short-term (Before NeoMem v1.0)

- **Maintain Skill architecture**, optimize internal implementation
- Implement **quasi-resident state** via cron + heartbeat
- Use **external storage** (SQLite/Redis) for persistence

### 5.2 Mid-term (NeoMem v2.0)

- **Migrate to Plugin architecture** (if OpenClaw supports)
- Become an **official OpenClaw Memory Plugin**
- Support **multi-backend storage** (local, cloud, distributed)

### 5.3 Long-term (Project Neo Phase 1 Complete)

- **Independent Service** - NeoMem can run as a standalone service
- Communicate with OpenClaw via **gRPC/REST API**
- Support **multi-AI system integration** (not limited to OpenClaw)

---

## 6. Migration Evaluation Criteria

Before migrating from Skill to Plugin architecture, evaluate:

| Criterion | Question | Threshold |
|-----------|----------|-----------|
| **Performance Gain** | How much latency reduction? | >30% improvement |
| **Feature Enablement** | What new features become possible? | Must enable P0 features |
| **Migration Cost** | How many person-days? | <5 days |
| **Backward Compatibility** | Can existing users upgrade seamlessly? | Must be seamless |
| **OpenClaw Stability** | Is Plugin API stable? | API frozen for 6+ months |

---

## 7. Related Documents

- `README.md` - Project overview
- `../RELEASE_NOTES_v0.8.0.md` - Current release notes
- `/Users/liantian/workspace/neoclaw/docs/Project_Neo_Engineering_Handbook.md` - HKAA architecture
- OpenClaw Plugin Architecture Documentation (TBD)

---

## 8. Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-03-24 | Initial architecture decision record | Friday |

---

## 9. Conclusion

**Original decision was reasonable** (based on constraints at the time), but **the challenge is valid** (from long-term architectural perspective).

**Recommended Actions:**
1. Complete NeoMem v1.0 (Skill architecture)
2. Research OpenClaw 2026.3.22 Plugin architecture capabilities
3. Evaluate migration cost/benefit in v2.0 planning
4. If benefits are clear, **migrate to Plugin architecture decisively**

---

*Document Created: 2026-03-24T00:19+08:00 (v1.0)*  
*Project: claw-mem → NeoMem*  
*Discussion Participants: Peter Cheng, Friday*  
*License: Apache-2.0*  
*Documentation Language: 100% English (Apache Standard)*  
*"Ad Astra Per Aspera"*
