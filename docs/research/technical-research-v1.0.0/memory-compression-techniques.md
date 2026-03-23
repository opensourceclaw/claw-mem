# Memory Compression Techniques

**Version**: 1.0.0
**Date**: 2026-03-23
**Author**: Study Agent
**Status**: Complete

---

## Executive Summary

This document researches memory compression techniques for claw-mem v1.0.0. Building on the existing F5_COMPRESSION.md implementation (gzip compression achieving 82.5% reduction), this research covers:

1. **Index Compression** - Already implemented (gzip)
2. **Memory Content Compression** - For large memory entries
3. **Embedding Compression** - For future dense retrieval
4. **Deduplication** - Remove redundant memories

**Recommendation**: Keep current gzip compression, add optional content deduplication for v1.0.0.

---

## 1. Current Implementation (v0.7.0)

### Gzip Index Compression

From F5_COMPRESSION.md:

```python
import gzip

def save_index(self) -> bool:
    """Save index to disk with compression"""
    temp_file = self.index_file.with_suffix('.pkl.gz.tmp')

    # Serialize index
    serialized = pickle.dumps(self.index)

    # Compress and save
    with gzip.open(temp_file, 'wb') as f:
        f.write(serialized)

    # Atomic rename
    temp_file.rename(self.index_file)
    return True
```

**Results**:
| Metric | Uncompressed | Compressed | Reduction |
|--------|-------------|------------|-----------|
| File Size | 1.2 MB | 210 KB | 82.5% |
| Save Time | 50ms | 55ms | +10% |
| Load Time | 45ms | 50ms | +11% |

**Status**: Already implemented and working. No changes needed for v1.0.0.

---

## 2. Memory Content Compression

### 2.1 When to Compress Memory Content

**Triggers**:
- Single memory entry > 10KB
- Daily memory file > 1MB
- Total memory storage > 100MB

### 2.2 Compression Strategies

#### Strategy A: Transparent Gzip (Recommended)

Compress large Markdown files transparently:

```python
import gzip
from pathlib import Path

class CompressedMarkdownStore:
    COMPRESSION_THRESHOLD = 1024 * 1024  # 1MB

    def write(self, content: str, path: Path) -> None:
        content_bytes = content.encode('utf-8')

        if len(content_bytes) > self.COMPRESSION_THRESHOLD:
            # Compress large files
            compressed_path = path.with_suffix('.md.gz')
            with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
                f.write(content)
        else:
            # Keep small files uncompressed
            path.write_text(content)

    def read(self, path: Path) -> str:
        # Auto-detect compression
        if path.with_suffix('.md.gz').exists():
            with gzip.open(path.with_suffix('.md.gz'), 'rt', encoding='utf-8') as f:
                return f.read()
        return path.read_text()
```

**Pros**:
- Transparent to application
- Significant space savings for large files
- Compatible with existing format

**Cons**:
- Slight CPU overhead
- Cannot view compressed files directly in text editor

---

#### Strategy B: Summarization Compression

Use LLM to compress memory content:

```python
def compress_memory_content(content: str, max_length: int = 500) -> str:
    """Use LLM to summarize long memory content"""
    if len(content) <= max_length:
        return content

    # Prompt for summarization
    prompt = f"""Summarize the following memory content in under {max_length} characters:

{content}

Summary:"""

    # Call LLM (if available)
    summary = call_llm(prompt)
    return f"[SUMMARIZED] {summary}"
```

**Pros**:
- Semantic compression (preserves meaning)
- Human-readable output
- Reduces token count for RAG

**Cons**:
- Requires LLM (conflicts with "Zero LLM Pipeline")
- Potential information loss
- Slower compression

**Recommendation**: Do NOT implement for v1.0.0 (violates design principles). Consider for Phase 2+ as optional feature.

---

## 3. Embedding Compression (For Future Dense Retrieval)

If dense retrieval is added (Phase 2+), embedding compression becomes relevant.

### 3.1 Quantization

Reduce embedding precision:

| Method | Bits | Size Reduction | Accuracy Loss |
|--------|------|----------------|---------------|
| FP32 (Original) | 32 | 1x | 0% |
| FP16 | 16 | 50% | <1% |
| INT8 | 8 | 75% | 1-3% |
| Binary | 1 | 97% | 5-10% |

**Implementation** (FAISS example):
```python
import faiss

# Original index (32-bit)
index = faiss.IndexFlatIP(384)

# Quantized index (8-bit)
quantized_index = faiss.IndexPQ(384, 8, 8)
quantized_index.train(vectors)
quantized_index.add(vectors)
```

### 3.2 Dimensionality Reduction

Reduce embedding dimensions:

```python
from sklearn.decomposition import PCA

# Reduce from 768 to 256 dimensions
pca = PCA(n_components=256)
reduced_embeddings = pca.fit_transform(original_embeddings)
```

**Trade-offs**:
- 768d → 256d: 66% size reduction, ~2% accuracy loss
- 768d → 128d: 83% size reduction, ~5% accuracy loss

**Recommendation**: Use `all-MiniLM-L6-v2` (384d) instead of compression for v1.0.0.

---

## 4. Memory Deduplication

### 4.1 Exact Deduplication

Remove duplicate memory entries:

```python
def deduplicate_memories(memories: List[Memory]) -> List[Memory]:
    """Remove exact duplicate memories"""
    seen_contents = set()
    unique_memories = []

    for memory in memories:
        content_hash = hash(memory.content.strip())
        if content_hash not in seen_contents:
            seen_contents.add(content_hash)
            unique_memories.append(memory)

    return unique_memories
```

### 4.2 Near-Deduplication (Fuzzy Matching)

Remove near-duplicate memories:

```python
from difflib import SequenceMatcher

def is_near_duplicate(content1: str, content2: str, threshold: float = 0.9) -> bool:
    """Check if two contents are near-duplicates"""
    ratio = SequenceMatcher(None, content1, content2).ratio()
    return ratio >= threshold

def deduplicate_with_fuzzy(memories: List[Memory], threshold: float = 0.9) -> List[Memory]:
    """Remove near-duplicate memories"""
    unique_memories = []

    for memory in memories:
        is_duplicate = False
        for existing in unique_memories:
            if is_near_duplicate(memory.content, existing.content, threshold):
                # Keep the longer version
                if len(existing.content) < len(memory.content):
                    unique_memories.remove(existing)
                    unique_memories.append(memory)
                is_duplicate = True
                break

        if not is_duplicate:
            unique_memories.append(memory)

    return unique_memories
```

**Pros**:
- Reduces storage
- Improves search relevance (no duplicate results)
- Clean memory database

**Cons**:
- Additional processing overhead
- May remove intentionally repeated memories

**Recommendation**: Implement exact deduplication for v1.0.0 as optional cleanup command.

---

## 5. Compression Comparison

| Technique | Size Reduction | CPU Overhead | Accuracy Impact | v1.0.0 Recommendation |
|-----------|---------------|--------------|-----------------|----------------------|
| **Gzip (Index)** | 82.5% | Low (~10%) | None | ✅ Already implemented |
| **Gzip (Content)** | 60-80% | Low (~10%) | None | ⚠️ Optional |
| **Summarization** | 70-90% | High (LLM) | Medium | ❌ Phase 2+ |
| **Embedding Quantization** | 50-75% | Medium | Low (1-3%) | ❌ Phase 2+ |
| **Exact Deduplication** | 5-20% | Very Low | None | ✅ Recommended |
| **Near-Deduplication** | 10-30% | Medium | Low | ⚠️ Optional |

---

## 6. Implementation Checklist for v1.0.0

### P0 (Required)
- [x] Gzip index compression (already in F5)
- [ ] Verify compression is working correctly

### P1 (Recommended)
- [ ] Exact deduplication utility command
- [ ] Memory size monitoring/logging

### P2 (Optional)
- [ ] Gzip compression for large Markdown files
- [ ] Near-deduplication for cleanup

### Phase 2+ (Future)
- [ ] LLM-based summarization
- [ ] Embedding quantization (if dense retrieval added)

---

## 7. References

1. F5_COMPRESSION.md - Existing gzip implementation
2. FAISS Documentation - https://faiss.ai/
3. Scikit-learn PCA - https://scikit-learn.org/stable/modules/decomposition.html

---

**Document History**:
| Date | Version | Change |
|------|---------|--------|
| 2026-03-23 | 1.0 | Initial research document |
