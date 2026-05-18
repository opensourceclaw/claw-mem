# Cache API

## QueryCache (v2.19.0+)

LRU cache with TTL for search results.

```python
from claw_mem.cache.query_cache import QueryCache

cache = QueryCache(max_size=1000, ttl_seconds=300)
cached = cache.get("dark mode")          # Returns List[str] or None
cache.set("dark mode", ["id1", "id2"])   # Cache results
cache.clear()
print(cache.hit_rate)                    # Float 0.0-1.0
stats = cache.stats()
```

Integrated into MemoryManager.search() automatically.
