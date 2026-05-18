# MemoryManager API

**Version**: v2.20.0

## Constructor

```python
MemoryManager(
    workspace: str = None,
    enable_graph: bool = True,
    enable_engram: bool = True,
    enable_spreading: bool = True,
    enable_decay: bool = True,
    enable_ground_truth: bool = True,
    enable_compression_spectrum: bool = True,
    enable_query_cache: bool = True,
    decay_config: DecayConfig = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|:-------:|-------------|
| `workspace` | str/None | None | Workspace path, auto-detected if None |
| `enable_graph` | bool | True | Enable MultiGraphMemory + DualLayerMemory |
| `enable_engram` | bool | True | Enable EngramIndex for O(1) lookup |
| `enable_spreading` | bool | True | Enable SpreadingActivation |
| `enable_decay` | bool | True | Enable edge-level decay |
| `enable_ground_truth` | bool | True | Enable GroundTruthStore |
| `enable_compression_spectrum` | bool | True | Enable CompressionSpectrum |
| `enable_query_cache` | bool | True | Enable query result cache |

## Core Methods

### store()

```python
def store(content: str, memory_type: str = "episodic",
          tags: List[str] = None, metadata: Dict = None,
          update_index: bool = True) -> bool
```

Store a memory entry.

**Exceptions**: `ValueError` if content empty or type invalid.

### search()

```python
def search(query: str, memory_type: str = None,
           metadata: Dict = None, limit: int = 10,
           mode: str = None, include_critical: bool = True) -> List[Dict]
```

Search memories. Pipeline: QueryCache → DecoupledRetriever (Engram+Spreading) → Hybrid BM25.

**Exceptions**: `ValueError` if query empty, `QueryTooLongError` if >2000 chars.

### get()

```python
def get(memory_id: str) -> Optional[Dict]
```

Retrieve a specific memory by ID.

### delete()

```python
def delete(memory_id: str) -> bool
```

Delete a memory.

## Graph Methods (v2.14.0+)

- `get_graph_stats() -> dict`
- `get_node_graph(memory_id: str) -> dict`
- `persist_graph() -> bool`
- `get_decay_stats() -> dict`
- `force_decay_cycle() -> int`
- `search_ground_truth(session_id, keyword, limit) -> List`
- `list_sessions() -> List`

## Engram/Spreading Methods (v2.15.0+)

- `get_engram_stats() -> dict`
- `rebuild_engram() -> int`
- `get_spreading_stats() -> dict`
- `get_compression_stats() -> dict`
- `manual_compress(memory_id: str) -> Optional[Dict]`

## Performance Methods (v2.19.0+)

- `get_performance_stats() -> dict`

## Error Types

- `StorageError` / `MemoryNotFoundError` / `StorageFullError` / `StorageCorruptedError`
- `RetrievalError` / `IndexNotReadyError` / `QueryTooLongError`
- `CompressionError` / `CompressionDisabledError`
- `InvalidThresholdError`
