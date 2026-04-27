# Issue: Memory System Improvement - Critical Release Process Recall

**Issue ID:** claw-mem-002  
**Created:** 2026-03-24  
**Priority:** P0 (Critical)  
**Status:** 📋 New  
**Component:** Memory System  
**Affects Version:** v0.8.0  
**Fixed Version:** v0.9.0 (planned)  

---

## Problem Description

The AI assistant (Friday) repeatedly forgets critical project information and principles despite being told multiple times. This causes:

1. **Repeated mistakes** - Same errors occur multiple times
2. **User frustration** - User must repeat instructions
3. **Efficiency loss** - Time wasted re-explaining known information
4. **Trust issues** - Reduces confidence in the memory system

### Specific Incidents

**Incident 1: Package Naming**
- **Told:** Package name should be `claw_rl` (not `neorl` or `neomind`)
- **Mistake:** Changed to `neorl` without asking
- **Correction:** User had to correct multiple times

**Incident 2: Documentation Language**
- **Told:** Apache standard requires 100% English for public documentation
- **Mistake:** Created bilingual (Chinese+English) release docs
- **Correction:** User reminded multiple times about this rule

**Incident 3: GitHub Repository Actions**
- **Told:** AI should create repo and push code itself
- **Mistake:** Asked user to create repo and push
- **Correction:** User had to remind about previous instructions

---

## Root Cause Analysis

### Current Memory Limitations

1. **Short-term memory only** - Conversations not persisted effectively
2. **No priority tagging** - Critical rules not marked as high-priority
3. **No periodic review** - Old memories not reviewed/reinforced
4. **Context window limits** - Important info falls out of context
5. **No active recall** - Memory not proactively checked before actions

### Technical Gaps

| Gap | Impact | Severity |
|-----|--------|----------|
| No critical rule tagging | Rules forgotten easily | High |
| No memory reinforcement | Old info not retained | High |
| No pre-action memory check | Mistakes not prevented | Critical |
| No memory confidence scoring | Can't distinguish certain/uncertain | Medium |
| No memory source tracking | Can't verify info origin | Medium |

---

## Requirements

### Functional Requirements

#### FR-1: Critical Rule Tagging
- System must allow marking memories as "critical rules"
- Critical rules must be reviewed before every action
- Critical rules must persist across sessions

#### FR-2: Pre-Action Memory Check
- Before executing significant actions, system must check relevant memories
- System must verify action against critical rules
- System must ask for confirmation if uncertainty detected

#### FR-3: Memory Reinforcement
- Important memories must be periodically reviewed
- Repeated corrections must strengthen memory weight
- Forgotten info must be flagged for reinforcement

#### FR-4: Memory Confidence Scoring
- Each memory must have confidence score (0-100%)
- Low-confidence memories must be verified before use
- Confidence must increase with successful use

#### FR-5: Memory Source Tracking
- Each memory must track its source (user instruction, inference, etc.)
- User-instructed memories must have highest priority
- Inferred memories must be verified with user

### Non-Functional Requirements

#### NFR-1: Performance
- Memory check must add <100ms latency
- Memory retrieval must complete in <50ms

#### NFR-2: Accuracy
- Critical rules must be remembered 100% of the time
- Memory recall accuracy must be >95%

#### NFR-3: Usability
- User must be able to mark memories as "critical"
- User must be able to review all stored memories

---

## Acceptance Criteria

### AC-1: Critical Rule Retention
- [ ] User can mark a rule as "critical"
- [ ] Critical rules are recalled 100% of the time
- [ ] Critical rules persist across 10+ sessions

### AC-2: Pre-Action Verification
- [ ] System checks memories before significant actions
- [ ] System asks for confirmation if uncertain
- [ ] System prevents actions that violate critical rules

### AC-3: Memory Reinforcement
- [ ] Repeated corrections strengthen memory
- [ ] Forgotten info is flagged for review
- [ ] Memory confidence increases with successful use

### AC-4: Error Reduction
- [ ] Same mistake not repeated more than once
- [ ] User corrections are immediately applied
- [ ] Memory-related errors reduced by 90%

---

## Implementation Plan

### Phase 1: Critical Rule System (v0.9.0)
- Add critical rule tagging
- Implement pre-action memory check
- Add memory confidence scoring

### Phase 2: Memory Reinforcement (v0.10.0)
- Implement periodic memory review
- Add memory weight adjustment
- Create memory source tracking

### Phase 3: Advanced Features (v0.11.0)
- Add memory relationship mapping
- Implement proactive memory suggestions
- Create memory health dashboard

---

## Testing Strategy

### Unit Tests
- Test critical rule tagging
- Test memory confidence scoring
- Test pre-action verification

### Integration Tests
- Test memory persistence across sessions
- Test memory reinforcement mechanism
- Test error reduction over time

### User Acceptance Tests
- User marks 10 critical rules
- System remembers all 10 rules across 10 sessions
- No repeated mistakes observed

---

## Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Critical Rule Recall** | ~70% | 100% | +30% |
| **Repeated Mistakes** | 3+ times | 0 times | -100% |
| **Memory Confidence** | N/A | >95% | New |
| **User Satisfaction** | 7/10 | 9/10 | +28% |

---

## Related Issues

- claw-mem-001: Initial memory system implementation
- claw-mem-003: Memory compression optimization (planned)
- claw-mem-004: Cross-session memory persistence (planned)

---

## References

- [OpenClaw-RL Paper](https://arxiv.org/abs/2603.10165)
- [Memory Enhancement Design](/Users/liantian/workspace/osprojects/claw-rl/docs/MEMORY_ENHANCEMENT.md)
- [Claw-RL Architecture](/Users/liantian/workspace/osprojects/claw-rl/docs/ARCHITECTURE_DECISION_001.md)

---

## Acknowledgments

**Reported by:** Peter Cheng  
**Date:** 2026-03-24  
**Priority:** P0 (Critical)  
**Impact:** High - Affects user trust and system reliability  

---

*Issue Created: 2026-03-24T14:10+08:00*  
*Component: Memory System*  
*Status: 📋 New*  
*Priority: P0 (Critical)*
