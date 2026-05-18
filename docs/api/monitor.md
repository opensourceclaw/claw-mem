# Monitor API

## PerformanceMonitor (v2.19.0+)

Latency histogram and cache hit-rate tracking.

```python
from claw_mem.monitor.performance import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.record_search(latency_ms=2.5)
monitor.record_cache_hit()
monitor.record_cache_miss()
stats = monitor.get_stats()
# {
#   "p50_latency_ms": 2.5,
#   "p95_latency_ms": 3.2,
#   "cache_hit_rate": 0.85,
#   "memory_mb": 15.3,
#   ...
# }
monitor.reset()
```

Access via `MemoryManager.get_performance_stats()`.
