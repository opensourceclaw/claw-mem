# Retrieval Algorithms

## Search Pipeline

```
Query → Keyword Filter → BM25 Ranking → Entity Enhancement → Heuristic Scoring → Results
```

## Retrievers

### KeywordRetriever
- Simple substring match
- Fast, O(n)
- Good for exact matches

### BM25Retriever
- Okapi BM25 ranking
- Term frequency + inverse document frequency
- Good for relevance ranking

### HybridBM25Retriever
- Combines keyword + BM25
- Balanced precision/recall

### EntityEnhancedRetriever
- Named entity recognition
- Boosts results with matching entities
- Requires spaCy (optional)

### HeuristicRetriever
- Recency boost
- Importance scoring
- Context matching

### SmartRetriever
- Combines all retrievers
- Weighted scoring
- Best overall quality

## Performance

| Retriever | Latency | Quality |
|-----------|---------|---------|
| keyword | ~1ms | Basic |
| bm25 | ~3ms | Good |
| hybrid | ~4ms | Better |
| entity | ~8ms | Good (with entities) |
| heuristic | ~5ms | Very Good |
| enhanced_smart | ~6ms | Best |
