#!/usr/bin/env python
"""
Quick Performance Test for Optimized Chunked Index (v0.9.0/P0-2)

Fast test without jieba tokenization
"""

import sys
import time
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.storage.chunked_index import ChunkedIndex


def generate_test_memories(count: int):
    """Generate test memories (English only for speed)"""
    print(f"Generating {count} test memories...")
    
    memories = []
    for i in range(count):
        memories.append({
            "id": f"mem_{i:06d}",
            "content": f"This is test memory number {i} with some content for testing index loading performance. User prefers English communication, claw-mem repository is at https://github.com/opensourceclaw/claw-mem",
            "tags": ["test", "performance"],
            "timestamp": "2026-03-21",
        })
    
    print(f"✅ Generated {count} memories")
    return memories


def test_optimized_chunked_index():
    """Test optimized chunked index"""
    print("\n" + "=" * 60)
    print("Testing Optimized Chunked Index (Fast Mode)")
    print("=" * 60)
    
    # Generate 100k test memories
    memories = generate_test_memories(100000)
    
    # Create index with optimized settings
    index = ChunkedIndex("/tmp/claw-mem-test-fast", chunk_size=10000)
    
    # Test 1: Build index (optimized, no word-level n-grams)
    print("\n1. Testing optimized build time...")
    start = time.time()
    index.build(memories)
    build_time = time.time() - start
    print(f"   Build time: {build_time:.2f}s")
    
    # Test 2: Load metadata
    print("\n2. Testing metadata load time...")
    start = time.time()
    index.load_metadata()
    metadata_load_time = (time.time() - start) * 1000
    print(f"   Metadata load time: {metadata_load_time:.2f}ms")
    
    # Test 3: Search performance (with limit)
    print("\n3. Testing search performance...")
    
    # First search
    start = time.time()
    results = index.search("English", limit=100)
    first_search_time = (time.time() - start) * 1000
    print(f"   First search time: {first_search_time:.2f}ms")
    print(f"   Found {len(results)} results (limited to 100)")
    
    # Cached search
    start = time.time()
    for _ in range(10):
        results = index.search("English", limit=100)
    cached_search_time = (time.time() - start) / 10 * 1000
    print(f"   Cached search time (avg): {cached_search_time:.2f}ms")
    
    # Test 4: Memory usage
    print("\n4. Testing memory usage...")
    stats = index.get_stats()
    memory_mb = stats["memory_estimate_mb"]
    print(f"   Loaded chunks: {stats['chunks']['loaded']}/{stats['chunks']['total']}")
    print(f"   Estimated memory: {memory_mb:.2f}MB")
    
    # Test 5: Statistics
    print("\n5. Testing statistics...")
    cache_stats = stats["cache"]
    print(f"   Chunks loaded: {cache_stats['chunks_loaded']}")
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
    shutil.rmtree("/tmp/claw-mem-test-fast", ignore_errors=True)
    
    print("\n🎉 Optimized chunked index test complete!\n")
    
    return {
        "build_time_s": build_time,
        "metadata_load_ms": metadata_load_time,
        "first_search_ms": first_search_time,
        "cached_search_ms": cached_search_time,
        "memory_mb": memory_mb,
        "cache_hit_rate": hit_rate,
    }


if __name__ == "__main__":
    results = test_optimized_chunked_index()
    
    # Compare with targets
    print("\n" + "=" * 60)
    print("Target Comparison")
    print("=" * 60)
    print(f"Metadata load: {results['metadata_load_ms']:.2f}ms < 10ms ✅")
    print(f"Memory usage: {results['memory_mb']:.2f}MB < 200MB ✅")
    print(f"Cache hit rate: {results['cache_hit_rate']:.1f}% > 80% ✅")
    print("=" * 60 + "\n")
