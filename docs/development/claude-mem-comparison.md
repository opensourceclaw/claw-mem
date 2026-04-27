# claw-mem v2.0.0 vs claude-mem Comparison Analysis

> Analysis Date: 2026-04-17
> Objective: Select the best memory system for OpenClaw projects

---

## 📊 Executive Summary

| Dimension | claw-mem v2.0.0 | claude-mem v12.1.6 |
|-----------|----------------|-------------------|
| **Positioning** | OpenClaw-specific memory plugin | Claude Code universal memory system |
| **Language** | Python + TypeScript | TypeScript (Bun) |
| **License** | Apache 2.0 | AGPL-3.0 |
| **Maturity** | v2.0 (Production) | v12.1 (Mature ecosystem) |
| **Latency** | ~6ms average | ~50-100ms (HTTP API) |
| **Architecture** | Three-tier memory + stdio RPC | Hook + Worker + SQLite |
| **Search** | BM25 + Heuristic + Entity | FTS5 + Chroma Vector |

**Core Conclusions:**
- **claw-mem** is better for OpenClaw internal integration (zero network overhead, Python-native)
- **claude-mem** is better for Claude Code ecosystem (mature toolchain, Web UI)

---

## 1. Architecture Comparison

### 1.1 claw-mem Architecture

```
┌─────────────────────────────────────┐
│   OpenClaw Plugin (TypeScript)      │
│   @opensourceclaw/openclaw-claw-mem │
└──────────────┬──────────────────────┘
               │ spawn + stdio JSON-RPC
               │ (~1-5ms latency)
               ▼
┌─────────────────────────────────────┐
│   claw-mem Python Bridge            │
│   - stdio JSON-RPC Server           │
│   - Command Routing                 │
└──────────────┬──────────────────────┘
               │ Python Function Call
               ▼
┌─────────────────────────────────────┐
│   claw-mem Core (Python)            │
│   - MemoryManager                   │
│   - Three-Tier Retrieval            │
│   - SQLite Storage                  │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ **Local-First**: stdio JSON-RPC, zero network overhead
- ✅ **Python Native**: Seamless integration with neoclaw/claw-rl
- ✅ **Three-Tier Memory**: Episodic + Semantic + Procedural layers
- ✅ **Multiple Retrievers**: Keyword → BM25 → Hybrid → Entity → Heuristic → Smart

### 1.2 claude-mem Architecture

```
┌─────────────────────────────────────┐
│   Claude Code Plugin Hooks          │
│   - SessionStart / SessionEnd       │
│   - UserPromptSubmit / PostToolUse  │
└──────────────┬──────────────────────┘
               │ HTTP API (port 37777)
               │ (~50-100ms latency)
               ▼
┌─────────────────────────────────────┐
│   Worker Service (Bun)              │
│   - Express HTTP Server             │
│   - MCP Tools Integration           │
│   - Web Viewer UI                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Storage Layer                     │
│   - SQLite (sessions, observations) │
│   - Chroma (vector embeddings)      │
│   - FTS5 (full-text search)         │
└─────────────────────────────────────┘
```

**Key Features:**
- ✅ **Standalone Worker**: HTTP service, multi-client sharing
- ✅ **Web UI**: localhost:37777 real-time memory stream viewer
- ✅ **MCP Tools**: Standard Model Context Protocol tools
- ✅ **Multi-Platform**: Claude Code / Gemini CLI / OpenCode / OpenClaw

---

## 2. Feature Comparison

### 2.1 Memory Model

| Feature | claw-mem | claude-mem |
|---------|----------|------------|
| **Memory Types** | Three tiers (Episodic/Semantic/Procedural) | Two tiers (observations + summaries) |
| **Memory Compression** | ❌ None | ✅ AI auto-summarization |
| **Importance Scoring** | ✅ ImportanceScorer | ✅ Implicit (summarization) |
| **Memory Decay** | ✅ MemoryDecay | ❌ None |
| **Privacy Control** | ❌ None | ✅ `<private>` tag exclusion |

**claw-mem Three-Tier Model:**
```python
# Episodic: Event sequence memory
episodic = EpisodicStorage(workspace)

# Semantic: Knowledge graph storage
semantic = SemanticStorage(workspace)

# Procedural: Rules and procedures
procedural = ProceduralStorage(workspace)
```

**claude-mem Two-Tier Model:**
```typescript
// Observation: Raw tool usage observations
observations: Array<{
  id: number;
  session_id: string;
  tool_name: string;
  content: string;
  timestamp: number;
}>

// Summary: AI-compressed semantic summaries
summaries: Array<{
  id: number;
  content: string;
  created_at: number;
}>
```

### 2.2 Retrieval Capabilities

| Feature | claw-mem | claude-mem |
|---------|----------|------------|
| **Keyword Search** | ✅ KeywordRetriever | ✅ FTS5 |
| **BM25** | ✅ HybridBM25Retriever | ❌ None |
| **Vector Search** | ❌ None | ✅ Chroma + Embeddings |
| **Entity Enhancement** | ✅ EntityEnhancedRetriever | ❌ None |
| **Heuristic Retrieval** | ✅ SmartRetriever | ❌ None |
| **Three-Tier Retrieval** | ✅ ThreeTierRetriever | ❌ None |
| **MCP Tools** | ❌ None | ✅ search/timeline/get_observations |

**claw-mem Retrieval Pipeline:**
```python
# Search mode: keyword → bm25 → hybrid → entity → heuristic → smart
search_mode = os.environ.get('CLAW_MEM_SEARCH_MODE', 'enhanced_smart')

# Three-tier retrieval process
retriever = ThreeTierRetriever(workspace)
results = retriever.retrieve(query, top_k=10)
```

**claude-mem MCP Workflow:**
```typescript
// Three-layer token optimization workflow
// 1. search: Get compressed index (~50-100 tokens/result)
search(query="authentication bug", limit=10)

// 2. timeline: Get temporal context
timeline(observation_id=123)

// 3. get_observations: Get full details (~500-1000 tokens/result)
get_observations(ids=[123, 456])
```

### 2.3 Automation Integration

| Feature | claw-mem | claude-mem |
|---------|----------|------------|
| **Auto-Recall** | ✅ Hook auto-injection | ✅ SessionStart Hook |
| **Auto-Capture** | ✅ Hook auto-storage | ✅ PostToolUse Hook |
| **Context Injection** | ✅ Automatic | ✅ Configurable |
| **Progressive Disclosure** | ❌ None | ✅ Three-layer token optimization |
| **Endless Mode** | ❌ None | ✅ Beta biomimetic memory |

---

## 3. Performance Comparison

### 3.1 Latency Analysis

| Operation | claw-mem | claude-mem | Difference |
|-----------|----------|------------|------------|
| **Initialize** | ~4ms | ~100-200ms | 25-50x |
| **Store** | ~8ms | ~20-50ms | 2.5-6x |
| **Search** | ~5ms | ~50-100ms | 10-20x |
| **Average** | ~6ms | ~50-100ms | 8-16x |

**Reason Analysis:**
- claw-mem: stdio JSON-RPC (local process communication)
- claude-mem: HTTP API (network stack overhead)

### 3.2 Memory Footprint

| Component | claw-mem | claude-mem |
|-----------|----------|------------|
| **Python Bridge** | ~10-20MB | - |
| **Bun Worker** | - | ~50-100MB |
| **SQLite** | Shared | Shared |
| **Chroma Vector DB** | - | ~100-200MB |
| **Total** | ~10-20MB | ~150-300MB |

### 3.3 Scalability

| Dimension | claw-mem | claude-mem |
|-----------|----------|------------|
| **Concurrent Clients** | Single process | Multi-client shared worker |
| **Distributed Deployment** | ❌ Not supported | ✅ Via HTTP API |
| **Web UI** | ❌ None | ✅ localhost:37777 |
| **Multi-Platform Support** | OpenClaw only | Claude Code / Gemini CLI / OpenCode / OpenClaw |

---

## 4. Developer Experience Comparison

### 4.1 Installation Methods

**claw-mem:**
```bash
# Python package
pip install claw-mem

# OpenClaw plugin
npm install @opensourceclaw/openclaw-claw-mem
```

**claude-mem:**
```bash
# Claude Code installation
npx claude-mem install

# OpenClaw installation
curl -fsSL https://install.cmem.ai/openclaw.sh | bash
```

### 4.2 Configuration Management

**claw-mem:**
```json
{
  "plugins": {
    "slots": {
      "memory": "claw-mem"
    },
    "claw-mem": {
      "config": {
        "workspaceDir": "~/.openclaw/workspace",
        "autoRecall": true,
        "autoCapture": true,
        "topK": 10
      }
    }
  }
}
```

**claude-mem:**
```json
{
  "CLAUDE_MEM_MODE": "code--zh",
  "WORKER_PORT": 37777,
  "DATA_DIR": "~/.claude-mem",
  "CONTEXT_INJECTION_ENABLED": true
}
```

### 4.3 Observability

| Feature | claw-mem | claude-mem |
|---------|----------|------------|
| **Web UI** | ❌ None | ✅ localhost:37777 |
| **API Endpoints** | ❌ None | ✅ 10+ REST endpoints |
| **Logging** | ✅ Audit logs | ✅ Worker logs |
| **Checkpoints** | ✅ CheckpointManager | ❌ None |
| **Citations** | ❌ None | ✅ ID reference system |

---

## 5. License & Ecosystem

### 5.1 License Differences

| Project | License | Impact |
|---------|---------|--------|
| claw-mem | Apache 2.0 | ✅ Business-friendly, no viral effect |
| claude-mem | AGPL-3.0 | ⚠️ Network deployment requires open sourcing |

**Key Difference:**
- **Apache 2.0**: Freely integrate into closed-source commercial projects
- **AGPL-3.0**: Must open source when providing services over network

### 5.2 Community Ecosystem

| Dimension | claw-mem | claude-mem |
|-----------|----------|------------|
| **GitHub Stars** | ~100 | ~4,000+ |
| **Multi-language Support** | ✅ CJK native | ✅ 19 language READMEs |
| **Documentation** | Basic | Full documentation site |
| **Update Frequency** | Active | Very active (v12.1.6) |
| **Discord Community** | ❌ None | ✅ Active community |

---

## 6. Use Case Recommendations

### 6.1 When to Choose claw-mem

✅ **Recommended Scenarios:**
1. **Deep OpenClaw Integration** - Python-native, seamless collaboration with neoclaw/claw-rl
2. **Low Latency Requirements** - stdio communication, 6ms average latency
3. **Local-First Deployment** - Zero network overhead, completely offline
4. **Apache License Requirements** - Avoid AGPL viral effect in commercial projects
5. **Three-Tier Memory Architecture** - Separation of Episodic/Semantic/Procedural
6. **Heuristic Retrieval** - SmartRetriever intelligent ranking

❌ **Not Recommended Scenarios:**
1. Need Web UI to view memory
2. Need multi-platform support (Claude Code/Gemini)
3. Need vector search capabilities
4. Need distributed deployment

### 6.2 When to Choose claude-mem

✅ **Recommended Scenarios:**
1. **Claude Code Ecosystem** - Native support, plugin marketplace installation
2. **Multi-Platform Needs** - Supports Claude Code / Gemini CLI / OpenCode
3. **Web UI Monitoring** - localhost:37777 real-time viewing
4. **Vector Search** - Chroma + Embeddings semantic retrieval
5. **Mature Ecosystem** - Complete documentation, community support
6. **Progressive Disclosure** - Three-layer token optimization

❌ **Not Recommended Scenarios:**
1. Sensitive to AGPL license
2. Need extremely low latency (<10ms)
3. Pure local deployment, no network needs

---

## 7. Integration Recommendations

### 7.1 OpenClaw Current State

Based on `MEMORY.md` configuration:
```
neoclaw v2.0.0
├── claw-mem>=1.0.8 (optional, memory extra)
└── claw-rl>=2.0.1 (optional, learning extra)
```

**Current Status:**
- ✅ claw-mem integrated as optional dependency
- ✅ Python-native, no additional processes needed
- ✅ Shared SQLite storage layer with claw-rl

### 7.2 Hybrid Approach Recommendations

**Recommended Architecture:**

```
neoclaw (OpenClaw Core)
├── claw-mem (Internal Memory System)
│   ├── Working Memory Cache
│   ├── Episodic Memory Storage
│   ├── Semantic Memory Index
│   └── Procedural Rule Extraction
│
├── claw-rl (Reinforcement Learning)
│   ├── BinaryRLJudge
│   ├── OPDHintExtractor
│   └── LearningLoop
│
└── claude-mem (Optional External Layer)
    ├── Web UI (localhost:37777)
    ├── Vector Search (Chroma)
    └── MCP Tools (External Integration)
```

**Implementation Steps:**

1. **Keep claw-mem as Core Memory Layer**
   - Reason: Python-native, low latency, Apache license

2. **Optional Integration of claude-mem Web UI**
   - Connect to claw-mem's SQLite data via HTTP API
   - Provide visual monitoring capabilities

3. **Vector Search Extension**
   - Add Chroma vector retrieval in claw-mem
   - Reference claude-mem's Embedding approach

### 7.3 Feature Gap Analysis

| Need to Add | claw-mem | Source |
|-------------|----------|--------|
| Web UI | ❌ Missing | Can integrate claude-mem UI or build custom |
| Vector Search | ❌ Missing | Can add Chroma integration |
| MCP Tools | ❌ Missing | Can implement MCP protocol adapter |
| Memory Compression | ❌ Missing | Can add AI Summarization |
| Privacy Tags | ❌ Missing | Can add `<private>` filtering |

---

## 8. Summary

### 8.1 Core Differences

| Dimension | claw-mem | claude-mem |
|-----------|----------|------------|
| **Design Philosophy** | Local-first, Python-native | Platform-agnostic, HTTP service |
| **Target Users** | OpenClaw developers | Claude Code users |
| **License** | Apache 2.0 (Business-friendly) | AGPL-3.0 (Viral open source) |
| **Performance** | Ultra-low latency (6ms) | Medium latency (50-100ms) |
| **Feature Completeness** | Memory core features | Memory + UI + Vector search |

### 8.2 Final Recommendations

**For OpenClaw Project:**

1. **Short-term (P0)**: Continue using claw-mem
   - Already integrated, Python-native, low latency
   - Meets core memory requirements

2. **Mid-term (P1)**: Add missing features
   - Add Chroma vector search
   - Implement simple Web UI or CLI viewer
   - Add memory compression (AI Summarization)

3. **Long-term (P2)**: Evaluate hybrid approach
   - If multi-platform support needed, consider claude-mem as external layer
   - If AGPL license becomes an obstacle, keep claw-mem standalone

**Key Decision Factors:**
- ✅ Apache License → claw-mem
- ✅ Deep OpenClaw Integration → claw-mem
- ✅ Ultra-low Latency Requirements → claw-mem
- ❌ Need Web UI → claude-mem or build custom
- ❌ Need Multi-platform → claude-mem

---

**Report Completed**: 2026-04-17 10:30 CST
**Reference Versions**: claw-mem v2.0.0, claude-mem v12.1.6
