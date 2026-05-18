# Migration Guide: v2.x to v3.0.0

## Breaking Changes

None yet — v3.0.0 is in planning. All v2.x APIs remain backward compatible.

## Configuration Parameter Mapping

| v2.13.x Parameter | v2.20.0 Equivalent | Notes |
|-------------------|-------------------|-------|
| `enable_graph` | Same | Now creates MultiGraphMemory + DualLayerMemory |
| `enable_compression` | `enable_compression_spectrum` | New compression is in spectrum module; existing MemoryCompressorV2 unchanged |
| (new) | `enable_engram` | Enabled by default since v2.15.0 |
| (new) | `enable_spreading` | Enabled by default since v2.15.0 |
| (new) | `enable_decay` | Enabled by default since v2.14.0 |
| (new) | `enable_ground_truth` | Enabled by default since v2.14.0 |
| (new) | `compression_trigger_*` | Configurable since v2.18.0 |

## Migration Steps

1. Update to latest v2.x: `pip install claw-mem --upgrade`
2. Verify compatibility: `python -c "from claw_mem import MemoryManager; mm = MemoryManager()"`
3. New features are enabled by default; disable if needed:
   ```python
   mm = MemoryManager(
       enable_graph=False,
       enable_engram=False,
   )
   ```

## Compatibility Guarantees

- All `store()` / `search()` / `get()` / `delete()` APIs unchanged
- Existing `InMemoryIndex` and `BM25Retriever` preserved as fallback
- `MemoryDecay` class deprecated but still functional (delegates to DecayController)
- `FriendlyError` based exceptions unchanged
