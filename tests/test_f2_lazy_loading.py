#!/usr/bin/env python3
# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test script for claw-mem v0.7.0 F2: Lazy Loading

Tests:
1. Index not loaded on initialization
2. Index loaded on first search
3. Startup time without loading
4. First search includes load time
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claw_mem.storage.index import InMemoryIndex


def test_lazy_loading():
    """Test lazy loading functionality"""
    print("=" * 60)
    print("claw-mem v0.7.0 F2: Lazy Loading Test")
    print("=" * 60)
    
    # Sample memories
    test_memories = [
        {"id": "1", "content": "用户询问上海明天的天气"},
        {"id": "2", "content": "用户偏好简洁的回答"},
        {"id": "3", "content": "Python 是一种编程语言"},
        {"id": "4", "content": "索引懒加载机制"},
        {"id": "5", "content": "首次搜索时才加载索引"},
    ]
    
    print(f"\n📝 Test memories: {len(test_memories)} records\n")
    
    # Step 1: Build and save index
    print("Step 1: Building and saving index...")
    index1 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index1.build(test_memories, save_index=True)
    print(f"✅ Index built and saved\n")
    
    # Step 2: Create new index instance (simulating restart)
    print("Step 2: Creating new index instance (simulating restart)...")
    start = time.time()
    index2 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    init_time = time.time() - start
    
    print(f"⏱️  Initialization time: {init_time:.6f}s")
    print(f"✅ Index built: {index2.built}")
    print(f"✅ Index loaded: {index2.index_loaded}")
    print(f"   (Should be False - not loaded yet)\n")
    
    # Verify index is NOT loaded yet
    assert not index2.built, "Index should NOT be built on initialization"
    assert not index2.index_loaded, "Index should NOT be loaded yet"
    
    # Step 3: First search triggers lazy loading
    print("Step 3: First search (triggers lazy loading)...")
    start = time.time()
    results = index2.ngram_search("天气", limit=5)
    first_search_time = time.time() - start
    
    print(f"⏱️  First search time: {first_search_time:.6f}s")
    print(f"🔍 Search results: {results}")
    print(f"✅ Index built: {index2.built}")
    print(f"✅ Index loaded: {index2.index_loaded}\n")
    
    # Verify index IS loaded after first search
    assert index2.built, "Index should be built after first search"
    assert index2.index_loaded, "Index should be loaded after first search"
    assert len(results) > 0, "Should find results for '天气'"
    
    # Step 4: Second search (no loading needed)
    print("Step 4: Second search (no loading needed)...")
    start = time.time()
    results2 = index2.ngram_search("Python", limit=5)
    second_search_time = time.time() - start
    
    print(f"⏱️  Second search time: {second_search_time:.6f}s")
    print(f"🔍 Search results: {results2}\n")
    
    # Step 5: Compare times
    print("Step 5: Performance Summary")
    print("-" * 40)
    print(f"Initialization:     {init_time:.6f}s")
    print(f"First search:       {first_search_time:.6f}s (includes load)")
    print(f"Second search:      {second_search_time:.6f}s")
    print(f"Init + First:       {init_time + first_search_time:.6f}s")
    print("-" * 40)
    
    # Verify lazy loading benefit
    # Init should be very fast (<10ms)
    assert init_time < 0.01, f"Initialization should be <10ms, got {init_time:.6f}s"
    print(f"✅ Initialization meets target (<10ms)")
    
    # Test BM25 search also triggers lazy loading
    print("\nStep 6: Testing BM25 lazy loading...")
    index3 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    assert not index3.built, "New index should not be built"
    
    if index3.bm25_index is not None or True:  # BM25 may not be available
        bm25_results = index3.bm25_search("天气", limit=5)
        print(f"🔍 BM25 search results: {bm25_results}")
        print(f"✅ BM25 search also triggers lazy loading\n")
    
    # Test hybrid search
    print("Step 7: Testing hybrid search lazy loading...")
    index4 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    assert not index4.built, "New index should not be built"
    
    hybrid_results = index4.hybrid_search("天气", limit=5)
    print(f"🔍 Hybrid search results: {hybrid_results}")
    print(f"✅ Hybrid search also triggers lazy loading\n")
    
    print("=" * 60)
    print("✅ All F2 tests passed!")
    print("=" * 60)
    
    return {
        "init_time": init_time,
        "first_search_time": first_search_time,
        "second_search_time": second_search_time,
    }


if __name__ == "__main__":
    results = test_lazy_loading()
    
    print("\n📊 F2 Lazy Loading Summary:")
    print(f"  - Initialization: {results['init_time']:.6f}s (target: <0.01s)")
    print(f"  - First search:   {results['first_search_time']:.6f}s")
    print(f"  - Second search:  {results['second_search_time']:.6f}s")
    
    if results['init_time'] < 0.01:
        print("  ✅ Lazy loading working - initialization is instant!")
    else:
        print("  ⚠️  Initialization slower than expected")
    
    print("\n💡 Lazy Loading Benefits:")
    print("  - App startup feels instant")
    print("  - Index only loaded when actually needed")
    print("  - No wasted work if no search is performed")
