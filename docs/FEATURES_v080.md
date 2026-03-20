# claw-mem v0.8.0 Feature Requirements

**Version**: v0.8.0  
**Theme**: User Experience & Intelligence  
**Status**: 📋 Draft  
**Created**: 2026-03-20  
**Based on**: v0.7.0 Post-Release Review

---

## 📋 Background

### v0.7.0 Achievements

| Metric | Result |
|--------|--------|
| **Startup Time** | 1.5s → 7.47ms (191x improvement) |
| **Index Compression** | 82.5% size reduction |
| **Lazy Loading** | 0.133ms initialization |
| **Exception Recovery** | Auto backup + corruption recovery |
| **Test Coverage** | 100% |

**Status**: Performance optimization completed ✅

### v0.8.0 Focus

Based on v0.7.0 release review, shift focus from:
- ❌ **Performance optimization** (completed in v0.7.0)
- ✅ **User experience & intelligence** (v0.8.0 focus)

### Installation Method

**Same as OpenClaw** (consistent with community):

```bash
# Clone repository
git clone https://github.com/opensourceclaw/claw-mem/claw-mem.git
cd claw-mem

# Install in editable mode
pip install -e .
```

**Rationale**:
- ✅ Consistent with OpenClaw installation
- ✅ Reduce user cognitive load
- ✅ Sync with community practices
- ✅ Easy to modify and test
- ✅ Works offline

---

## 🎯 Feature Requirements

### P0 Priority (Must Release)

#### F000: Memory System Bug Fix (CRITICAL)

**Status**: ⏸️ **ON HOLD - Waiting for OpenClaw Refactor**

**Decision**: Defer to OpenClaw core team. Will be fixed in OpenClaw next major release.

**Temporary Workaround**:
- Manual verification of critical information
- Double-check URLs, paths, names before important operations
- Report memory issues to OpenClaw team

**Original Requirements** (for reference):
- Fix memory retrieval accuracy
- Implement memory deduplication
- Add session start memory validation

**Effort**: Deferred  
**Priority**: 🔴 CRITICAL (blocked by OpenClaw refactor)

---

#### F001: Error Message Friendliness

**Problem**:
```python
❌ Current:
Error: Index not found at ~/.claw-mem/index/index_v0.7.0.pkl.gz

✅ Expected:
[Error] Memory index not found, rebuilding... (about 1 second)
[Suggestion] If this persists, run: claw-mem repair
[Error Code] INDEX_NOT_FOUND
```

**Requirements**:
- All error messages in Chinese (for Chinese users)
- 80% errors with fix suggestions
- Error codes queryable in documentation
- `FriendlyError` base class

**Error Code List**:
| Error Code | Scenario | Friendly Message |
|------------|----------|-----------------|
| INDEX_NOT_FOUND | Index not exists | Rebuilding, please wait |
| WORKSPACE_NOT_FOUND | Workspace not found | Please check OpenClaw config |
| MEMORY_CORRUPTED | Memory file corrupted | Try restore from backup |
| PERMISSION_DENIED | Permission denied | Please check file permissions |

**Acceptance Criteria**:
- [ ] 100% error messages in Chinese
- [ ] 80% errors have fix suggestions
- [ ] Error code documentation complete
- [ ] User test pass rate >80%

**Effort**: 1 day  
**Priority**: 🔴 P0

---

#### F002: Auto Configuration Detection

**Problem**:
```python
# Current: User must manually configure
memory = MemoryManager(
    workspace="/Users/liantian/.openclaw/workspace"  # Manual
)

# Expected: Auto-detect
memory = MemoryManager()  # Auto-detect
```

**Requirements**:
- Auto-detect OpenClaw workspace
- Multi-path attempts (`~/.openclaw/workspace`, etc.)
- Friendly message on detection failure
- Support manual override

**Default Paths**:
```python
DEFAULT_PATHS = [
    "~/.openclaw/workspace",
    "~/.config/openclaw/workspace",
    os.getcwd(),  # Current directory
]
```

**Acceptance Criteria**:
- [ ] Auto-detect workspace by default
- [ ] Detection success rate >90%
- [ ] Friendly message on failure
- [ ] Support manual parameter override
- [ ] Config result viewable

**Effort**: 0.5 day  
**Priority**: 🔴 P0

---

#### F003: Memory Importance Scoring

**Problem**:
```
Current: All memories treated equally
Impact: Critical information may be buried

Example:
User said 10 times: "I like Sichuan food"
User said 1 time: "I'm allergic to peanuts"
❌ Both have same weight
✅ "Allergy" should have higher priority
```

**Requirements**:
- Importance scoring algorithm (type + frequency + recency)
- Search results re-ranked by importance
- Context injection prioritizes high-importance memories
- Support viewing memory importance

**Scoring Formula**:
```
Importance Score = Base (1.0) + Type Weight + Frequency Weight + Recency Weight

Base Score: 1.0
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

Maximum: 2.0
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

**Requirements**: Identify correction patterns, extract Pre-flight rules  
**Effort**: 2 days  
**Priority**: 🟡 P1

---

#### F102: Memory Decay Mechanism

**Requirements**: Ebbinghaus forgetting curve, auto-archive  
**Effort**: 1.5 days  
**Priority**: 🟡 P1

---

#### F103: CLI Visualization Tools

**Requirements**: `claw-mem stats`, `claw-mem debug` commands  
**Effort**: 1.5 days  
**Priority**: 🟡 P1

---

#### F104: Backup/Restore Commands

**Requirements**: `claw-mem backup`, `claw-mem restore`  
**Effort**: 0.5 day  
**Priority**: 🟡 P1

---

### P2 Priority (Optional)

#### F201: Debug Mode
**Effort**: 1 day  
**Priority**: 🟢 P2

---

#### F202: Statistics Dashboard
**Effort**: 0.5 day  
**Priority**: 🟢 P2

---

#### F203: Documentation Optimization
**Effort**: 1 day  
**Priority**: 🟢 P2

---

## 📅 Release Plan

### Recommended: Option A (Without F000)

**Duration**: 3.5 days  
**Scope**: F001-F003 (F000 deferred to OpenClaw core)  
**Release**: v0.8.0

```
Day 1: F001 Error Message Friendliness
Day 2: F002 Auto Configuration
Day 3-4: F003 Importance Scoring
Day 4: Testing + Documentation
```

**Note**: F000 (Memory Bug Fix) is deferred to OpenClaw core team. Will be included when OpenClaw refactor is complete.

---

## 📊 Success Metrics

| Metric | v0.7.0 Baseline | v0.8.0 Target | Improvement |
|--------|----------------|---------------|-------------|
| **Memory Accuracy** | <80% | Manual verification (temporary) | - |
| **Error Resolution Rate** | 30% | 70% | 2.3x |
| **Configuration Success** | Manual | Auto (>90%) | 10x |
| **Search Satisfaction** | 60% | 80% | 1.3x |

---

## ⚠️ Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Auto rule accuracy low | High | Low | Default not auto-apply |
| Importance scoring performance | Low | Medium | Cache results |
| Iteration delay | Medium | Medium | Use Option A |

**Overall Risk**: Low-Medium ✅

---

## 📝 Document Language Rule

**All project documentation**: 100% English  
**Discussion with Peter Cheng**: Chinese

---

## Appendix

### A. Feature Summary

| Priority | Count | Features | Total Effort |
|----------|-------|----------|--------------|
| **P0 (Deferred)** | 1 | F000 (Waiting for OpenClaw) | Deferred |
| **P0** | 3 | F001, F002, F003 | 3.5 days |
| **P1** | 4 | F101-F104 | 5.5 days |
| **P2** | 3 | F201-F203 | 2.5 days |

**Total v0.8.0**: 3.5 days (F000 deferred)

---

**Document Status**: Draft  
**Created**: 2026-03-20  
**Installation**: `pip install -e .` (local only)

---

*PyPI release deferred to v1.0.0. Focus on user experience and intelligence.*
