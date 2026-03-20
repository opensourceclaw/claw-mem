# F000: Memory System Bug Fix - Implementation Plan

**Status**: 🔴 CRITICAL  
**Created**: 2026-03-20  
**Priority**: Must fix before v0.8.0 release

---

## 🐛 Problem Analysis

### Observed Symptoms

| Symptom | Example |
|---------|---------|
| **Wrong data retrieval** | Retrieved `claw-mem.git` instead of `claw-mem/claw-mem.git` |
| **Repeated errors after correction** | User corrected 3+ times, still wrong |
| **Session start memory not loaded** | Memory existed but not used |

### Root Causes

#### 1. Memory Retrieval Inaccuracy

**Current Flow**:
```
User provides info → Stored in MEMORY.md
                    ↓
Next session → memory_search() → Should find it
                    ↓
                But returns wrong/outdated info
```

**Problem**:
- `memory_search` may be using semantic similarity instead of exact match
- Multiple similar entries cause confusion
- No priority for "most recent correction"

#### 2. Memory Update Mechanism Failure

**Current Flow**:
```
User corrects → Should update MEMORY.md immediately
              ↓
But: Old entry remains, new entry added
              ↓
Result: Multiple conflicting entries
```

**Problem**:
- No deduplication mechanism
- No "correction overrides previous" logic
- All entries treated equally

#### 3. Session Start Memory Injection

**Current Flow**:
```
Session starts → Should load MEMORY.md
              ↓
But: May not load or load wrong entries
              ↓
Result: Agent starts with wrong context
```

**Problem**:
- No validation that memory was loaded
- No consistency check between loaded memory and actual files
- Silent failure if memory load fails

---

## 🔧 Solution Design

### Fix 1: Improved Memory Retrieval

**Implementation**:
```python
class MemoryRetriever:
    def retrieve(self, query: str, exact_match: bool = False) -> List[Memory]:
        if exact_match:
            # Priority 1: Exact match
            results = self.exact_match_search(query)
        else:
            # Priority 2: Semantic search
            results = self.semantic_search(query)
        
        # Priority 3: Most recent correction wins
        results = self.sort_by_recency_and_confidence(results)
        
        return results[:1]  # Return only top match
```

**Key Changes**:
- ✅ Exact match priority for critical info (URLs, paths, names)
- ✅ Recency weighting (newer corrections override old)
- ✅ Confidence scoring (user corrections = high confidence)

---

### Fix 2: Memory Update with Deduplication

**Implementation**:
```python
class MemoryManager:
    def store(self, content: str, tags: List[str], allow_duplicate: bool = False):
        # Check for existing similar entries
        existing = self.search_similar(content, tags)
        
        if existing and not allow_duplicate:
            # Ask user: "Found similar entry, update or add new?"
            # Or auto-update if confidence > threshold
            self.update(existing[0].id, content)
        else:
            self.add_new(content, tags)
```

**Key Changes**:
- ✅ Duplicate detection before adding
- ✅ Update existing entries instead of adding duplicates
- ✅ User confirmation for ambiguous cases

---

### Fix 3: Session Start Memory Validation

**Implementation**:
```python
class SessionInitializer:
    def start_session(self):
        # Load memory
        memory = self.load_memory()
        
        # Validate
        if not self.validate_memory(memory):
            # Critical: Alert user
            self.notify("Memory validation failed, please check MEMORY.md")
        
        # Consistency check
        if not self.consistency_check(memory):
            # Warning: Inconsistencies found
            self.notify("Memory inconsistencies detected")
        
        # Inject into context
        self.inject_memory(memory)
```

**Key Changes**:
- ✅ Memory load validation
- ✅ Consistency check (no conflicting entries)
- ✅ User notification if validation fails

---

## 📋 Implementation Tasks

### Task 1: Memory Retrieval Fix

**Files to Modify**:
- `~/.openclaw/workspace/memory_search.py` (if exists)
- OpenClaw core memory retrieval logic

**Changes**:
- [ ] Add exact match priority
- [ ] Add recency weighting
- [ ] Add confidence scoring
- [ ] Limit results to top 1 for critical queries

**Estimated Time**: 4 hours

---

### Task 2: Memory Update with Deduplication

**Files to Modify**:
- `~/.openclaw/workspace/MEMORY.md` management logic
- Memory store/update functions

**Changes**:
- [ ] Add duplicate detection
- [ ] Add update vs add logic
- [ ] Add user confirmation for ambiguous cases
- [ ] Add "correction timestamp" to entries

**Estimated Time**: 4 hours

---

### Task 3: Session Start Validation

**Files to Modify**:
- Session initialization logic
- Memory injection mechanism

**Changes**:
- [ ] Add memory load validation
- [ ] Add consistency check
- [ ] Add user notification on failure
- [ ] Add memory load logging

**Estimated Time**: 4 hours

---

### Task 4: Testing & Verification

**Test Cases**:
- [ ] User provides URL, retrieved correctly in next session
- [ ] User corrects URL, old entry removed/updated
- [ ] Session starts with correct memory
- [ ] No duplicate entries after multiple corrections
- [ ] Memory validation alerts on failure

**Estimated Time**: 4 hours

---

## ✅ Acceptance Criteria

### Must Pass All Tests

| Test | Expected Result | Status |
|------|----------------|--------|
| **Correct URL retrieval** | `claw-mem/claw-mem.git` retrieved | ⏳ |
| **No repeated errors** | After correction, never wrong again | ⏳ |
| **Session memory load** | Correct memory at session start | ⏳ |
| **No duplicates** | Single entry per fact | ⏳ |
| **Validation alerts** | User notified if memory fails | ⏳ |

---

## 📊 Success Metrics

| Metric | Before | After Target |
|--------|--------|--------------|
| **Memory Accuracy** | <80% | >95% |
| **Duplicate Entries** | Common | 0 |
| **Correction Repetition** | 3+ times | 1 time |
| **Session Start Validation** | None | 100% |

---

## 🚦 Current Status

**Status**: ⏸️ **ON HOLD - Waiting for OpenClaw Refactor**

**Decision**: Wait for OpenClaw core team (远影) to fix memory system bugs.

**Rationale**:
- OpenClaw is undergoing major refactoring (announced on x.com)
- Next release will have significant changes
- Fixing memory system now may be obsolete after refactor

**Temporary Workaround**:
- Manual verification of critical information (URLs, paths, names)
- Double-check before important operations
- Report any memory-related issues to OpenClaw team

**Target**: Fix will be included in OpenClaw next major release (TBD)

```
Day 1 (4 hours):
├─ Task 1: Memory Retrieval Fix
└─ Task 2: Memory Update with Deduplication

Day 2 (4 hours):
├─ Task 3: Session Start Validation
└─ Task 4: Testing & Verification

Total: 2 days (16 hours)
```

---

## ⚠️ Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenClaw core changes needed | High | Work with OpenClaw team if needed |
| Breaking existing memory format | Medium | Backward compatible changes |
| Performance impact | Low | Cache optimized queries |

---

**Status**: Ready to implement  
**Next Step**: Start Task 1 - Memory Retrieval Fix
