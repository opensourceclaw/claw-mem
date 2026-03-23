# Best Practices for Memory Systems

**Version**: 1.0.0
**Date**: 2026-03-23
**Author**: Study Agent
**Status**: Complete

---

## Executive Summary

This document provides best practices for building memory systems for AI agents, covering architecture patterns, RAG (Retrieval-Augmented Generation) techniques, testing strategies, and performance optimization.

**Target Audience**: Dev Agent implementing claw-mem v1.0.0

---

## Part 1: Memory System Architecture Patterns

### 1.1 Tiered Memory Architecture

**Pattern**: Multi-layer memory with different characteristics per layer.

```
┌─────────────────────────────────────────────────────────┐
│              Three-Tier Memory Architecture              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  L1: Working Memory (Fast, Volatile)                    │
│  ├── Location: In-memory cache                          │
│  ├── Latency: <10ms                                     │
│  ├── Capacity: Current session only                     │
│  └── Use Case: Session context, recent items            │
│                                                         │
│  L2: Short-term Memory (Fast, Semi-persistent)          │
│  ├── Location: Daily Markdown files                     │
│  ├── Latency: <100ms                                    │
│  ├── Capacity: 30-day rolling window                    │
│  └── Use Case: Recent conversations, episodic memory    │
│                                                         │
│  L3: Long-term Memory (Slower, Persistent)              │
│  ├── Location: MEMORY.md (semantic), skills/ (procedural)│
│  ├── Latency: <500ms                                    │
│  ├── Capacity: Unlimited (permanent)                    │
│  └── Use Case: Core facts, user preferences, skills     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation Guidelines**:

1. **Clear Boundaries**: Each layer has distinct access patterns
2. **Automatic Promotion**: Important L2 memories can be promoted to L3
3. **Graceful Degradation**: System works if any single layer fails

### 1.2 Repository Pattern for Storage

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class MemoryRepository(ABC):
    """Abstract repository interface for memory storage"""

    @abstractmethod
    def get(self, memory_id: str) -> Optional[Memory]:
        pass

    @abstractmethod
    def find(self, query: str, limit: int = 10) -> List[Memory]:
        pass

    @abstractmethod
    def save(self, memory: Memory) -> None:
        pass

    @abstractmethod
    def delete(self, memory_id: str) -> None:
        pass

class MarkdownRepository(MemoryRepository):
    """Concrete implementation using Markdown files"""

    def __init__(self, workspace_path: str):
        self.workspace = Path(workspace_path)

    def get(self, memory_id: str) -> Optional[Memory]:
        # Implementation
        pass

    def find(self, query: str, limit: int = 10) -> List[Memory]:
        # Implementation
        pass

    def save(self, memory: Memory) -> None:
        # Implementation
        pass

    def delete(self, memory_id: str) -> None:
        # Implementation
        pass
```

**Benefits**:
- Easy to swap storage backends
- Testable with mock repositories
- Clean separation of concerns

### 1.3 Caching Strategy

```python
from functools import lru_cache
from typing import Optional

class CachedMemoryManager:
    """Memory manager with LRU caching"""

    def __init__(self, repository: MemoryRepository, cache_size: int = 100):
        self.repository = repository
        self.cache_size = cache_size
        self._cache: Dict[str, Memory] = {}

    @lru_cache(maxsize=100)
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Cached memory retrieval"""
        # Check L1 cache first
        if memory_id in self._cache:
            return self._cache[memory_id]

        # Fall back to repository
        memory = self.repository.get(memory_id)
        if memory:
            self._cache[memory_id] = memory

        return memory

    def invalidate_cache(self, memory_id: str) -> None:
        """Invalidate cache for updated memories"""
        self._cache.pop(memory_id, None)
        if hasattr(self.get_memory, 'cache_clear'):
            self.get_memory.cache_clear()
```

---

## Part 2: RAG Best Practices

### 2.1 Retrieval Pipeline

```
Query → Pre-processing → Search → Re-ranking → Context Assembly → LLM
```

**Step-by-Step Implementation**:

```python
class RAGPipeline:
    """Retrieval-Augmented Generation pipeline"""

    def __init__(self, retriever: Retriever, reranker: Optional[ReRanker] = None):
        self.retriever = retriever
        self.reranker = reranker or DefaultReRanker()

    def process_query(self, query: str) -> ProcessedQuery:
        """Pre-process query: tokenize, expand, embed"""
        # 1. Tokenize
        tokens = self.tokenize(query)

        # 2. Query expansion (optional)
        expanded = self.expand_query(tokens)

        # 3. Generate embedding (if using dense retrieval)
        embedding = self.embed(query) if self.use_dense else None

        return ProcessedQuery(tokens=tokens, expanded=expanded, embedding=embedding)

    def retrieve(self, query: str, limit: int = 10) -> List[Memory]:
        """Retrieve and re-rank memories"""
        # Initial retrieval
        candidates = self.retriever.search(query, limit=limit * 2)

        # Re-ranking
        if self.reranker:
            reranked = self.reranker.rank(query, candidates)
        else:
            reranked = sorted(candidates, key=lambda x: x.score, reverse=True)

        return reranked[:limit]

    def assemble_context(self, memories: List[Memory], max_tokens: int = 1000) -> str:
        """Assemble retrieved memories into context"""
        context_parts = []
        current_tokens = 0

        for memory in memories:
            memory_text = self.format_memory(memory)
            memory_tokens = self.count_tokens(memory_text)

            if current_tokens + memory_tokens > max_tokens:
                break

            context_parts.append(memory_text)
            current_tokens += memory_tokens

        return "\n\n".join(context_parts)
```

### 2.2 Query Expansion

Improve retrieval by expanding queries with synonyms:

```python
class QueryExpander:
    """Expand queries with synonyms for better retrieval"""

    SYNONYM_MAP = {
        'deploy': ['deploy', 'deployment', 'release', 'publish'],
        'search': ['search', 'find', 'retrieve', 'lookup'],
        'memory': ['memory', 'memories', 'context', 'history'],
        # Add more as needed
    }

    def expand(self, query: str) -> str:
        """Expand query with synonyms"""
        terms = query.lower().split()
        expanded_terms = []

        for term in terms:
            if term in self.SYNONYM_MAP:
                expanded_terms.extend(self.SYNONYM_MAP[term])
            else:
                expanded_terms.append(term)

        return ' '.join(expanded_terms)
```

### 2.3 Re-ranking Strategies

```python
from typing import List, Tuple

class ReRanker:
    """Re-rank retrieved documents"""

    def rank(self, query: str, documents: List[Memory]) -> List[Memory]:
        """Re-rank documents based on query relevance"""
        scored = [(doc, self.score(query, doc)) for doc in documents]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, score in scored]

    def score(self, query: str, document: Memory) -> float:
        """Calculate relevance score"""
        # Combine multiple signals
        lexical_score = self.lexical_match(query, document)
        recency_score = self.recency_bonus(document)
        importance_score = document.importance_score

        # Weighted combination
        return (0.5 * lexical_score +
                0.3 * recency_score +
                0.2 * importance_score)

    def recency_bonus(self, document: Memory) -> float:
        """Give bonus to recent memories"""
        from datetime import datetime
        days_old = (datetime.now() - document.created_at).days
        return 1.0 / (1.0 + days_old * 0.1)  # Decay over time
```

---

## Part 3: Test Coverage Strategies

### 3.1 Testing Pyramid

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲         (10% - Full workflow)
                 ╱──────╲
                ╱        ╲
               ╱Integration╲      (30% - Module integration)
              ╱────────────╲
             ╱              ╲
            ╱   Unit Tests   ╲     (60% - Individual functions)
           ╱──────────────────╲
```

### 3.2 Unit Test Examples

```python
import pytest
from claw_mem.retrieval.bm25 import BM25Retriever
from claw_mem.memory.models import Memory

class TestBM25Retriever:
    """Unit tests for BM25 retrieval"""

    @pytest.fixture
    def sample_memories(self) -> List[Memory]:
        return [
            Memory(id="1", content="User prefers Python for development"),
            Memory(id="2", content="Deployment happens via twine upload"),
            Memory(id="3", content="User likes Chinese food in Shanghai"),
        ]

    @pytest.fixture
    def retriever(self, sample_memories: List[Memory]) -> BM25Retriever:
        retriever = BM25Retriever()
        retriever.build_index(sample_memories)
        return retriever

    def test_search_returns_results(self, retriever: BM25Retriever):
        results = retriever.search("Python", limit=5)
        assert len(results) > 0
        assert results[0][0].id == "1"  # Most relevant first

    def test_search_respects_limit(self, retriever: BM25Retriever):
        results = retriever.search("user", limit=2)
        assert len(results) <= 2

    def test_search_empty_query(self, retriever: BM25Retriever):
        results = retriever.search("", limit=5)
        assert len(results) == 0

    def test_search_no_matches(self, retriever: BM25Retriever):
        results = retriever.search("quantum computing", limit=5)
        assert len(results) == 0
```

### 3.3 Integration Test Examples

```python
import pytest
import tempfile
from pathlib import Path
from claw_mem.storage.markdown_store import MarkdownRepository
from claw_mem.retrieval.hybrid import HybridRetriever

class TestHybridRetrievalIntegration:
    """Integration tests for hybrid retrieval"""

    @pytest.fixture
    def temp_workspace(self) -> Path:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_hybrid_retrieval_across_layers(self, temp_workspace: Path):
        # Setup
        store = MarkdownRepository(temp_workspace)
        retriever = HybridRetriever(store)

        # Add test memories
        store.save(Memory(id="l1_1", content="L1 working memory test", layer="l1"))
        store.save(Memory(id="l2_1", content="L2 short-term memory test", layer="l2"))
        store.save(Memory(id="l3_1", content="L3 long-term memory test", layer="l3"))

        # Search across all layers
        results = retriever.search("memory test", layers=["l1", "l2", "l3"], limit=10)

        # Verify results from all layers
        assert len(results) == 3
        layers = {r.layer for r in results}
        assert layers == {"l1", "l2", "l3"}
```

### 3.4 Test Coverage Requirements

| Component | Minimum Coverage | Priority |
|-----------|------------------|----------|
| core/memory_manager.py | 95% | P0 |
| retrieval/*.py | 90% | P0 |
| storage/*.py | 90% | P0 |
| cli.py | 80% | P1 |
| utils/*.py | 70% | P2 |

### 3.5 Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=claw_mem --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_bm25_retriever.py -v

# Run tests matching pattern
pytest -k "test_search" -v

# Run tests and fail on coverage threshold
pytest --cov=claw_mem --cov-fail-under=90
```

---

## Part 4: Performance Optimization Techniques

### 4.1 Lazy Loading (Already Implemented)

From F2_LAZY_LOADING.md:

```python
def _ensure_loaded(self) -> None:
    """Ensure index is loaded (lazy loading support)"""
    if self.built:
        return

    # Try to load from disk
    if self.enable_persistence and self.index_file.exists():
        loaded = self.load_index()
        if loaded:
            print(f"💾 Index lazy-loaded from disk: {len(self.memory_ids)} memories")
            return
```

### 4.2 Batch Operations

```python
class BatchMemoryWriter:
    """Batch write for better I/O performance"""

    def __init__(self, repository: MemoryRepository, batch_size: int = 100):
        self.repository = repository
        self.batch_size = batch_size
        self.pending: List[Memory] = []

    def write(self, memory: Memory) -> None:
        self.pending.append(memory)
        if len(self.pending) >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        if not self.pending:
            return

        # Single write operation for batch
        self.repository.save_batch(self.pending)
        self.pending = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()  # Ensure flush on exit
```

### 4.3 Index Optimization

```python
class OptimizedInMemoryIndex:
    """Optimized in-memory index"""

    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.ngram_index: Dict[str, Set[str]] = defaultdict(set)
        self._built = False

    def build_incremental(self, new_memories: List[Memory]) -> None:
        """Build index incrementally instead of full rebuild"""
        for memory in new_memories:
            self._add_to_ngram(memory)
            self.memories[memory.id] = memory
        self._built = True

    def _add_to_ngram(self, memory: Memory) -> None:
        """Add single memory to ngram index"""
        tokens = self._tokenize(memory.content)
        for i in range(len(tokens) - 3 + 1):
            ngram = ' '.join(tokens[i:i+3])
            self.ngram_index[ngram].add(memory.id)
```

### 4.4 Performance Benchmarks

```python
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

class TestRetrievalPerformance:
    """Performance benchmarks for retrieval"""

    @pytest.fixture
    def large_index(self) -> HybridRetriever:
        """Create retriever with 10,000 memories"""
        retriever = HybridRetriever(store)
        for i in range(10000):
            store.save(Memory(id=f"mem_{i}", content=f"Test memory {i}"))
        return retriever

    def test_bm25_search_latency(self, large_index: HybridRetriever, benchmark: BenchmarkFixture):
        """Benchmark BM25 search latency"""
        result = benchmark(large_index.bm25_search, "test memory")
        assert benchmark.stats.stats.mean < 0.1  # < 100ms

    def test_ngram_search_latency(self, large_index: HybridRetriever, benchmark: BenchmarkFixture):
        """Benchmark N-gram search latency"""
        result = benchmark(large_index.ngram_search, "test memory")
        assert benchmark.stats.stats.mean < 0.01  # < 10ms

    def test_hybrid_search_latency(self, large_index: HybridRetriever, benchmark: BenchmarkFixture):
        """Benchmark hybrid search latency"""
        result = benchmark(large_index.search, "test memory", 10)
        assert benchmark.stats.stats.mean < 0.5  # < 500ms
```

**Performance Targets**:
| Operation | Target Latency | Current | Status |
|-----------|----------------|---------|--------|
| N-gram search | <10ms | ~5ms | ✅ |
| BM25 search | <100ms | ~50ms | ✅ |
| Hybrid search | <500ms | TBD | ⚠️ |
| Index build (1K memories) | <1s | ~150ms | ✅ |
| Context injection | <1s | TBD | ⚠️ |

---

## Part 5: Checklist for claw-mem v1.0.0

### Architecture
- [ ] Three-tier memory implemented (L1/L2/L3)
- [ ] Repository pattern for storage abstraction
- [ ] Caching strategy in place

### RAG
- [ ] Query pre-processing implemented
- [ ] Hybrid retrieval (N-gram + BM25) working
- [ ] Re-ranking based on relevance/recency
- [ ] Context assembly with length limits

### Testing
- [ ] Unit tests for all core modules (90%+ coverage)
- [ ] Integration tests for retrieval pipeline
- [ ] Performance benchmarks established

### Performance
- [ ] Lazy loading implemented
- [ ] Batch operations for writes
- [ ] Index optimization (incremental builds)
- [ ] All latency targets met

---

## References

1. Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS*.

2. Guu, K., et al. (2020). REALM: Retrieval-Augmented Language Model Pre-Training. *ICML*.

3. claw-mem ARCHITECTURE.md - Three-tier memory design

4. F2_LAZY_LOADING.md - Lazy loading implementation

5. pytest documentation - https://docs.pytest.org/

6. pytest-benchmark - https://pytest-benchmark.readthedocs.io/

---

**Document History**:
| Date | Version | Change |
|------|---------|--------|
| 2026-03-23 | 1.0 | Initial best practices document |
