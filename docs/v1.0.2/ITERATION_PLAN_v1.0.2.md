# claw-mem v1.0.2 Iteration Plan

**Version:** 1.0  
**Created:** 2026-03-24  
**Status:** 📋 Planning  
**Priority:** P0 (Critical)  
**Component:** Memory System Enhancement  
**License:** Apache-2.0  
**Documentation Standard:** 100% English (Apache International Open Source Standard)  

---

## Executive Summary

claw-mem v1.0.2 focuses on **critical memory system improvements** to address repeated forgetting of important rules and principles. This iteration is essential for restoring user trust and system reliability.

**Core Objective:** Eliminate repeated forgetting of critical rules, restore user trust and system reliability.

---

## Problem Statement

### Current Issues

| Issue | Frequency | Impact | Severity |
|-------|-----------|--------|----------|
| **Forgotten Package Names** | 3+ times | Wasted time, frustration | High |
| **Wrong Documentation Language** | 2+ times | Apache compliance risk | Critical |
| **Incorrect Release Process** | 2+ times | Delayed releases | High |
| **No Pre-Action Verification** | Every action | Preventable errors | Critical |
| **No Critical Rule Tagging** | Always | Rules forgotten easily | High |

### Root Causes

1. **No Priority System** - All memories treated equally
2. **No Active Recall** - Memories not checked before actions
3. **No Reinforcement** - Corrections not strengthened
4. **No Confidence Scoring** - Can't distinguish certain/uncertain
5. **No Source Tracking** - Can't verify memory origin

---

## Iteration Goals

### Primary Goals

1. ✅ **Critical Rule Tagging** - Mark and prioritize critical rules
2. ✅ **Pre-Action Memory Check** - Verify before significant actions
3. ✅ **Memory Reinforcement** - Strengthen repeated corrections
4. ✅ **Confidence Scoring** - Score memory reliability (0-100%)
5. ✅ **Source Tracking** - Track memory origin (user/inferred)

### Success Metrics

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| **Critical Rule Recall** | ~70% | 100% | +30% |
| **Repeated Mistakes** | 3+ times | 0 times | -100% |
| **Pre-Action Verification** | 0% | 100% | New |
| **Memory Confidence** | N/A | >95% | New |
| **User Satisfaction** | 7/10 | 9/10 | +28% |

---

## Features

### Feature 1: Critical Rule Tagging (FR-1)

**Description:** Allow marking memories as "critical rules" with highest priority.

**Requirements:**
- [ ] User can mark memory as "critical"
- [ ] Critical rules stored separately
- [ ] Critical rules reviewed before every action
- [ ] Critical rules persist across 10+ sessions

**Implementation:**
```python
class Memory:
    is_critical: bool  # NEW
    priority: int  # NEW: 1-5 (5=critical)
```

**Acceptance Criteria:**
- [ ] User can mark rule as critical via command
- [ ] Critical rules recalled 100% of the time
- [ ] Critical rules persist across sessions

---

### Feature 2: Pre-Action Memory Check (FR-2)

**Description:** Check relevant memories before executing significant actions.

**Requirements:**
- [ ] System checks memories before actions
- [ ] Verify against critical rules
- [ ] Ask for confirmation if uncertain
- [ ] Prevent actions that violate critical rules

**Implementation:**
```python
def pre_action_check(action: str, context: dict) -> CheckResult:
    # 1. Retrieve relevant memories
    # 2. Check critical rules
    # 3. Check confidence
    # 4. Return result
```

**Acceptance Criteria:**
- [ ] Pre-action check adds <100ms latency
- [ ] Violations detected 100% of the time
- [ ] User asked for confirmation when uncertain

---

### Feature 3: Memory Reinforcement (FR-3)

**Description:** Strengthen memories through repeated use and corrections.

**Requirements:**
- [ ] Repeated corrections strengthen memory
- [ ] Forgotten info flagged for review
- [ ] Confidence increases with successful use
- [ ] Periodic memory review

**Implementation:**
```python
def reinforce_memory(memory_id: str, success: bool):
    memory = get_memory(memory_id)
    if success:
        memory.confidence += 0.05
    else:
        memory.confidence -= 0.2
        memory.flagged_for_review = True
```

**Acceptance Criteria:**
- [ ] Confidence increases with successful use
- [ ] Failed memories flagged for review
- [ ] Review queue generated daily

---

### Feature 4: Confidence Scoring (FR-4)

**Description:** Each memory has confidence score (0-100%).

**Requirements:**
- [ ] Confidence score 0-100%
- [ ] Low-confidence memories verified
- [ ] Score increases with successful use
- [ ] Score decreases with failures

**Confidence Calculation:**
```
confidence = base_score + use_bonus + success_bonus - penalty

Where:
- base_score = 0.5 (50% for new memories)
- use_bonus = min(0.3, use_count * 0.01)
- success_bonus = min(0.2, success_rate * 0.2)
- penalty = failure_count * 0.1
```

**Acceptance Criteria:**
- [ ] All memories have confidence score
- [ ] Low-confidence (<80%) verified before use
- [ ] Score accurately reflects reliability

---

### Feature 5: Source Tracking (FR-5)

**Description:** Track memory origin for verification.

**Requirements:**
- [ ] Track source (user/inferred/system)
- [ ] User-instructed memories highest priority
- [ ] Inferred memories verified with user
- [ ] Source visible in memory details

**Source Types:**
| Source | Priority | Auto-Verify |
|--------|----------|-------------|
| `user` | 5 (Critical) | No |
| `inferred` | 3 (Medium) | Yes |
| `system` | 1 (Low) | Yes |

**Acceptance Criteria:**
- [ ] All memories have source tracked
- [ ] User memories have highest priority
- [ ] Inferred memories verified

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goals:**
- [ ] Memory schema updated (is_critical, confidence, source)
- [ ] Critical rule tagging implemented
- [ ] Memory storage upgraded

**Deliverables:**
- Updated Memory class
- Critical rule API
- Migration script for existing memories

### Phase 2: Pre-Action Check (Week 3-4)

**Goals:**
- [ ] Pre-action check system implemented
- [ ] Critical rule verification
- [ ] Confirmation dialog for uncertain actions

**Deliverables:**
- pre_action_check() function
- Integration with action system
- User confirmation UI

### Phase 3: Reinforcement (Week 5-6)

**Goals:**
- [ ] Memory reinforcement mechanism
- [ ] Confidence scoring
- [ ] Source tracking

**Deliverables:**
- reinforce_memory() function
- Confidence calculation
- Source tracking system

### Phase 4: Testing & Polish (Week 7-8)

**Goals:**
- [ ] Unit tests (90%+ coverage)
- [ ] Integration tests
- [ ] User acceptance testing

**Deliverables:**
- Test suite
- Performance benchmarks
- User documentation

---

## Testing Strategy

### Unit Tests

| Test | Coverage | Status |
|------|----------|--------|
| Critical rule tagging | 100% | 📋 TODO |
| Pre-action check | 100% | 📋 TODO |
| Confidence scoring | 100% | 📋 TODO |
| Memory reinforcement | 100% | 📋 TODO |
| Source tracking | 100% | 📋 TODO |

### Integration Tests

| Test | Scenario | Status |
|------|----------|--------|
| Cross-session persistence | Critical rules persist 10+ sessions | 📋 TODO |
| Pre-action verification | Prevents rule violations | 📋 TODO |
| Reinforcement mechanism | Confidence increases correctly | 📋 TODO |

### User Acceptance Tests

| Test | Criteria | Status |
|------|----------|--------|
| Critical rule retention | 10 rules, 10 sessions, 100% recall | 📋 TODO |
| Error reduction | No repeated mistakes | 📋 TODO |
| User satisfaction | Score >9/10 | 📋 TODO |

---

## Success Metrics

### Technical Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Critical Rule Recall** | ~70% | 100% | Test across 10 sessions |
| **Pre-Action Check Latency** | N/A | <100ms | Performance benchmark |
| **Memory Confidence Accuracy** | N/A | >95% | Compare score vs actual |
| **Error Reduction** | 3+ repeats | 0 repeats | Count repeated mistakes |

### User Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **User Satisfaction** | 7/10 | 9/10 | Post-release survey |
| **Trust Score** | N/A | >8/10 | Trust questionnaire |
| **Efficiency Gain** | N/A | -50% time | Time spent re-explaining |

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Performance Degradation** | High | Medium | Optimize memory retrieval, add caching |
| **False Positives** | Medium | Medium | Tune confidence thresholds |
| **User Annoyance** | Medium | Low | Make confirmations optional for trusted actions |
| **Migration Issues** | High | Low | Backup memories, rollback plan |

---

## Documentation

### New Documentation

- [ ] `docs/CRITICAL_RULES.md` - How to mark and manage critical rules
- [ ] `docs/MEMORY_CONFIDENCE.md` - Understanding confidence scoring
- [ ] `docs/PRE_ACTION_CHECK.md` - How pre-action verification works
- [ ] `docs/MEMORY_REINFORCEMENT.md` - Memory reinforcement mechanism

### Updated Documentation

- [ ] `README.md` - Add v1.0.2 features
- [ ] `RELEASE_NOTES_v1.0.2.md` - Complete release notes
- [ ] `ARCHITECTURE_DECISION_001.md` - Update with new features

---

## Release Plan

### Timeline

| Phase | Duration | Dates | Status |
|-------|----------|-------|--------|
| **Phase 1: Foundation** | 2 weeks | 2026-03-25 to 04-07 | 📋 Planned |
| **Phase 2: Pre-Action Check** | 2 weeks | 2026-04-08 to 04-21 | 📋 Planned |
| **Phase 3: Reinforcement** | 2 weeks | 2026-04-22 to 05-05 | 📋 Planned |
| **Phase 4: Testing** | 2 weeks | 2026-05-06 to 05-19 | 📋 Planned |
| **Release** | - | 2026-05-20 | 📋 Planned |

### Release Checklist

- [ ] All features implemented
- [ ] All tests passing (100%)
- [ ] Performance benchmarks met
- [ ] Documentation complete (100% English)
- [ ] User acceptance testing passed
- [ ] Release notes ready

---

## Team & Responsibilities

| Role | Person | Responsibilities |
|------|--------|------------------|
| **Product Owner** | Peter Cheng | Requirements, priorities, approval |
| **Lead Developer** | Friday | Implementation, testing, documentation |
| **QA** | Automated Tests | Test coverage, quality gates |

---

## Contact

**Repository:** https://github.com/opensourceclaw/claw-mem  
**Issues:** https://github.com/opensourceclaw/claw-mem/issues  
**Documentation:** `/Users/liantian/workspace/claw-mem/docs/`  

---

## Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-03-24 | Initial iteration plan | Friday |

---

*Document Created: 2026-03-24T14:30+08:00*  
*Version: 1.0*  
*Status: 📋 Planning*  
*Priority: P0 (Critical)*  
*Target Release: v1.0.2*  
*License: Apache-2.0*  
*Documentation Language: 100% English (Apache Standard)*
