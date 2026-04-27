# claw-mem v1.0.0 Documentation

**Version**: 1.0.0  
**Release Date**: 2026-03-23  
**Status**: 📋 Requirements Phase  
**Theme**: Three-Tier Memory Retrieval  

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Core Problem](#core-problem)
3. [Requirements](#requirements)
4. [Technical Architecture](#technical-architecture)
5. [API Reference](#api-reference)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Release Plan](#release-plan)

---

## 🎯 Overview

claw-mem v1.0.0 introduces **Three-Tier Memory Retrieval** - a paradigm shift from passive loading to active retrieval.

### The Vision

Current memory system has three-tier **storage** but lacks three-tier **retrieval**:

| Tier | Storage | Retrieval | Status |
|------|---------|-----------|--------|
| L1 Working Memory | ✅ Current session context | ❌ Cannot inherit across sessions | Incomplete |
| L2 Short-term Memory | ✅ Daily memory files | ⚠️ Only loads today/yesterday, no active search | Incomplete |
| L3 Long-term Memory | ✅ MEMORY.md | ⚠️ Only loads, no semantic search | Incomplete |

### v1.0.0 Solution

Transform from **passive loading** to **active retrieval**:

```
OLD: Load fixed files → Hope relevant content is there
NEW: Identify topic → Search across all tiers → Inject relevant context
```

---

## 🔍 Core Problem

### Problem Manifestation

1. **Session Amnesia** - New sessions cannot find previous discussions
2. **Passive Loading** - Only reads fixed files (today's memory + MEMORY.md), no active search
3. **Topic Fragmentation** - Specific topics (Harness Engineering, Project Neo Architecture) lost if not in recent files

### Root Cause

Current session startup flow:
```
1. Read SOUL.md
2. Read USER.md
3. Read memory/YYYY-MM-DD.md (today + yesterday)
4. Read MEMORY.md (main session only)
```

This is **passive loading**, not **active retrieval**.

---

## 📋 Requirements

### REQ-001: Session Startup Active Retrieval

**Priority**: 🔴 P0

**Description**: On new session startup, perform cross-tier semantic search based on topic/context.

**Functional Requirements**:
- [ ] Identify current session topic/intent
- [ ] Perform semantic search in L2/L3 memory based on topic
- [ ] Inject retrieval results into session context
- [ ] Support manual search trigger (e.g., `/search` command)

**Acceptance Criteria**:
- Session A discusses topic X
- New session B starts
- Session B automatically retrieves topic X content

---

### REQ-002: Three-Tier Search API

**Priority**: 🔴 P0

**Description**: Implement unified search interface supporting cross-tier search.

**API Design**:
```python
def search_memory(query: str, 
                  layers: List[str] = ["l1", "l2", "l3"],
                  limit: int = 10) -> List[MemoryResult]:
    """
    Cross-tier memory search
    
    Args:
        query: Search query
        layers: Search layers ["l1", "l2", "l3"]
        limit: Number of results to return
    
    Returns:
        List of memory results with source layer, confidence, content
    """
```

**Return Structure**:
```python
@dataclass
class MemoryResult:
    content: str
    layer: str  # "l1", "l2", "l3"
    confidence: float  # 0.0 - 1.0
    source_file: str
    timestamp: datetime
    tags: List[str]
```

---

### REQ-003: Topic Tag System Enhancement

**Priority**: 🟡 P1

**Description**: Improve memory tag/index system for topic categorization.

**Functional Requirements**:
- [ ] Auto-extract topic tags from memory entries
- [ ] Support topic hierarchy (e.g., `Project Neo > Architecture > Multi-Agent`)
- [ ] Fast filtering by topic
- [ ] Topic cloud/topic map visualization

**Example Tags**:
```
- Project Neo
- Project Neo > Architecture
- Project Neo > Multi-Agent
- Harness Engineering
- OpenClaw > Skills
- OpenClaw > Memory
```

---

### REQ-004: Memory Search Logging

**Priority**: 🟢 P2

**Description**: Log search history for optimization and debugging.

**Functional Requirements**:
- [ ] Log each search: query, results, sources
- [ ] Support search history replay
- [ ] Analyze search success rate
- [ ] Identify high-frequency "not found" topics, prompt user to add memory

**Log Structure**:
```json
{
  "timestamp": "2026-03-23T14:30:00Z",
  "query": "Project Neo architecture",
  "results_count": 5,
  "layers_searched": ["l2", "l3"],
  "success": true,
  "top_result_confidence": 0.92
}
```

---

### REQ-005: Session Context Inheritance

**Priority**: 🟡 P1

**Description**: New sessions can inherit previous session context.

**Functional Requirements**:
- [ ] Save key context at session end
- [ ] Load recent session summary on new session startup
- [ ] Support explicit session linking (`continue session:xxx`)

**Session Summary Format**:
```markdown
## Session: session_20260323_143000

**Topics Discussed**:
- Project Neo Architecture
- Multi-Agent System Design

**Key Decisions**:
- Adopted 3-pillar structure (Stark, Pepper, Happy)
- Friday as main agent coordinator

**Pending Actions**:
- Review Business Agent documentation
```

---

## 🏗️ Technical Architecture

### Retrieval Flow

```
New Session Startup
        │
        ▼
Topic Identification (Intent Classification)
        │
        ├─── Keyword Extraction
        ├─── Semantic Vectorization
        └─── Topic Tag Matching
        │
        ▼
Cross-Tier Search (Three-Tier Search)
        │
        ├─── L1: Recent Session Transcripts (if available)
        ├─── L2: memory/*.md Semantic Search
        └─── L3: MEMORY.md Semantic Search
        │
        ▼
Result Aggregation & Ranking
        │
        ├─── Deduplication
        ├─── Confidence Sorting
        └─── Relevance Filtering
        │
        ▼
Context Injection
        │
        └─── Inject search results into system prompt
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│              claw-mem v1.0.0 Architecture                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Topic     │    │   Three-    │    │   Result    │ │
│  │ Identifier  │───▶│   Tier      │───▶│   Aggregator│ │
│  │             │    │   Searcher  │    │             │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│         │                   │                   │       │
│         │                   │                   │       │
│         ▼                   ▼                   ▼       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Keyword   │    │   L1/L2/L3  │    │  Confidence │ │
│  │   Extractor │    │   Adapters  │    │   Scorer    │ │
│  └─────────────┘    └─────────────┘    └─────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │          Context Injector                        │   │
│  │  (Injects results into session prompt)           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Search Latency | < 2 seconds | Cold start < 5 seconds |
| Search Accuracy | > 85% | Relevant results in top 5 |
| Memory Overhead | < 100MB | Index memory usage |
| Concurrent Searches | 10+ | Parallel search support |

---

## 🔧 API Reference

### Search API

```python
from claw_mem import MemoryManager

# Initialize
memory = MemoryManager(workspace="/Users/you/.openclaw/workspace")

# Basic search
results = memory.search("Project Neo architecture", limit=10)

# Multi-tier search
results = memory.search(
    "Multi-Agent system",
    layers=["l2", "l3"],  # Search short-term and long-term
    limit=5
)

# Search with tags
results = memory.search(
    "architecture",
    tags=["Project Neo"],
    limit=10
)
```

### Result Structure

```python
for result in results:
    print(f"Content: {result.content}")
    print(f"Layer: {result.layer}")           # l1, l2, or l3
    print(f"Confidence: {result.confidence}") # 0.0 - 1.0
    print(f"Source: {result.source_file}")
    print(f"Timestamp: {result.timestamp}")
    print(f"Tags: {result.tags}")
```

### Manual Search Command

```python
# Trigger manual search
memory.trigger_search(query="harness engineering")
```

---

## ✅ Acceptance Criteria

### Functional Acceptance

#### 1. Session Continuity Test
- ✅ Session A discusses topic X
- ✅ New session B starts
- ✅ Session B automatically retrieves topic X content
- ✅ Retrieved content is relevant and accurate

#### 2. Cross-Tier Search Test
- ✅ Query in L2 memory → Retrieved successfully
- ✅ Query in L3 memory → Retrieved successfully
- ✅ Query across multiple tiers → Results aggregated correctly
- ✅ No duplicate results

#### 3. Topic Identification Test
- ✅ Mention "Harness Engineering" → Retrieves related discussions
- ✅ Mention "Project Neo" → Retrieves architecture definitions
- ✅ Mention "Multi-Agent" → Retrieves Pillar Agent information

### Performance Acceptance

| Metric | Target | Test Method |
|--------|--------|-------------|
| Search Response Time | < 2 seconds | Measure 100 searches |
| Memory Overhead | < 100MB | Monitor RSS during search |
| Support 1000+ Entries | ✅ Pass | Test with 1000+ memory entries |
| Accuracy (Top 5) | > 85% | Manual relevance rating |

---

## 📅 Release Plan

### Phase 1: Core Search (P0)

**Content**: REQ-001 + REQ-002

**Deliverables**:
- Topic identification module
- Three-tier search API
- Context injection mechanism

**Estimated Time**: TBD

---

### Phase 2: Tags & Inheritance (P1)

**Content**: REQ-003 + REQ-005

**Deliverables**:
- Topic tag system
- Auto-tag extraction
- Session context inheritance

**Estimated Time**: TBD

---

### Phase 3: Logging & Analytics (P2)

**Content**: REQ-004

**Deliverables**:
- Search logging
- Analytics dashboard
- "Not found" topic detection

**Estimated Time**: TBD

---

### Phase 4: Testing & Documentation

**Content**: Comprehensive testing + User documentation

**Deliverables**:
- Test suite for all features
- User guide
- API documentation
- Migration guide

**Estimated Time**: TBD

---

## 🎯 Target Release Date

**TBD** - Awaiting Peter confirmation on priorities

---

## 🔗 Related Documents

- [claw-mem Release Process](./claw-mem-release-process.md)
- [v0.9.0 Release Notes](./RELEASE_NOTES_v090_DRAFT.md)
- [v0.8.0 Features](./FEATURES_v080.md)
- [Apache 2.0 License](../LICENSE)

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-03-23 | Initial requirements document created | Friday |

---

**Author**: Friday (Business Agent)  
**Reviewer**: Peter (Pending Confirmation)  
**Last Updated**: 2026-03-23  

---

*claw-mem - Make OpenClaw Truly Remember*  
*Project Neo - Est. 2026*  
*"Ad Astra Per Aspera"*
