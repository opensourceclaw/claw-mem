# claw-mem v0.8.0 Requirements Specification

**Version**: v0.8.0  
**Theme**: User Experience & Intelligence  
**Status**: 📋 Draft  
**Created**: 2026-03-20  
**Authors**: Peter Cheng + Friday  
**Target Release**: 2026-03-25

---

## 📖 Table of Contents

- [Executive Summary](#executive-summary)
- [v0.7.0 Review](#v070-review)
- [Issues and Problems Analysis](#issues-and-problems-analysis)
- [v0.8.0 Vision and Goals](#v080-vision-and-goals)
- [Functional Requirements](#functional-requirements)
- [Non-Functional Requirements](#non-functional-requirements)
- [User Stories](#user-stories)
- [Acceptance Criteria](#acceptance-criteria)
- [Release Plan](#release-plan)
- [Risk Assessment](#risk-assessment)

---

## Executive Summary

### Project Background

claw-mem v0.7.0 was successfully released on 2026-03-19, achieving **performance optimization** goals:
- Startup time: 1.5s → 7.47ms (**191x improvement**)
- Index compression: **82.5% reduction**
- Lazy loading: **0.133ms** initialization
- Exception recovery: automatic backup + corruption recovery

**v0.7.0 Core Achievement**: Solid technical foundation, excellent performance metrics ✅

### v0.8.0 Positioning

Based on feedback from Lingensi Technology exchange and comprehensive product analysis, v0.8.0 focuses on:

> **From "Technically Qualified" → "Product Mature"**

**Core Shift**:
- ❌ No longer pursuing: Extreme performance optimization
- ✅ Instead focusing: User experience, intelligence, community building

### Core Requirements Sources

| Source | Content | Translated Features |
|--------|---------|-------------------|
| **Lingensi Tech Feedback** | High installation barrier, unfriendly error messages | PyPI release, error friendliness |
| **Technical Analysis** | No semantic search, passive memory organization | Importance scoring, auto rules |
| **Product Analysis** | Pre-flight Check not intelligent enough | Auto rule extraction |
| **UX Analysis** | Complex installation, technical error messages | Auto config, Chinese errors |
| **Community Analysis** | Documentation unfriendly to non-technical users | Beginner tutorial series |

---

## v0.7.0 Review

### Completion Status

| Feature | Status | Measured Data |
|---------|--------|---------------|
| Index Persistence | ✅ | No rebuild on restart |
| Lazy Loading | ✅ | 0.133ms initialization |
| Incremental Update | ✅ | 14.16ms/memory |
| Index Compression | ✅ | 82.5% reduction |
| Exception Recovery | ✅ | Auto backup + recovery |
| Integrity Check | ✅ | verify_integrity() |

### Remaining Issues

From v0.7.0 post-release user feedback and code review:

| Issue | Impact | Priority |
|-------|--------|----------|
| Complex installation (Git URL) | Non-technical users cannot install | 🔴 High |
| Technical error messages | Users don't know how to fix | 🔴 High |
| Manual workspace configuration | Config errors cause failures | 🟡 Medium |
| No memory priority in search | Important info may be buried | 🟡 Medium |

---

## Issues and Problems Analysis

### 1. Technical Architecture Issues

#### 1.1 Limited Search Capability

**Problem**:
```
Current: Only N-gram + BM25 keyword matching
Impact: Cannot understand "similar meaning but different words" queries
```

**Examples**:
| User Searches | Current Result | Expected Result |
|--------------|----------------|-----------------|
| "Repo URL" | ✅ Found | ✅ Found |
| "code repository address" | ❌ Not found | ✅ Should find |
| "GitHub link" | ❌ Not found | ✅ Should find |

**v0.8.0 Solution**:
- ✅ Implement memory importance scoring (based on type, frequency, recency)
- ⏳ Vector search (deferred to v0.9.0 as optional module)

---

#### 1.2 Memory Organization Too Passive

**Problem**:
```
Current: Depends on user corrections, no active learning
Impact: Same errors may repeat
```

**Scenario**:
```
User 1st time: ❌ Don't create files to ~/.openclaw/workspace/
AI: OK, remembered.

User 10th time: AI tries to create to ~/.openclaw/workspace/ again
❌ Current: Needs user to correct again
✅ Expected: AI automatically follows previously extracted rules
```

**v0.8.0 Solution**:
- ✅ Auto rule extraction engine
- ✅ Pre-flight Check rule库 auto-update

---

#### 1.3 No Memory Importance Differentiation

**Problem**:
```
Current: All memories treated equally
Impact: Critical information may be buried
```

**Scenario**:
```
User said 10 times: "I like Sichuan food"
User said 1 time: "I'm allergic to peanuts"

❌ Current: Both memories have same weight
✅ Expected: "Allergy" info should have higher priority
```

**v0.8.0 Solution**:
- ✅ Importance scoring algorithm
- ✅ Search results re-ranked by importance
- ✅ Context injection prioritizes high-importance memories

---

### 2. Product Function Issues

#### 2.1 Pre-flight Check Not Intelligent Enough

**Problem**:
```
Current: Static rules, hardcoded check logic
Impact: Cannot adapt to new scenarios, no learning from errors
```

**v0.8.0 Solution**:
- ✅ Auto rule extraction engine
- ✅ Rule confidence evaluation
- ✅ Requires user approval before application (not auto-effective)

---

#### 2.2 Memory Decay Mechanism Missing

**Problem**:
```
Current: Designed but not implemented (Ebbinghaus forgetting curve)
Impact: Memory bloat, increased search noise
```

**Predicted Issue**:
```
After 6 months:
- Memory entries: 1000+
- Effective memories: maybe only 200
- Search noise: 80% irrelevant or outdated info
```

**v0.8.0 Solution**:
- ✅ Implement activation decay mechanism
- ✅ Different decay rates for different types
- ✅ Low-priority memories auto-archived

---

#### 2.3 Missing Visualization and Debug Tools

**Problem**:
```
Current: CLI + Markdown only, no visualization
Impact: Cannot直观 view memory status, hard to debug
```

**User Scenario**:
```
User asks: "Why does AI always forget X?"

❌ Current: Need to manually browse Markdown files
✅ Expected: claw-mem stats to view status
         claw-mem debug to view search logs
```

**v0.8.0 Solution**:
- ✅ CLI stats command (memory status)
- ✅ CLI debug command (search logs)
- ⏳ Web UI (deferred to v1.0.0)

---

### 3. User Experience Issues

#### 3.1 High Installation Barrier

**Problem**:
```
Current: Install from GitHub, need pip install git+...
Impact: Barrier for non-technical users
```

**Comparison**:
```bash
❌ Current:
pip install git+https://github.com/opensourceclaw/claw-mem/claw-mem.git@v0.7.0
# Then manually configure workspace path

✅ Expected:
pip install claw-mem
# Auto-detect OpenClaw configuration
```

**v0.8.0 Solution**:
- ✅ PyPI official release
- ✅ Auto configuration detection
- ✅ Installation wizard (CLI interactive)

---

#### 3.2 Error Messages Not Friendly

**Problem**:
```
Current: Technical error messages, no fix suggestions
Impact: Users don't know what to do, poor experience
```

**Comparison**:
```python
❌ Current:
Error: Index not found at ~/.claw-mem/index/index_v0.7.0.pkl.gz

✅ Expected (Chinese):
[Error] Memory index not found, rebuilding... (about 1 second)
[Suggestion] If this persists, run: claw-mem repair
[Error Code] INDEX_NOT_FOUND
```

**v0.8.0 Solution**:
- ✅ Error messages in Chinese
- ✅ 80% errors with fix suggestions
- ✅ Error codes queryable in documentation

---

#### 3.3 Missing One-Click Migration Tools

**Problem**:
```
Current: Difficult to migrate from other systems, manual backup/restore
Impact: High switching cost, easy to make mistakes
```

**v0.8.0 Solution**:
- ✅ claw-mem backup command
- ✅ claw-mem restore command
- ⏳ Migration from MemGPT/Mem0 (deferred to v0.9.0)

---

### 4. Documentation and Community Issues

#### 4.1 Documentation Unfriendly to Non-Technical Users

**Problem**:
```
Current: Many technical terms, lack of scenario-based tutorials
Impact: Steep learning curve, hard for non-technical users
```

**Comparison**:
```
❌ Current documentation:
"InMemoryIndex uses N-gram hashing for O(1) retrieval"

✅ Ideal documentation:
"How to make AI remember your preferences? 3 steps, permanent effect"
```

**v0.8.0 Solution**:
- ✅ Beginner tutorial series (3 articles)
- ✅ Scenario-based use cases (10 examples)
- ✅ FAQ

---

#### 4.2 Community Building Just Starting

**Problem**:
```
Current: No user feedback channel, no case sharing
Impact: Hard for community to grow, issues not collected timely
```

**v0.8.0 Solution**:
- ✅ Enable GitHub Discussions
- ✅ Case sharing template
- ✅ Contribution guide documentation

---

## v0.8.0 Vision and Goals

### Vision Statement

> **Enable every Harness Engineer to have an AI team that "remembers", "easy to use", and "intelligent"**

### Core Value Proposition

| Value | Description | Implemented Features |
|-------|-------------|---------------------|
| **Learn Once, Permanent Effect** | Experience auto-persisted, no repeated corrections | Auto rule extraction |
| **Personal Experience, Team Sharing** | Memories exportable/importable, team sharing | Backup/restore commands |
| **Tacit Knowledge, Explicit Persistence** | Auto-extract rules from conversations | Rule extraction engine |
| **Zero Config, Out of Box** | Auto-detect, no manual config | Auto configuration detection |
| **Friendly Errors, Self-Service** | Chinese messages + fix suggestions | Error friendliness |

### Success Metrics

| Metric | v0.7.0 Baseline | v0.8.0 Target | Improvement |
|--------|----------------|---------------|-------------|
| **Installation Time** | 5 min (Git+config) | 1 min (PyPI) | 5x |
| **First Config** | Manual edit | Auto-detect | 10x |
| **Error Resolution Rate** | 30% (user self-fix) | 70% (fix per suggestion) | 2.3x |
| **Search Satisfaction** | 60% | 80% (importance ranking) | 1.3x |
| **Documentation Readability** | Tech users 8/10 | Non-tech users 7/10 | - |

---

## Functional Requirements

### P0 Priority (Must Release)

#### F001: PyPI Release

**User Story**:
```
As a new user
I want to install with pip install claw-mem
So that I don't need to understand Git and GitHub
```

**Description**:
- Create pyproject.toml and setup.cfg
- Release to PyPI (test on TestPyPI first)
- Support `pip install claw-mem`
- CLI command auto-registered

**Acceptance Criteria**:
- [ ] `pip install claw-mem` succeeds
- [ ] Version correct (0.8.0)
- [ ] Dependencies auto-installed
- [ ] `claw-mem --version` works
- [ ] TestPyPI verification passed
- [ ] Official PyPI verification passed

**Effort**: 1 day  
**Priority**: 🔴 P0

---

#### F002: Error Message Friendliness

**User Story**:
```
As a non-technical user
I want to see Chinese error messages with fix suggestions
So that I can solve problems myself without checking documentation
```

**Description**:
- All error messages in Chinese
- 80% errors with fix suggestions
- Error codes queryable
- FriendlyError base class

**Acceptance Criteria**:
- [ ] 100% error messages in Chinese
- [ ] 80% errors have fix suggestions
- [ ] Error code documentation complete
- [ ] User test pass rate >80%

**Error Code List**:
| Error Code | Scenario | Friendly Message |
|------------|----------|-----------------|
| INDEX_NOT_FOUND | Index not exists | Rebuilding, please wait |
| WORKSPACE_NOT_FOUND | Workspace not found | Please check OpenClaw config |
| MEMORY_CORRUPTED | Memory file corrupted | Try restore from backup |
| PERMISSION_DENIED | Permission denied | Please check file permissions |

**Effort**: 1 day  
**Priority**: 🔴 P0

---

#### F003: Auto Configuration Detection

**User Story**:
```
As a regular user
I want workspace path auto-detected
So that out-of-box experience, reduce config errors
```

**Description**:
- Auto-detect OpenClaw workspace
- Multi-path attempts (~/.openclaw/workspace, etc.)
- Friendly message on detection failure
- Support manual override

**Acceptance Criteria**:
- [ ] Auto-detect workspace by default
- [ ] Detection success rate >90%
- [ ] Friendly message on failure
- [ ] Support manual parameter override
- [ ] Config result viewable

**Effort**: 0.5 day  
**Priority**: 🔴 P0

---

#### F004: Memory Importance Scoring

**User Story**:
```
As a power user
I want important memories prioritized in search
So that critical info won't be buried
```

**Description**:
- Importance scoring algorithm (type + frequency + recency)
- Search results re-ranked by importance
- Context injection prioritizes high-importance memories
- Support viewing memory importance

**Scoring Formula**:
```
Importance Score = Base (1.0) + Type Weight + Frequency Weight + Recency Weight

Type Weight:
  - Semantic (core facts): +0.5
  - Procedural (skills): +0.3
  - Episodic (daily): +0.0

Frequency Weight:
  - Access count > 10: +0.3
  - Access count > 5: +0.2
  - Access count > 1: +0.1

Recency Weight:
  - Accessed within 7 days: +0.2
  - Accessed within 30 days: +0.1

Max: 2.0
```

**Acceptance Criteria**:
- [ ] Scoring formula correctly implemented
- [ ] Search results ranked by importance
- [ ] No significant performance impact (<10%)
- [ ] Support viewing memory importance score
- [ ] User test satisfaction >70%

**Effort**: 2 days  
**Priority**: 🟡 P0

---

### P1 Priority (Strongly Recommended)

#### F101: Auto Rule Extraction

**User Story**:
```
As a manager
I want system to auto-extract rules from my corrections
So that same errors don't repeat
```

**Description**:
- Identify correction patterns from conversations
- Extract Pre-flight Check rules
- Rule confidence evaluation
- Requires user approval before application

**Acceptance Criteria**:
- [ ] Can identify common correction patterns
- [ ] Extracted rules are executable
- [ ] Support rule review (not auto-apply)
- [ ] Rules exportable/importable
- [ ] Accuracy >70%

**Effort**: 2 days  
**Priority**: 🟡 P1

---

#### F102: Memory Decay Mechanism

**User Story**:
```
As a long-term user
I want unimportant memories to auto-degrade
So that memory stays lean, search more accurate
```

**Description**:
- Ebbinghaus forgetting curve implementation
- Different decay rates for different types
- Low-priority memories auto-archived
- Support configuring decay constants

**Decay Constants**:
| Memory Type | Half-life | Description |
|-------------|-----------|-------------|
| Episodic | 7 days | Fast decay, expires in 30 days |
| Semantic | 90 days | Slow decay, permanent |
| Procedural | 180 days | Very slow decay, permanent |

**Acceptance Criteria**:
- [ ] Forgetting curve formula correct
- [ ] Different decay rates for different types
- [ ] Support configuring decay constants
- [ ] Archived memories recoverable
- [ ] No significant performance impact

**Effort**: 1.5 days  
**Priority**: 🟡 P1

---

#### F103: CLI Visualization Tools

**User Story**:
```
As a developer
I want to view memory status via CLI
So that quick diagnosis, understand memory situation
```

**Description**:
- `claw-mem stats` command
- `claw-mem debug` command
- Terminal visualization output
- Search log viewing

**Acceptance Criteria**:
- [ ] stats command output beautiful
- [ ] debug command shows detailed info
- [ ] Support export to JSON
- [ ] User test satisfaction >70%

**Effort**: 1.5 days  
**Priority**: 🟡 P1

---

#### F104: Backup/Restore Commands

**User Story**:
```
As a cautious user
I want one-click backup and restore
So that no data loss on upgrade or migration
```

**Description**:
- `claw-mem backup` command
- `claw-mem restore` command
- Support incremental backup
- Support specifying backup location

**Acceptance Criteria**:
- [ ] backup command works
- [ ] restore command works
- [ ] Backup file integrity verification
- [ ] Support incremental backup

**Effort**: 0.5 day  
**Priority**: 🟡 P1

---

### P2 Priority (Optional)

#### F201: Debug Mode

**Description**: Search logs, detailed error messages  
**Effort**: 1 day  
**Priority**: 🟢 P2

#### F202: Statistics Dashboard

**Description**: Memory status statistics, charts  
**Effort**: 0.5 day  
**Priority**: 🟢 P2

#### F203: Documentation Optimization

**Description**: Beginner tutorial series, scenario-based use cases  
**Effort**: 1 day  
**Priority**: 🟢 P2

---

## Non-Functional Requirements

### Performance Requirements

| Metric | v0.7.0 Baseline | v0.8.0 Target | Description |
|--------|----------------|---------------|-------------|
| **Startup Time** | <50ms | <100ms | Slight increase allowed (new features) |
| **Search Latency** | <100ms | <150ms | Importance sorting overhead |
| **Memory Footprint** | <100MB | <150MB | Rule engine overhead |
| **Index Size** | 11KB | <20KB | Rule index addition |

### Usability Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Installation Success Rate** | >95% | PyPI installation test |
| **Configuration Success Rate** | >90% | Auto-detection success |
| **Error Resolution Rate** | >70% | Users fix per suggestions |
| **Documentation Readability** | >7/10 | Non-technical user rating |

### Compatibility Requirements

| Requirement | Description |
|-------------|-------------|
| **Backward Compatible** | Fully compatible with v0.7.0 memory file format |
| **Python Version** | 3.9+ |
| **Operating System** | macOS/Linux/Windows |
| **OpenClaw Version** | v0.5.0+ |

### Security Requirements

| Requirement | Description |
|-------------|-------------|
| **Local-First** | Default fully local, no cloud dependency |
| **Privacy Protection** | No user data upload |
| **Write Validation** | Reject malicious injection content |
| **Audit Logging** | All modifications traceable |

---

## User Stories

### User Personas

#### Persona 1: Technical Newbie (Xiao Li)

```
Background: College student, first time using AI assistant
Skills: Computer literate, no programming
Needs: Simple, easy to use, no errors
Pain points: Afraid of complex config, afraid of errors can't fix
```

**Key Scenarios**:
- Install claw-mem (needs to be simple)
- First configuration (needs to be auto)
- Encounter errors (needs friendly messages)

**v0.8.0 Improvements**:
- ✅ PyPI one-click install
- ✅ Auto configuration detection
- ✅ Chinese errors + suggestions

---

#### Persona 2: Business Professional (Manager Wang)

```
Background: Enterprise middle management, manages 10-person team
Skills: Business savvy, not technical
Needs: Improve efficiency, reduce repetitive work
Pain points: AI always makes same errors
```

**Key Scenarios**:
- Make AI remember team norms
- Correct AI's wrong behaviors
- Share experience with team members

**v0.8.0 Improvements**:
- ✅ Auto rule extraction
- ✅ Memory importance scoring
- ✅ Backup/restore for sharing

---

#### Persona 3: Developer (Engineer Zhang)

```
Background: Software engineer, 5 years experience
Skills: Programming, Git
Needs: Customizable, extensible, debuggable
Pain points: Hard to debug, missing tools
```

**Key Scenarios**:
- Debug search issues
- View memory status
- Customize rules

**v0.8.0 Improvements**:
- ✅ CLI debug command
- ✅ stats visualization
- ✅ Rules export/import

---

## Acceptance Criteria

### Overall Acceptance Criteria

| Category | Criteria | Measurement |
|----------|----------|-------------|
| **Feature Complete** | P0 features 100% complete | Functional tests |
| **Test Coverage** | Code coverage >95% | pytest-cov |
| **Performance Met** | All performance targets met | Performance tests |
| **Documentation Complete** | All docs updated | Documentation review |
| **User Testing** | Satisfaction >80% | User feedback |

### Feature Acceptance Checklist

#### P0 Features
- [ ] F001 PyPI Release - Installation verification passed
- [ ] F002 Error Friendliness - User tests passed
- [ ] F003 Auto Config - Detection success rate >90%
- [ ] F004 Importance Scoring - Search satisfaction >70%

#### P1 Features (if included)
- [ ] F101 Auto Rules - Accuracy >70%
- [ ] F102 Memory Decay - Formula verification passed
- [ ] F103 CLI Visualization - User satisfaction >70%
- [ ] F104 Backup/Restore - Integrity verification passed

---

## Release Plan

### Recommended: Option A (Lite Version)

**Duration**: 5 days (03-21 ~ 03-25)  
**Scope**: P0 features (F001-F004)  
**Release**: v0.8.0 official

```
┌─────────────────────────────────────────────────────────────┐
│                    v0.8.0 Iteration Timeline                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Day 1 (03-21 Sat): F001 PyPI Release                       │
│  ├─ Create pyproject.toml                                  │
│  ├─ Configure setup.cfg                                    │
│  ├─ TestPyPI testing                                       │
│  └─ Official PyPI release                                  │
│                                                             │
│  Day 2 (03-22 Sun): F002 + F003 UX Improvements             │
│  ├─ FriendlyError base class                               │
│  ├─ Error messages localization                            │
│  ├─ ConfigDetector auto-detection                          │
│  └─ User testing                                           │
│                                                             │
│  Day 3 (03-23 Mon): F004 Importance Scoring                 │
│  ├─ ImportanceScorer implementation                        │
│  ├─ Search results re-ranking                              │
│  ├─ Performance optimization                               │
│  └─ Unit tests                                             │
│                                                             │
│  Day 4 (03-24 Tue): Testing + Documentation                 │
│  ├─ Integration tests                                      │
│  ├─ Performance tests                                      │
│  ├─ Documentation updates                                  │
│  └─ Bug fixes                                              │
│                                                             │
│  Day 5 (03-25 Wed): Release Verification                    │
│  ├─ Peter review                                           │
│  ├─ Git Tag creation                                       │
│  ├─ GitHub Release                                         │
│  ├─ PyPI verification                                      │
│  └─ User notification                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Alternative: Option B (Full Version)

**Duration**: 10 days (03-21 ~ 03-30)  
**Scope**: P0 + P1 features  
**Release**: v0.8.0 official

### Alternative: Option C (Phased)

**Duration**: Two phases  
**Scope**: P0 → P1 in batches

```
v0.8.0 (03-25): P0 features - UX foundation
v0.8.1 (03-30): P1 features - Intelligence enhancement
```

---

## Risk Assessment

### Risk Matrix

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **PyPI release process complex** | Medium | Medium | Prepare early, test TestPyPI first | Friday |
| **Auto rule accuracy low** | High | Low | Default not auto-apply, requires review | Friday |
| **Importance scoring impacts performance** | Low | Medium | Cache scoring results | Friday |
| **Iteration延期** | Medium | Medium | Use Option A (lite version) | Peter |
| **User feedback collection difficult** | Medium | Low | GitHub Discussions + survey | Friday |

### Risk Response Strategies

#### High Risks

**None** ✅

#### Medium Risks

| Risk | Response Strategy |
|------|------------------|
| PyPI release process | Prepare 1 day early, TestPyPI verification first |
| Iteration delay | Use Option A, defer P1 to v0.8.1 |
| User feedback collection | Include survey link in release |

#### Low Risks

| Risk | Response Strategy |
|------|------------------|
| Auto rule accuracy | Clearly label "experimental", requires review |
| Importance scoring performance | Performance test verification, optimize if exceeded |

---

## Appendix

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Harness Engineering** | New AI human-machine collaboration paradigm, humans manage AI employees |
| **Pre-flight Check** | Mandatory rule check before operations |
| **Importance Scoring** | Memory priority based on type, frequency, recency |
| **Activation Decay** | Ebbinghaus forgetting curve implementation |

### Appendix B: References

1. claw-mem v0.7.0 Release Report
2. claw-mem Issues Analysis Report (2026-03-20)
3. Lingensi Technology Exchange Notes (2026-03-20)
4. Ebbinghaus Forgetting Curve Research
5. AI Harness Engineering Whitepaper

### Appendix C: Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-20 | Friday | Initial version |

---

## Approval

| Role | Name | Date | Status |
|------|------|------|--------|
| **Product Owner** | Peter Cheng | ⏳ | Pending |
| **Tech Lead** | Friday | ⏳ | Pending |
| **Project Manager** | - | ⏳ | Pending |

---

**Document Status**: Draft  
**Created**: 2026-03-20T14:57  
**Next Update**: After approval

---

*This document is the official requirements specification for claw-mem v0.8.0. All feature development must follow this document.*
