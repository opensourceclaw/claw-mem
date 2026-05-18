# Getting Started

## Installation

```bash
pip install claw-mem
```

## Quick Start

```python
from claw_mem import MemoryManager

# Initialize with all features
mm = MemoryManager(
    enable_graph=True,        # Graph structure memory
    enable_engram=True,       # O(1) n-gram index
    enable_spreading=True,    # Spreading activation
    enable_decay=True,        # Edge-level decay
    enable_compression_spectrum=True,  # Tiered compression
)

# Store memories
mm.store("User prefers dark mode", memory_type="semantic")
mm.store("Dark mode reduces eye strain", memory_type="semantic")

# Search (uses Engram + Spreading pipeline)
results = mm.search("dark mode", limit=5)
for r in results:
    print(f"{r['id']}: {r['score']:.3f}")

# Get statistics
stats = mm.get_stats()
perf = mm.get_performance_stats()
```

## Core Concepts

- **Episodic Memory**: Conversation history (30-day TTL)
- **Semantic Memory**: Extracted facts (permanent)
- **Procedural Memory**: Skills and workflows
- **Graph Memory** (v2.14.0+): Four-orthogonal subgraph index
- **Engram Index** (v2.15.0+): O(1) n-gram hash lookup
- **Compression Spectrum** (v2.18.0+): Episodes→Skills→Rules→Principles

## Error Handling

```python
from claw_mem.errors import StorageError, RetrievalError

try:
    mm.store("", memory_type="episodic")  # Empty content
except ValueError as e:
    print(f"Validation error: {e}")

try:
    mm.search("x" * 3000)  # Query too long
except RetrievalError as e:
    print(f"Retrieval error: {e}")
```
