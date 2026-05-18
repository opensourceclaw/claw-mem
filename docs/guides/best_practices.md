# Best Practices

## Performance Optimization

1. **Enable Engram + Spreading**: The DecoupledRetriever pipeline provides sub-5ms search latency
2. **Use QueryCache**: Enabled by default, caches frequent queries
3. **Configure Decay Thresholds**: Tune per-edge half-life for your use case
4. **Monitor Performance**: Use `get_performance_stats()` to track latency

## Error Handling

```python
from claw_mem.errors import (
    StorageError, RetrievalError, CompressionError
)

try:
    results = mm.search(query, limit=10)
except RetrievalError:
    results = []  # Graceful degradation
```

## Memory Types

- **Episodic**: Use for conversation logs (auto-expire after 30 days)
- **Semantic**: Use for persistent facts (no expiration)
- **Procedural**: Use for skills and reusable workflows

## Compression Strategy

- Set `compression_trigger_access=5` for frequently-used patterns
- Non-blocking: compression runs on access, not background
- Engram auto-syncs compressed content for searchability
- Default enabled since v2.18.0

## Graph Memory Usage

- `enable_graph=True`: Full MultiGraphMemory + DualLayerMemory
- `enable_decay=False`: Disable edge decay if graph stability is preferred
- `enable_ground_truth=False`: Disable raw conversation storage for privacy
