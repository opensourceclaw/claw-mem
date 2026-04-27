# claw-mem v1.0.0 Requirements

**Created**: 2026-03-23
**Version**: v1.0.0
**Status**: Requirements Collection Phase
**Theme**: Three-Tier Memory Retrieval

---

## Core Problem

### Current State: Three-Tier Storage Implemented, Three-Tier Retrieval Missing

| Layer | Storage | Retrieval | Status |
|-------|---------|-----------|--------|
| L1 Working Memory | Current session context | New sessions cannot inherit | Incomplete |
| L2 Short-term Memory | daily memory files | Only loads today/yesterday, no proactive retrieval | Incomplete |
| L3 Long-term Memory | MEMORY.md | Only loads, no semantic retrieval | Incomplete |

### Problem Manifestations

1. **New Session "Amnesia"** — Each new session cannot find previously discussed content
2. **Passive Loading** — Only reads fixed files (today's memory + MEMORY.md), no proactive search
3. **Topic Fragmentation** — Specific topics (e.g., Harness Engineering, Project Neo architecture) cannot be retrieved if not in recent files

### Root Cause

Current session startup flow:
```
1. Read SOUL.md
2. Read USER.md
3. Read memory/YYYY-MM-DD.md (today + yesterday)
4. Read MEMORY.md (main session)
```

This is **passive loading**, not **proactive retrieval**.

---

## v1.0.0 Requirements List

### REQ-001: Session Startup Proactive Retrieval Mechanism

**Description**: When a new session starts, perform cross-layer semantic retrieval based on topic/context

**Functional Requirements**:
- [ ] Identify current session topic/intent
- [ ] Perform semantic search in L2/L3 memory based on topic
- [ ] Inject retrieval results into session context
- [ ] Support manual retrieval trigger (e.g., `/search` command)

**Priority**: P0

---

### REQ-002: Three-Tier Search API

**Description**: Implement unified retrieval API supporting cross-layer search

**API Design**:
```python
def search_memory(query: str,
                  layers: List[str] = ["l1", "l2", "l3"],
                  limit: int = 10) -> List[MemoryResult]:
    """
    Cross-layer memory retrieval

    Args:
        query: Search query
        layers: Retrieval layers ["l1", "l2", "l3"]
        limit: Number of results to return

    Returns:
        List of memory results with source layer, confidence, content
    """
```

**Priority**: P0

---

### REQ-003: Topic Tag System Enhancement

**Description**: Improve memory tag/index system to support topic classification

**Functional Requirements**:
- [ ] Automatically extract topic tags from memory entries
- [ ] Support topic hierarchy (e.g., `Project Neo > Architecture > Multi-Agent`)
- [ ] Fast filtering based on topics
- [ ] Topic cloud/topic map visualization

**Priority**: P1

---

### REQ-004: Memory Retrieval Logging

**Description**: Log retrieval history for optimization and debugging

**Functional Requirements**:
- [ ] Log query, results, and source for each retrieval
- [ ] Support retrieval history replay
- [ ] Analyze retrieval success rate
- [ ] Identify high-frequency "not found" topics and prompt user to add memories

**Priority**: P2

---

### REQ-005: Session Context Inheritance

**Description**: New sessions can inherit context from previous sessions

**Functional Requirements**:
- [ ] Save key context at session end
- [ ] Load recent session summary at new session startup
- [ ] Support explicit session linking (`continue session:xxx`)

**Priority**: P1

---

## Technical Architecture

### Retrieval Flow

```
New Session Startup
    │
    ▼
Intent Classification
    │
    ├─── Keyword Extraction
    ├─── Semantic Vectorization
    └─── Topic Tag Matching
    │
    ▼
Cross-Layer Retrieval (Three-Tier Search)
    │
    ├─── L1: Recent Session Transcripts (if available)
    ├─── L2: memory/*.md Semantic Search
    └─── L3: MEMORY.md Semantic Search
    │
    ▼
Result Aggregation & Ranking
    │
    ├─── Deduplication
    ├─── Confidence Ranking
    └─── Relevance Filtering
    │
    ▼
Context Injection
    │
    └─── Inject retrieval results into system prompt
```

### Performance Requirements

- Retrieval latency: < 2 seconds (cold start < 5 seconds)
- Retrieval accuracy: > 85% (relevant results in top 5)
- Support concurrent retrieval

---

## Acceptance Criteria

### Functional Acceptance

1. **Session Continuity Test**
   - Session A discusses topic X
   - Start new session B
   - Session B can automatically retrieve content about topic X

2. **Cross-Layer Retrieval Test**
   - Query memory in L2 → Can retrieve
   - Query memory in L3 → Can retrieve
   - Query memory across multiple layers → Results aggregated correctly

3. **Topic Recognition Test**
   - Mention "Harness Engineering" → Retrieve related discussions
   - Mention "Project Neo" → Retrieve architecture definitions
   - Mention "Multi-Agent" → Retrieve Pillar Agent information

### Performance Acceptance

- Retrieval response time < 2 seconds
- Memory usage < 100MB (index)
- Support 1000+ memory entries

---

## Release Plan

| Phase | Content | Estimated Time |
|-------|---------|---------------|
| Phase 1 | REQ-001 + REQ-002 (Core Retrieval) | TBD |
| Phase 2 | REQ-003 + REQ-005 (Tags + Inheritance) | TBD |
| Phase 3 | REQ-004 (Logging + Analytics) | TBD |
| Phase 4 | Testing + Documentation | TBD |

**Target Release Date**: TBD (awaiting Peter priority confirmation)

---

## Related Documentation

- [claw-mem Release Process](./claw-mem-release-process.md)
- [v0.6.0 Release Notes](./claw-mem-v0.6.0-release.md)
- [v0.5.0 Release Process](./claw-mem-v0.5.0-release-process.md)

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-23 | Initial requirements document created | Friday |

---

**Author**: Friday
**Approver**: Peter (pending)
**Last Updated**: 2026-03-23
