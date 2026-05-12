# claw-mem v2.2.0 - Concept-Mediated Graph

**Release Date**: 2026-04-23

## Highlights

This release adds **Concept-Mediated Graph**, enabling intelligent knowledge organization through:

- **Four Node Types**: Episode, Fact, Reflection, Concept
- **Five Edge Types**: NEXT, DERIVED_FROM, SYNTHESIZED_FROM, RELATED_TO, HAS_CONCEPT
- **Hybrid Retrieval**: Semantic Search + PPR (Personalized PageRank)

## New Features

### Concept-Mediated Graph

```python
from claw_mem import ConceptMediatedGraph, LLMExtractor

# Create graph with LLM extractor
graph = ConceptMediatedGraph(
    embedder=my_embedder,
    extractor=LLMExtractor(llm_client=my_llm)
)

# Add conversation
episode_ids = graph.add_conversation([
    {"speaker": "user", "content": "I decided to use Python for development"},
    {"speaker": "agent", "content": "I recommend using FastAPI framework"}
])

# Retrieve relevant memories
results = graph.retrieve("development framework", k=10, alpha=0.5)
```

### LLM Extractors

- `LLMExtractor` - LLM-powered fact and concept extraction
- `KeywordExtractor` - Lightweight keyword extraction
- `DummyExtractor` - Empty extractor for testing

### MemoryManager Integration

```python
from claw_mem import MemoryManager

# Enable graph support
manager = MemoryManager(enable_gating=True, enable_graph=True)

# Graph is automatically created
if manager.graph:
    # Use graph features
    manager.graph.add_episode("Important decision", speaker="user")
```

## Stats

- **Tests**: 86 (all passing)
- **Coverage**: concept_graph.py 83%
- **Performance**: Add < 100ms, Retrieve < 50ms
- **Code**: 17 files changed, 2854 insertions(+)

## References

- Based on **GAAMA paper**: "Graph-Augmented Associative Memory"
- Builds on v2.1.0 Write-Time Gating foundation

## Installation

```bash
# From GitHub
pip install git+https://github.com/opensourceclaw/claw-mem.git@v2.2.0

# Or editable install
git clone https://github.com/opensourceclaw/claw-mem.git
cd claw-mem
git checkout v2.2.0
pip install -e .
```

## What's Next

- v2.3.0: Evolving Memory (ACE paper)
- v2.4.0: Bidirectional Memory Transfer (MIA paper)

---

**Full Changelog**: https://github.com/opensourceclaw/claw-mem/compare/v2.1.0...v2.2.0
