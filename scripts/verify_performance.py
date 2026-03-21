#!/usr/bin/env python
"""
Simple Performance Verification for Optimized Retriever (v0.9.0)

Run this to verify:
- Query latency <50ms for short text
- Query latency <200ms for long text  
- Cache hit rate >80%
"""

import sys
import time
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.retrieval.optimized import OptimizedRetriever, LRUCache, TTLCache


class MockStorage:
    """Mock storage for testing"""
    def __init__(self, memories):
        self.memories = memories
    
    def get_all(self):
        return self.memories
    
    def get_recent(self, limit):
        return self.memories[:limit]


def test_lru_cache():
    """Test LRU Cache"""
    print("\n=== Testing LRU Cache ===")
    
    cache = LRUCache(max_size=3)
    cache.put("key1", [{"content": "value1"}])
    cache.put("key2", [{"content": "value2"}])
    cache.put("key3", [{"content": "value3"}])
    
    assert cache.get("key1") == [{"content": "value1"}]
    assert cache.get("key2") == [{"content": "value2"}]
    assert cache.get("key3") == [{"content": "value3"}]
    assert cache.size() == 3
    
    # Test eviction
    cache.put("key4", [{"content": "value4"}])
    assert cache.get("key1") is None  # Evicted
    assert cache.size() == 3
    
    print("✅ LRU Cache tests passed")


def test_ttl_cache():
    """Test TTL Cache"""
    print("\n=== Testing TTL Cache ===")
    
    cache = TTLCache(max_size=100, ttl_seconds=1)
    cache.put("key1", [{"content": "value1"}])
    
    assert cache.get("key1") == [{"content": "value1"}]
    
    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("key1") is None
    
    print("✅ TTL Cache tests passed")


def test_performance():
    """Test performance with mock data"""
    print("\n=== Testing Performance ===")
    
    # Create mock storages with 300 memories
    memories = [
        {"content": "用户偏好使用中文交流", "tags": ["偏好", "语言"], "timestamp": "2026-03-21"},
        {"content": "claw-mem 仓库地址是 https://github.com/opensourceclaw/claw-mem", "tags": ["项目"], "timestamp": "2026-03-20"},
        {"content": "Peter Cheng 是项目负责人", "tags": ["人员"], "timestamp": "2026-03-19"},
    ] * 100
    
    storages = {
        "episodic": MockStorage(memories),
        "semantic": MockStorage(memories),
        "procedural": MockStorage(memories),
    }
    
    retriever = OptimizedRetriever(l1_size=1000, l2_size=5000)
    
    # Test 1: First query (cache miss)
    print("\n1. Testing first query (cache miss)...")
    start = time.time()
    result = retriever.search("中文", **storages)
    first_query_time = (time.time() - start) * 1000
    print(f"   First query time: {first_query_time:.2f}ms")
    
    # Test 2: Repeated queries (cache hit)
    print("\n2. Testing repeated queries (cache hit)...")
    times = []
    for _ in range(100):
        start = time.time()
        result = retriever.search("中文", **storages)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[94]  # 95th percentile
    
    print(f"   Average query time: {avg_time:.2f}ms")
    print(f"   P95 query time: {p95_time:.2f}ms")
    
    # Verify performance targets
    assert avg_time < 50, f"❌ Average time {avg_time}ms exceeds 50ms target"
    assert p95_time < 100, f"❌ P95 time {p95_time}ms exceeds 100ms target"
    print(f"   ✅ Performance target met: <50ms average, <100ms P95")
    
    # Test 3: Cache hit rate
    print("\n3. Testing cache hit rate...")
    stats = retriever.get_stats()
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit rate: {stats['hit_rate_percent']}%")
    
    assert stats['hit_rate_percent'] > 80, f"❌ Hit rate {stats['hit_rate_percent']}% below 80% target"
    print(f"   ✅ Cache hit rate target met: >80%")
    
    # Test 4: Memory usage
    print("\n4. Testing memory usage...")
    l1_mem = stats['l1_cache']['memory_estimate_mb']
    l2_mem = stats['l2_cache']['memory_estimate_mb']
    total_mem = l1_mem + l2_mem
    print(f"   L1 cache memory: {l1_mem:.2f}MB")
    print(f"   L2 cache memory: {l2_mem:.2f}MB")
    print(f"   Total memory: {total_mem:.2f}MB")
    
    assert total_mem < 100, f"❌ Memory usage {total_mem}MB exceeds 100MB target"
    print(f"   ✅ Memory usage target met: <100MB")
    
    # Test 5: Long text query
    print("\n5. Testing long text query...")
    long_query = "用户偏好使用中文交流，claw-mem 仓库地址是 https://github.com/opensourceclaw/claw-mem，Peter Cheng 是项目负责人" * 10
    
    start = time.time()
    result = retriever.search(long_query, **storages)
    long_query_time = (time.time() - start) * 1000
    
    print(f"   Long text query time: {long_query_time:.2f}ms")
    
    assert long_query_time < 200, f"❌ Long query time {long_query_time}ms exceeds 200ms target"
    print(f"   ✅ Long text query target met: <200ms")
    
    print("\n=== All Performance Tests Passed! ===\n")
    
    return {
        "first_query_ms": first_query_time,
        "avg_query_ms": avg_time,
        "p95_query_ms": p95_time,
        "hit_rate_percent": stats['hit_rate_percent'],
        "memory_mb": total_mem,
        "long_query_ms": long_query_time,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("claw-mem v0.9.0 Performance Verification")
    print("=" * 60)
    
    # Run tests
    test_lru_cache()
    test_ttl_cache()
    results = test_performance()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"✅ Short text query: {results['avg_query_ms']:.2f}ms (target: <50ms)")
    print(f"✅ P95 latency: {results['p95_query_ms']:.2f}ms (target: <100ms)")
    print(f"✅ Cache hit rate: {results['hit_rate_percent']:.1f}% (target: >80%)")
    print(f"✅ Memory usage: {results['memory_mb']:.2f}MB (target: <100MB)")
    print(f"✅ Long text query: {results['long_query_ms']:.2f}ms (target: <200ms)")
    print("=" * 60)
    print("🎉 All targets met! P0-1 retrieval optimization complete!")
    print("=" * 60 + "\n")
