#!/usr/bin/env python3
"""
claw-mem Performance Benchmark Script
测试优化前后的性能差异
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from claw_mem import MemoryManager
from claw_mem.retrieval.three_tier import ThreeTierRetriever

def benchmark_search():
    """Benchmark search performance"""
    print("=" * 70)
    print("🚀 claw-mem Performance Benchmark")
    print("=" * 70)
    print("")
    
    workspace = '/Users/liantian/.openclaw/workspace'
    mem = MemoryManager(workspace=workspace)
    
    # Test 1: First search (cold start)
    print("📊 Test 1: First Search (Cold Start)")
    print("-" * 70)
    start = time.time()
    results = mem.search('memory system architecture')
    cold_latency = (time.time() - start) * 1000
    print(f"✅ First search: {cold_latency:.2f}ms")
    print(f"✅ Results: {len(results)} memories")
    print("")
    
    # Test 2: Repeated searches (warm cache)
    print("📊 Test 2: Repeated Searches (Warm Cache)")
    print("-" * 70)
    start = time.time()
    for i in range(10):
        results = mem.search('memory system architecture')
    avg_latency = (time.time() - start) * 1000 / 10
    print(f"✅ Average (10x): {avg_latency:.2f}ms")
    print(f"✅ Total time: {(time.time() - start) * 1000:.2f}ms")
    print("")
    
    # Test 3: Three-tier retrieval
    print("📊 Test 3: Three-Tier Retrieval")
    print("-" * 70)
    retriever = ThreeTierRetriever(workspace=workspace)
    
    start = time.time()
    l1 = retriever.search('memory system architecture', layers=['l1'])
    l2 = retriever.search('memory system architecture', layers=['l2'])
    l3 = retriever.search('memory system architecture', layers=['l3'])
    tier_latency = (time.time() - start) * 1000
    print(f"✅ L1: {len(l1)} results")
    print(f"✅ L2: {len(l2)} results")
    print(f"✅ L3: {len(l3)} results")
    print(f"✅ Three-tier latency: {tier_latency:.2f}ms")
    print("")
    
    # Summary
    print("=" * 70)
    print("📊 Performance Summary")
    print("=" * 70)
    print(f"✅ Cold Start: {cold_latency:.2f}ms (Target: <500ms)")
    print(f"✅ Warm Cache: {avg_latency:.2f}ms (Target: <100ms)")
    print(f"✅ Three-Tier: {tier_latency:.2f}ms (Target: <200ms)")
    print("=" * 70)
    
    # Verdict
    print("")
    if cold_latency < 500 and avg_latency < 100:
        print("🎉 Performance targets MET!")
    else:
        print("⚠️  Performance targets NOT met - optimization needed")
        if cold_latency >= 500:
            print(f"   - Cold start too slow ({cold_latency:.2f}ms >= 500ms)")
        if avg_latency >= 100:
            print(f"   - Warm cache too slow ({avg_latency:.2f}ms >= 100ms)")
    print("")

if __name__ == '__main__':
    benchmark_search()
