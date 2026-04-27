# claw-mem Requirements Specification

**Version**: 1.0  
**Date**: 2026-03-18  
**Status**: Draft (Pending Review)  
**Repository**: https://github.com/opensourceclaw/claw-mem

---

## 1. Vision and Goals

### 1.1 Project Vision

> "Build an international-grade open source memory project for OpenClaw, enabling more people to enjoy the convenience brought by AI technology."

**Core Insight**:
- ❌ **NOT**: A patch to solve Friday's personal problems
- ✅ **BUT**: A general-purpose memory solution for the OpenClaw community

### 1.2 Target Users

| User Type | Scenario | Needs |
|-----------|----------|-------|
| **Developers** | Managing projects with OpenClaw | Remember project context, tech stack, decision history |
| **Researchers** | Organizing literature with OpenClaw | Remember paper insights, research ideas, citations |
| **Writers** | Organizing content with OpenClaw | Remember writing style, outlines, material library |
| **General Users** | Daily AI assistant usage | Remember preferences, habits, important dates |

### 1.3 Core Value Proposition

| Current OpenClaw | After claw-mem |
|------------------|----------------|
| Every session starts fresh | Cross-session persistent memory |
| Users repeat same corrections | AI learns from errors, doesn't repeat |
| Memory depends on manual organization | Auto-extract, auto-organize, auto-retrieve |
| Generic AI assistant | Personal AI partner that truly knows you |

---

## 2. User Requirements Analysis

### 2.1 Universal Needs from Peter-Friday Collaboration

| # | Scenario | Problem | Universality | Priority |
|---|----------|---------|--------------|----------|
| 1 | File created in wrong directory | Rules exist but not consulted | 🔴 All users encounter this | P0 |
| 2 | Key facts forgotten | Repo URLs, configs repeatedly wrong | 🔴 Common AI assistant issue | P0 |
| 3 | Incomplete procedural tasks | Tag created but no Release | 🟡 Procedural error | P1 |
| 4 | Boundary violations | Creating files without confirmation | 🔴 Boundary issue (configurable) | P1 |
| 5 | Preferences forgotten | Language, format, communication style | 🟢 Personalization | P2 |

### 2.2 Requirements Derived from Paper Research

| Paper | Inspiration | Translated Requirement |
|-------|-------------|----------------------|
| **GAM** | JIT compilation + dual architecture | Lightweight daily memory + deep research memory |
| **Context Engineering 2.0** | Entropy reduction + self-baking | Auto-summarization + hierarchical organization |
| **Engram** | N-gram hashing + sparse allocation | Fast retrieval + low memory footprint |
| **Mnemosyne** | 5-layer architecture + zero LLM pipeline | Layered memory + low-cost operation |
| **Reflexion** | Reflection + episodic memory | Learn from errors + reflection records |

### 2.3 OpenClaw Existing Memory Format Analysis

**Existing Format** (compatible retention):
```
~/.openclaw/workspace/
├── MEMORY.md              # Semantic Memory (Core Facts)
└── memory/
    ├── YYYY-MM-DD.md      # Episodic Memory (Daily Conversations)
    └── skills/            # Procedural Memory (Skills/Processes)
```

**Existing Problems**:
| Problem | Manifestation | Impact |
|---------|---------------|--------|
| Passive triggering | Depends on user correction | Errors repeat |
| No enforcement | Rules exist but not consulted | Rules become decorative |
| Knowledge isolation | Learning records disconnected from actions | Learn separately, do separately |
| No context injection | Sessions don't auto-load relevant memory | Always starting over |

---

## 3. Functional Requirements

### 3.1 Must Have (P0) - MVP Core Features

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|-------------------|
| **F001** | Pre-session Memory Injection | Auto-load relevant memory into context each session | Relevant memory visible after startup |
| **F002** | Pre-flight Checklist | Force-check relevant rules before specific operations | Check TOOLS.md before file operations |
| **F003** | Key Facts Persistence | Facts explicitly told by user are permanently saved | Persists after session restart |
| **F004** | Error Learning Records | Auto-extract learning entries from user corrections | Generate learning records after correction |
| **F005** | Memory Retrieval | Support keyword search for memory | Returns relevant memory fragments |
| **F006** | OpenClaw Format Compatibility | Fully compatible with existing MEMORY.md and memory/*.md | Existing files work seamlessly |

### 3.2 Should Have (P1) - Stable Version

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|-------------------|
| **F101** | Hybrid Retrieval | Keyword + Vector + N-gram hybrid retrieval | Retrieval accuracy >90% |
| **F102** | Memory Hierarchy | Auto-summarization + 4-layer structure | Support hierarchical browsing |
| **F103** | Activation Decay | Based on Ebbinghaus forgetting curve | Unused memory auto-degrades |
| **F104** | Memory Integrity Validation | Prevent malicious injection and corruption | Abnormal writes rejected |
| **F105** | Audit Logging | Record all memory modifications | Modification history traceable |
| **F106** | Checkpoint System | Regular memory snapshots with rollback | Support recovery to previous state |

### 3.3 Could Have (P2) - Advanced Features

| ID | Feature | Description | Acceptance Criteria |
|----|---------|-------------|-------------------|
| **F201** | Temporal Knowledge Graph | Time relationships between memories | Support timeline browsing |
| **F202** | 5-Signal Scoring Retrieval | Semantic + Recency + Importance + Frequency + Type | Smarter retrieval |
| **F203** | Flash Reasoning | BFS traversal of knowledge graph to reconstruct narrative | Support complex reasoning |
| **F204** | Multi-Agent Memory Sharing | Cross-Agent knowledge synchronization | Multiple Agents share memory |
| **F205** | Cloud Sync (Optional) | Encrypted cloud backup | User optionally enables |
| **F206** | Memory Visualization | Graphical display of memory relationships | Intuitive visualization interface |

### 3.4 Won't Have (Not Needed Now)

| ID | Feature | Reason |
|----|---------|--------|
| **F301** | Fully Automatic LLM Memory Organization | High cost, violates local-first principle |
| **F302** | Real-time Collaborative Editing | Too complex, not core requirement |
| **F303** | Mobile App | Focus on OpenClaw desktop |

---

## 4. Non-Functional Requirements

### 4.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Startup Time | <1s | Cold start to usable |
| Memory Retrieval Latency | <100ms | P95 latency |
| Memory Footprint | <100MB | 1000 memory entries |
| Write Latency | <50ms | Single memory write |

### 4.2 Security

| Requirement | Implementation |
|-------------|----------------|
| Local-First | Default fully local operation |
| Privacy Protection | No user data upload |
| Write Validation | Reject malicious injection content |
| Audit Logging | All modifications traceable |

### 4.3 Compatibility

| Requirement | Implementation |
|-------------|----------------|
| OpenClaw Format | Fully compatible with existing memory files |
| Cross-Platform | macOS/Linux/Windows |
| Python Version | 3.9+ |
| Backward Compatibility | Old version memory files usable |

### 4.4 Extensibility

| Requirement | Implementation |
|-------------|----------------|
| Plugin Architecture | Core + plugin mode |
| Custom Retrievers | Support replacing retrieval algorithms |
| Custom Storage Backends | Support SQLite/Vector DB/Others |

---

## 5. Technical Stack

### 5.1 Technology Decisions Based on Papers

| Component | Selection | Source | Rationale |
|-----------|-----------|--------|-----------|
| **Memory Storage** | SQLite + Markdown files | Mnemosyne | Zero LLM pipeline, low cost |
| **Retrieval Index** | N-gram hashing + BM25 | Engram | O(1) retrieval, mature and stable |
| **Memory Organization** | 4-layer summary structure | Context Engineering 2.0 | Entropy reduction, auto-organization |
| **Memory Decay** | Activation Decay | Mnemosyne | Ebbinghaus forgetting curve |
| **Architecture Pattern** | AOT+JIT hybrid | GAM | Lightweight + deep combination |

### 5.2 Technology Stack

```
Core Layer:
- Python 3.9+
- SQLite3 (built-in)
- Whoosh/BM25 (full-text search)

Optional Layer:
- Redis (L1 cache, optional)
- Chroma/FAISS (vector retrieval, optional)

Tool Layer:
- Click (CLI)
- Pydantic (data validation)
- pytest (testing)
```

---

## 6. Competitive Analysis

| Feature | claw-mem | MemGPT | Mem0 | LangChain Memory |
|---------|---------|--------|------|-----------------|
| **Architecture** | 5-layer cognitive | Dual-layer | Single-layer | Single-layer |
| **Retrieval** | Hybrid (N-gram+Vector+BM25) | Vector | Vector | Vector |
| **Organization** | Self-baking 4-layer + Graph | Flat | Flat | Flat |
| **Learning** | Manual + Auto-extract | Manual | Manual | Manual |
| **Cost** | $0 (L1/L2 zero LLM) | $0.01/memory | $0.01/memory | $0.01/memory |
| **Latency** | <50ms (L1/L2) | 500ms-2s | 500ms-2s | 500ms-2s |
| **OpenClaw Integration** | ✅ Native | ❌ | ❌ | ⚠️ Needs adaptation |
| **Local-First** | ✅ | ⚠️ | ❌ | ⚠️ |

---

## 7. Roadmap

### Phase 1: MVP (Week 1-2)

**Goal**: Core features functional

| Task | Estimated Time | Deliverable |
|------|---------------|-------------|
| Core Storage Layer | 2 days | SQLite + Markdown read/write |
| Basic Retrieval | 2 days | Keyword search |
| Pre-session Injection | 1 day | Auto-load memory |
| Pre-flight Checklist | 1 day | Force-check before operations |
| Testing + Documentation | 2 days | Unit tests + README |

**Milestone**: v0.5.0 release (✅ Completed)

### Phase 2: Stable (Week 3-4)

**Goal**: Performance optimization + hybrid retrieval

| Task | Estimated Time | Deliverable |
|------|---------------|-------------|
| N-gram Index | 2 days | Fast retrieval |
| Hybrid Retrieval | 2 days | Keyword + BM25 + Vector |
| Memory Hierarchy | 2 days | 4-layer summary |
| Activation Decay | 1 day | Forgetting curve |
| Testing + Documentation | 3 days | Complete tests + API docs |

**Milestone**: v1.0.0 release

### Phase 3: Advanced (Week 5-8)

**Goal**: Advanced features + community release

| Task | Estimated Time | Deliverable |
|------|---------------|-------------|
| Temporal Knowledge Graph | 1 week | Relationship indexing |
| 5-Signal Scoring | 3 days | Intelligent retrieval |
| Community Release Prep | 1 week | Docs + examples + promotion |

**Milestone**: v2.0.0 release + community outreach

---

## 8. Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Insufficient community feedback | Product deviates from needs | Medium | Proactively collect Discord/GitHub feedback |
| Performance below target | Poor user experience | Low | Early performance testing + optimization |
| Compatibility issues | Existing users cannot migrate | Low | Thorough testing + migration tools |
| Complex implementation | Development difficulty | Medium | Phased implementation, MVP first |

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| GitHub Stars | 500+ (within 6 months) | GitHub Insights |
| Installations | 1000+ (within 6 months) | PyPI downloads + skill installs |
| Community Contributions | 10+ PRs (within 6 months) | GitHub PRs |
| User Satisfaction | 4.5/5+ | Community survey |
| Memory Accuracy | 90%+ | Retrieval tests |

---

## 10. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **Episodic Memory** | Daily conversation records (memory/YYYY-MM-DD.md) |
| **Semantic Memory** | Core facts (MEMORY.md) |
| **Procedural Memory** | Skills and processes (memory/skills/*.md) |
| **Pre-flight Check** | Mandatory rule check before specific operations |
| **Activation Decay** | Memory importance decreases over time without use |

### B. References

1. GAM (General Agentic Memory) - Multi-institution, 2025
2. Context Engineering 2.0 - GAIR Lab (SJTU), 2025
3. Engram: Conditional Memory - DeepSeek-AI, 2025
4. Mnemosyne/SuperLocalMemory V3 - Qualixar, 2025
5. Reflexion: Language Agents with Verbal Reinforcement Learning - Princeton, NeurIPS 2023

---

**Document History**:

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-18 | Friday | Initial draft |

---

**Status**: Draft (Pending Peter's Review and Approval)
