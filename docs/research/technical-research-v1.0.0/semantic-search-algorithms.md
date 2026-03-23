# Semantic Search Algorithms for Memory Retrieval

**Version**: 1.0.0
**Date**: 2026-03-23
**Author**: Study Agent
**Status**: Complete

---

## Executive Summary

This document researches semantic search algorithms suitable for the claw-mem v1.0.0 three-tier memory retrieval system. Based on the requirements in `claw-mem-v1.0.0-requirements.md`, the system must achieve:
- Retrieval latency < 2 seconds
- Recall accuracy > 85% (relevant results in top 5)
- Support for 1000+ memory entries

**Recommendation**: Hybrid approach combining BM25 + N-gram for L1/L2, with optional dense retrieval for L3.

---

## 1. Search Algorithm Categories

### 1.1 Lexical/Search Methods

| Algorithm | Speed | Accuracy | Best For |
|-----------|-------|----------|----------|
| **N-gram Match** | O(1) | Medium | Exact phrase matching |
| **BM25** | O(n) | High | Keyword-based retrieval |
| **TF-IDF** | O(n) | Medium | Simple keyword search |

### 1.2 Semantic/Dense Methods

| Algorithm | Speed | Accuracy | Best For |
|-----------|-------|----------|----------|
| **Sentence Transformers** | O(nd) | Very High | Semantic similarity |
| **BERT Bi-Encoder** | O(nd) | Very High | Cross-lingual retrieval |
| **ColBERT** | O(nd) | Highest | Fine-grained matching |

---

## 2. Recommended Approach for claw-mem

### 2.1 Tiered Search Strategy

Based on the three-tier memory architecture:

```
L1 (Working Memory) - In-Memory Cache
├── Algorithm: N-gram + Cache Lookup
├── Latency Target: <10ms
└── Rationale: O(1) lookup for recent items

L2 (Short-term Memory) - Daily Memory Files
├── Algorithm: BM25 + N-gram Hybrid
├── Latency Target: <100ms
└── Rationale: Fast keyword search with phrase matching

L3 (Long-term Memory) - MEMORY.md
├── Algorithm: Hybrid (BM25 + Optional Dense)
├── Latency Target: <500ms
└── Rationale: Semantic understanding for permanent memories
```

### 2.2 Hybrid Fusion Formula

```python
def reciprocal_rank_fusion(results: List[List[Tuple[str, float]]], k: int = 60):
    """
    Reciprocal Rank Fusion for combining multiple retrieval results.

    Args:
        results: List of ranked result lists from different retrievers
        k: Ranking constant (default 60)

    Returns:
        Fused and re-ranked results
    """
    fused_scores: Dict[str, float] = defaultdict(float)

    for result_list in results:
        for rank, (doc_id, score) in enumerate(result_list):
            fused_scores[doc_id] += 1.0 / (k + rank)

    return sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
```

---

## 3. Algorithm Deep Dive

### 3.1 N-gram Index (Already Implemented)

**Current Implementation** (from ARCHITECTURE.md):
```python
class NGramIndex:
    def __init__(self, n: int = 3):
        self.n = n
        self.index: Dict[str, Set[MemoryID]] = defaultdict(set)

    def search(self, query: str, limit: int = 10) -> List[MemoryID]:
        tokens = self.tokenize(query)
        if len(tokens) < self.n:
            return []

        ngram = ' '.join(tokens[:self.n])
        return list(self.index.get(ngram, set()))[:limit]
```

**Pros**:
- O(1) lookup time
- Excellent for exact phrase matching
- No external dependencies

**Cons**:
- Cannot handle semantic similarity
- Requires exact word matches
- Index size grows with corpus

**Recommendation**: Keep as-is for L1/L2 phrase matching.

### 3.2 BM25 (Already in Architecture)

**Implementation Reference**:
```python
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.memory_ids: List[MemoryID] = []
        self.documents: List[List[str]] = []

    def build_index(self, memories: List[Memory]) -> None:
        self.memory_ids = [m.id for m in memories]
        self.documents = [self.tokenize(m.content) for m in memories]
        self.bm25 = BM25Okapi(self.documents)

    def search(self, query: str, limit: int = 10) -> List[Tuple[MemoryID, float]]:
        scores = self.bm25.get_scores(self.tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(self.memory_ids[i], score) for i, score in ranked[:limit]]
```

**Pros**:
- Industry standard for keyword search
- Handles term frequency well
- Fast for moderate corpus sizes
- Works well with N-gram fusion

**Cons**:
- No semantic understanding
- Synonym handling requires expansion

**Recommendation**: Primary retrieval for L2, combine with L3.

### 3.3 Dense Retrieval (Optional for v1.0.0)

**When to Consider**:
- L3 memory exceeds 10,000 entries
- Semantic matching is critical
- Users report "missing" relevant memories

**Recommended Models** (2025 benchmarks):

| Model | Dimensions | Speed | MTEB Score |
|-------|------------|-------|------------|
| `all-MiniLM-L6-v2` | 384 | Fast | 61.2 |
| `bge-small-en-v1.5` | 384 | Fast | 62.8 |
| `bge-base-en-v1.5` | 768 | Medium | 64.2 |
| `e5-large-v2` | 1024 | Slow | 65.1 |

**Implementation** (if needed):
```python
from sentence_transformers import SentenceTransformer

class DenseRetriever:
    def __init__(self, model_name: str = "bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.embeddings: np.ndarray = None
        self.memory_ids: List[MemoryID] = []

    def build_index(self, memories: List[Memory]) -> None:
        self.memory_ids = [m.id for m in memories]
        texts = [m.content for m in memories]
        self.embeddings = self.model.encode(texts, normalize_embeddings=True)

    def search(self, query: str, limit: int = 10) -> List[Tuple[MemoryID, float]]:
        query_emb = self.model.encode([query], normalize_embeddings=True)[0]
        scores = cosine_similarity([query_emb], self.embeddings)[0]
        ranked = np.argsort(scores)[::-1][:limit]
        return [(self.memory_ids[i], scores[i]) for i in ranked]
```

---

## 4. Implementation Priority

### Phase 1 (v1.0.0 Core - P0)
- [x] N-gram index (already in codebase)
- [ ] BM25 implementation
- [ ] Hybrid fusion (N-gram + BM25)
- [ ] Intent classification for topic detection

### Phase 2 (Post-v1.0.0 - P1)
- [ ] Dense retrieval optional integration
- [ ] ChromaDB/FAISS for vector storage
- [ ] Query expansion for synonyms

### Phase 3 (Future - P2)
- [ ] ColBERT for fine-grained matching
- [ ] Learning-to-rank models
- [ ] Multi-stage retrieval pipeline

---

## 5. Performance Estimates

### Benchmark Predictions (1000 memories)

| Configuration | Index Build | Query Latency | Memory Usage |
|---------------|-------------|---------------|--------------|
| N-gram only | 50ms | 5ms | 10MB |
| BM25 only | 100ms | 20ms | 15MB |
| N-gram + BM25 | 150ms | 25ms | 25MB |
| + Dense (384d) | 500ms | 50ms | 100MB |

### Scalability Analysis

| Memory Count | N-gram | BM25 | Dense |
|--------------|--------|------|-------|
| 100 | 2ms | 5ms | 10ms |
| 1,000 | 5ms | 20ms | 50ms |
| 10,000 | 10ms | 100ms | 200ms |
| 100,000 | 50ms | 500ms | 800ms |

---

## 6. References

1. Robertson, S., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval*.

2. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *EMNLP*.

3. Thakur, N., et al. (2021). BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. *NeurIPS*.

4. Chen, J., et al. (2024). MTEB: Massive Text Embedding Benchmark. *arXiv preprint*.

---

**Document History**:
| Date | Version | Change |
|------|---------|--------|
| 2026-03-23 | 1.0 | Initial research document |
