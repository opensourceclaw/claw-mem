# Vector Database Options for Memory Storage

**Version**: 1.0.0
**Date**: 2026-03-23
**Author**: Study Agent
**Status**: Complete

---

## Executive Summary

This document evaluates vector database options for claw-mem v1.0.0. Based on the project's design principles (Local-First, Zero LLM Pipeline, Keep It Simple), the recommendation is:

**v1.0.0 Decision**: Do NOT integrate a vector database. Use in-memory index with Markdown storage as specified in ARCHITECTURE.md.

**Future Consideration**: If dense retrieval becomes necessary (Phase 2+), ChromaDB is the recommended choice.

---

## 1. Design Principle Alignment

claw-mem v1.0.0 design principles from ARCHITECTURE.md:

| Principle | Requirement | Vector DB Impact |
|-----------|-------------|------------------|
| **Local-First** | No cloud dependency | Most vector DBs support local |
| **Zero LLM Pipeline** | L1/L2 without LLM | Vector DBs require embeddings |
| **Keep It Simple** | Markdown-only, no external DBs | Vector DBs add complexity |
| **Minimal Dependencies** | Pure Python + standard library | Vector DBs add dependencies |
| **OpenClaw Compatible** | Existing memory formats | No conflict |

**Conclusion**: Vector databases add complexity that conflicts with v1.0.0 simplicity goals.

---

## 2. Vector Database Options (For Future Reference)

### 2.1 ChromaDB

| Attribute | Details |
|-----------|---------|
| **Type** | Embedded vector database |
| **Language** | Python, JavaScript |
| **Storage** | Local SQLite + files |
| **License** | Apache 2.0 |
| **GitHub** | chroma-core/chroma |

**Pros**:
- Embedded mode (no server required)
- Simple Python API
- Built-in persistence
- HNSW indexing for fast search
- Active community

**Cons**:
- Adds dependency (~100MB)
- Requires embedding generation
- Learning curve for API

**API Example**:
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection(name="memories")

# Add memories
collection.add(
    documents=["Memory content 1", "Memory content 2"],
    metadatas=[{"type": "semantic"}, {"type": "episodic"}],
    ids=["mem1", "mem2"]
)

# Query
results = collection.query(
    query_texts=["search query"],
    n_results=10
)
```

**Recommendation**: Best choice IF vector storage is needed in Phase 2+.

---

### 2.2 FAISS (Facebook AI Similarity Search)

| Attribute | Details |
|-----------|---------|
| **Type** | Similarity search library |
| **Language** | Python, C++ |
| **Storage** | File-based (manual) |
| **License** | MIT |
| **GitHub** | facebookresearch/faiss |

**Pros**:
- Extremely fast (C++ backend)
- Multiple index types (IVF, HNSW, PQ)
- GPU support available
- Industry standard

**Cons**:
- Not a database (no persistence built-in)
- Complex API for advanced features
- Requires manual index management
- Facebook/Meta dependency

**API Example**:
```python
import faiss
import numpy as np

# Create index
dimension = 384
index = faiss.IndexFlatL2(dimension)

# Add vectors
vectors = np.array([[...], [...]], dtype='float32')
index.add(vectors)

# Search
query = np.array([[...]], dtype='float32')
distances, indices = index.search(query, k=10)
```

**Recommendation**: Use only if FAISS-specific features needed (GPU, quantization).

---

### 2.3 Qdrant

| Attribute | Details |
|-----------|---------|
| **Type** | Vector search engine |
| **Language** | Rust core, Python client |
| **Storage** | Local or server mode |
| **License** | Apache 2.0 |
| **GitHub** | qdrant/qdrant |

**Pros**:
- High performance (Rust backend)
- REST API + gRPC
- Rich filtering support
- Local mode available

**Cons**:
- Server deployment complexity
- Overkill for personal use
- Additional infrastructure

**Recommendation**: Not recommended for claw-mem (too complex).

---

### 2.4 LanceDB

| Attribute | Details |
|-----------|---------|
| **Type** | Embedded vector database |
| **Language** | Python, Rust |
| **Storage** | Local files |
| **License** | Apache 2.0 |
| **GitHub** | lancedb/lancedb |

**Pros**:
- Serverless, embedded
- Columnar storage (Lance format)
- SQL-like queries
- Good for hybrid search

**Cons**:
- Newer project (less mature)
- Adds Rust dependency

**Recommendation**: Consider as alternative to ChromaDB if needed.

---

## 3. Comparison Matrix

| Feature | ChromaDB | FAISS | Qdrant | LanceDB | In-Memory (Current) |
|---------|----------|-------|--------|---------|---------------------|
| **Embedded Mode** | Yes | Yes | Limited | Yes | Yes |
| **Persistence** | Built-in | Manual | Built-in | Built-in | Markdown files |
| **Speed** | Fast | Fastest | Fast | Fast | Fastest (RAM) |
| **Complexity** | Low | Medium | High | Low | Lowest |
| **Dependencies** | ~100MB | ~50MB | Server | ~80MB | None |
| **License** | Apache 2.0 | MIT | Apache 2.0 | Apache 2.0 | Apache 2.0 |
| **Best For** | Phase 2+ | GPU search | Enterprise | Hybrid | v1.0.0 |

---

## 4. Implementation Strategy

### v1.0.0 (Current Sprint)
```
Storage: Markdown files only
Index: In-memory (N-gram + BM25)
Search: Hybrid lexical (no vectors)
```

**Architecture**:
```
claw_mem/
├── storage/
│   └── markdown_store.py    # Markdown file storage
├── retrieval/
│   ├── keyword.py           # Keyword search
│   ├── bm25.py              # BM25 search
│   └── hybrid.py            # Hybrid retriever
└── storage/
    └── index.py             # In-memory index (no vector DB)
```

### Phase 2+ (If Dense Retrieval Needed)
```
Storage: Markdown files + ChromaDB
Index: In-memory (lexical) + ChromaDB (semantic)
Search: Hybrid (lexical + dense)
```

**Implementation Path**:
```python
# Optional ChromaDB integration (Phase 2)
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

if CHROMADB_AVAILABLE:
    client = chromadb.Client()
    collection = client.get_or_create_collection("memories")
    # Use dense retrieval
else:
    # Fall back to BM25 only
    pass
```

---

## 5. When to Add Vector Database

**Trigger Conditions**:
1. L3 memory exceeds 10,000 entries
2. User feedback indicates poor semantic recall
3. Users specifically request semantic search
4. Performance allows (latency budget available)

**Decision Tree**:
```
Need semantic search?
├── No → Continue with BM25 only (v1.0.0 approach)
└── Yes
    ├── < 10K memories → In-memory embeddings (FAISS or numpy)
    └── >= 10K memories → ChromaDB with persistence
```

---

## 6. Cost Analysis

### In-Memory Index (Current Approach)

| Cost | Amount |
|------|--------|
| Dependencies | None (rank-bm25 only) |
| Memory Usage | ~25MB for 1,000 memories |
| Disk Usage | Markdown files only |
| Startup Time | ~100ms for index build |

### ChromaDB Integration (Phase 2+)

| Cost | Amount |
|------|--------|
| Dependencies | chromadb (~100MB) |
| Memory Usage | ~50MB for 1,000 memories |
| Disk Usage | Markdown + Chroma files (~2x) |
| Startup Time | ~500ms for index + vector load |
| Embedding Cost | ~100ms per memory (one-time) |

---

## 7. References

1. ChromaDB Documentation. https://docs.trychroma.com/

2. FAISS GitHub. https://github.com/facebookresearch/faiss

3. Qdrant Documentation. https://qdrant.tech/documentation/

4. LanceDB Documentation. https://lancedb.github.io/lancedb/

5. claw-mem ARCHITECTURE.md - Section 4.5: In-Memory Index

---

**Document History**:
| Date | Version | Change |
|------|---------|--------|
| 2026-03-23 | 1.0 | Initial research document |
