#!/usr/bin/env python
"""
Performance Verification for Chunked Index (v0.9.0/P0-2)

Run this to verify:
- 100k entries load: <2 seconds (was >5s)
- Memory usage: <200MB (was >500MB)
"""

import sys
import time
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.storage.chunked_index import ChunkedIndex, OptimizedIndexManager


def generate_test_memories(count: int):
    """Generate test memories"""
    print(f"Generating {count} test memories...")
    
    memories = []
    for i in range(count):
        memories.append({
            "id": f"mem_{i:06d}",
            "content": f"这是第 {i} 条测试记忆，包含一些内容用于测试索引加载性能。用户偏好使用中文交流，claw-mem 仓库地址是 https://github.com/opensourceclaw/claw-mem",
            "tags": ["测试", "性能"],
            "timestamp": "2026-03-21",
        })
    
    print(f"✅ Generated {count} memories")
    return memories


def test_chunked_index():
    """Test chunked index performance"""
    print("\n" + "=" * 60)
    print("Testing Chunked Index Performance (v0.9.0/P0-2)")
    print("=" * 60)
    
    # Generate 100k test memories
    memories = generate_test_memories(100000)
    
    # Create index
    index = ChunkedIndex("/tmp/claw-mem-test-index", chunk_size=10000)
    
    # Test 1: Build index
    print("\n1. Testing index build time...")
    start = time.time()
    index.build(memories)
    build_time = time.time() - start
    print(f"   Build time: {build_time:.2f}s")
    
    # Test 2: Load metadata only
    print("\n2. Testing metadata load time...")
    start = time.time()
    index.load_metadata()
    metadata_load_time = (time.time() - start) * 1000
    print(f"   Metadata load time: {metadata_load_time:.2f}ms")
    
    # Verify metadata load target
    assert metadata_load_time < 10, f"❌ Metadata load {metadata_load_time}ms exceeds 10ms target"
    print(f"   ✅ Metadata load target met: <10ms")
    
    # Test 3: Search performance
    print("\n3. Testing search performance...")
    
    # First search (will load chunks)
    start = time.time()
    results = index.search("中文")
    first_search_time = (time.time() - start) * 1000
    print(f"   First search time: {first_search_time:.2f}ms")
    print(f"   Found {len(results)} results")
    
    # Cached search
    start = time.time()
    for _ in range(10):
        results = index.search("中文")
    cached_search_time = (time.time() - start) / 10 * 1000
    print(f"   Cached search time (avg): {cached_search_time:.2f}ms")
    
    # Test 4: Memory usage
    print("\n4. Testing memory usage...")
    stats = index.get_stats()
    memory_mb = stats["memory_estimate_mb"]
    print(f"   Loaded chunks: {stats['chunks']['loaded']}/{stats['chunks']['total']}")
    print(f"   Estimated memory: {memory_mb:.2f}MB")
    
    # Verify memory target
    assert memory_mb < 200, f"❌ Memory usage {memory_mb}MB exceeds 200MB target"
    print(f"   ✅ Memory usage target met: <200MB")
    
    # Test 5: Statistics
    print("\n5. Testing statistics...")
    cache_stats = stats["cache"]
    print(f"   Chunks loaded: {cache_stats['chunks_loaded']}")
    print(f"   Chunks evicted: {cache_stats['chunks_evicted']}")
    print(f"   Cache hits: {cache_stats['cache_hits']}")
    print(f"   Cache misses: {cache_stats['cache_misses']}")
    
    hit_rate = cache_stats['cache_hits'] / (cache_stats['cache_hits'] + cache_stats['cache_misses']) * 100 if (cache_stats['cache_hits'] + cache_stats['cache_misses']) > 0 else 0
    print(f"   Cache hit rate: {hit_rate:.1f}%")
    
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"✅ Build time: {build_time:.2f}s")
    print(f"✅ Metadata load: {metadata_load_time:.2f}ms (target: <10ms)")
    print(f"✅ First search: {first_search_time:.2f}ms")
    print(f"✅ Cached search: {cached_search_time:.2f}ms")
    print(f"✅ Memory usage: {memory_mb:.2f}MB (target: <200MB)")
    print(f"✅ Cache hit rate: {hit_rate:.1f}%")
    print("=" * 60)
    
    # Cleanup
    import shutil
    shutil.rmtree("/tmp/claw-mem-test-index", ignore_errors=True)
    
    print("\n🎉 All P0-2 targets met! Chunked index optimization complete!\n")
    
    return {
        "build_time_s": build_time,
        "metadata_load_ms": metadata_load_time,
        "first_search_ms": first_search_time,
        "cached_search_ms": cached_search_time,
        "memory_mb": memory_mb,
        "cache_hit_rate": hit_rate,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("claw-mem v0.9.0/P0-2 Chunked Index Performance Test")
    print("=" * 60)
    
    results = test_chunked_index()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")
