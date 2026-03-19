#!/usr/bin/env python3
"""
Test script for claw-mem v0.7.0 F1: Index Persistence

Tests:
1. Index building and saving
2. Index loading from disk
3. Incremental updates
4. Performance comparison (build vs load)
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claw_mem.storage.index import InMemoryIndex


def test_index_persistence():
    """Test index persistence functionality"""
    print("=" * 60)
    print("claw-mem v0.7.0 F1: Index Persistence Test")
    print("=" * 60)
    
    # Sample memories for testing
    test_memories = [
        {"id": "1", "content": "用户询问上海明天的天气"},
        {"id": "2", "content": "用户偏好简洁的回答，不喜欢冗长解释"},
        {"id": "3", "content": "Python 是一种编程语言"},
        {"id": "4", "content": "Python 可以用于数据分析"},
        {"id": "5", "content": "用户喜欢早上 9 点开始工作"},
        {"id": "6", "content": "上次查询天气时忘记考虑时区，导致时间错误"},
        {"id": "7", "content": "帮我查一下上海明天的天气，我准备去出差"},
        {"id": "8", "content": "claw-mem v0.7.0 支持索引持久化"},
        {"id": "9", "content": "索引持久化可以显著减少启动时间"},
        {"id": "10", "content": "懒加载机制让首次搜索时才加载索引"},
    ]
    
    print(f"\n📝 Test memories: {len(test_memories)} records\n")
    
    # Test 1: Build index and save
    print("Test 1: Building index from scratch...")
    start = time.time()
    index1 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index1.build(test_memories, save_index=True)
    build_time = time.time() - start
    print(f"⏱️  Build time: {build_time:.3f}s\n")
    
    # Test 2: Load index from disk
    print("Test 2: Loading index from disk...")
    start = time.time()
    index2 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    loaded = index2.load_index()
    load_time = time.time() - start
    print(f"⏱️  Load time: {load_time:.3f}s")
    print(f"✅ Load success: {loaded}\n")
    
    # Test 3: Verify loaded index
    print("Test 3: Verifying loaded index...")
    assert index2.built, "Index should be built after loading"
    assert len(index2.memory_ids) == len(test_memories), f"Expected {len(test_memories)} memories, got {len(index2.memory_ids)}"
    assert len(index2.ngram_index) > 0, "N-gram index should not be empty"
    print(f"✅ Memory count: {len(index2.memory_ids)}")
    print(f"✅ N-gram count: {len(index2.ngram_index)}\n")
    
    # Test 4: Search functionality
    print("Test 4: Testing search functionality...")
    query = "Python"
    ngram_results = index2.ngram_search(query, limit=5)
    print(f"🔍 N-gram search for '{query}': {ngram_results}")
    
    if index2.bm25_index is not None:
        bm25_results = index2.bm25_search(query, limit=5)
        print(f"🔍 BM25 search for '{query}': {bm25_results}")
    
    query = "天气"
    ngram_results = index2.ngram_search(query, limit=5)
    print(f"🔍 N-gram search for '{query}': {ngram_results}\n")
    
    # Test 5: Incremental update
    print("Test 5: Testing incremental update...")
    new_memory = {"id": "11", "content": "新增的记忆条目用于测试增量更新"}
    start = time.time()
    index2.add_memory(new_memory["content"], new_memory["id"], save_async=False)
    update_time = time.time() - start
    print(f"⏱️  Incremental update time: {update_time:.3f}s")
    print(f"✅ Memory count after update: {len(index2.memory_ids)}\n")
    
    # Test 6: Performance comparison
    print("Test 6: Performance Summary")
    print("-" * 40)
    print(f"Build from scratch: {build_time:.3f}s")
    print(f"Load from disk:     {load_time:.3f}s")
    print(f"Incremental update: {update_time:.3f}s")
    print(f"Speedup:            {build_time/load_time:.1f}x faster with persistence")
    print("-" * 40)
    
    # Test 7: Get stats
    print("\nTest 7: Index Statistics")
    stats = index2.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    
    return {
        "build_time": build_time,
        "load_time": load_time,
        "update_time": update_time,
        "speedup": build_time / load_time if load_time > 0 else float('inf'),
    }


if __name__ == "__main__":
    results = test_index_persistence()
    
    # Print performance summary
    print("\n📊 Performance Summary:")
    print(f"  - Build time: {results['build_time']:.3f}s")
    print(f"  - Load time:  {results['load_time']:.3f}s")
    print(f"  - Speedup:    {results['speedup']:.1f}x")
    
    if results['load_time'] < 0.5:
        print("  ✅ Load time meets target (<0.5s)")
    else:
        print("  ⚠️  Load time exceeds target (<0.5s)")
    
    if results['speedup'] > 3:
        print("  ✅ Speedup meets target (>3x)")
    else:
        print("  ⚠️  Speedup below target (>3x)")
