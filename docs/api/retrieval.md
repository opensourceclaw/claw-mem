# Retrieval API

## EngramIndex (v2.15.0+)

O(1) N-Gram hash inverted index.

```python
from claw_mem.retrieval.engram import EngramIndex

engram = EngramIndex(ngram_size=3)
engram.index("mem_1", "User prefers dark mode")
results = engram.lookup("dark mode", top_k=10)
engram.index_batch([("id_1", "text"), ("id_2", "text")])
engram.remove("mem_1")
stats = engram.get_stats()
```

## SpreadingActivation (v2.15.0+)

Graph-based activation spreading.

```python
from claw_mem.retrieval.spreading import SpreadingActivation

spreader = SpreadingActivation(graph)
spreader.configure(max_depth=2, decay_factor=0.5)
activations = spreader.activate({"node_1": 1.0}, intent="general")
```

## DecoupledRetriever (v2.15.0+)

Unified pipeline: Query → Engram → Spreading → Ranking.

```python
from claw_mem.retrieval.decoupled import DecoupledRetriever

retriever = DecoupledRetriever(engram, spreader, graph)
results = retriever.search("dark mode", top_k=5, intent="semantic")
```

## BM25 / Hybrid Retriever

```python
bm25 = BM25Retriever(k1=1.5, b=0.75)
results = bm25.search(query, memories)

hybrid = HybridBM25Retriever(bm25_weight=0.7, keyword_weight=0.3)
results = hybrid.search(query, memories)
```
