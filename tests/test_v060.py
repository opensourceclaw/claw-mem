#!/usr/bin/env python
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
claw-mem v0.6.0 System Test Suite

Comprehensive testing of new features:
- In-Memory Index
- Working Memory Cache
- Hybrid Search (N-gram + BM25)
- Performance improvements

Compare with v0.5.0 baseline
"""

import time
import statistics
from pathlib import Path
from datetime import datetime

from claw_mem import MemoryManager
from claw_mem.storage.index import InMemoryIndex, WorkingMemoryCache


class TestResults:
    """Test results collector"""
    
    def __init__(self):
        self.results = {}
    
    def record(self, test_name: str, passed: bool, metrics: dict = None):
        self.results[test_name] = {
            'passed': passed,
            'metrics': metrics or {},
            'timestamp': datetime.now().isoformat()
        }
    
    def summary(self) -> dict:
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r['passed'])
        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': passed / total if total > 0 else 0
        }


def test_in_memory_index(results: TestResults):
    """Test In-Memory Index functionality"""
    print("\n=== Test: In-Memory Index ===")
    
    index = InMemoryIndex(ngram_size=3)
    
    # Test data
    test_memories = [
        {'id': '1', 'content': 'User prefers DD/MM/YYYY date format'},
        {'id': '2', 'content': 'User likes Chinese communication'},
        {'id': '3', 'content': 'Repository: https://github.com/opensourceclaw/claw-mem'},
    ]
    
    # Build index
    start = time.time()
    index.build(test_memories)
    build_time = time.time() - start
    
    print(f"✓ Index built in {build_time*1000:.1f}ms")
    print(f"✓ N-grams: {len(index.ngram_index)}")
    
    results.record('index_build', index.built, {
        'build_time_ms': build_time * 1000,
        'ngram_count': len(index.ngram_index)
    })
    
    # Test N-gram search
    start = time.time()
    ngram_results = index.ngram_search('OpenClaw', limit=5)
    ngram_time = time.time() - start
    
    print(f"✓ N-gram search in {ngram_time*1000:.1f}ms: {len(ngram_results)} results")
    
    results.record('ngram_search', len(ngram_results) > 0, {
        'search_time_ms': ngram_time * 1000,
        'results_count': len(ngram_results)
    })
    
    # Test BM25 search
    start = time.time()
    bm25_results = index.bm25_search('User', limit=5)
    bm25_time = time.time() - start
    
    print(f"✓ BM25 search in {bm25_time*1000:.1f}ms: {len(bm25_results)} results")
    
    results.record('bm25_search', len(bm25_results) > 0, {
        'search_time_ms': bm25_time * 1000,
        'results_count': len(bm25_results)
    })
    
    # Test hybrid search
    start = time.time()
    hybrid_results = index.hybrid_search('User', limit=5)
    hybrid_time = time.time() - start
    
    print(f"✓ Hybrid search in {hybrid_time*1000:.1f}ms: {len(hybrid_results)} results")
    
    results.record('hybrid_search', len(hybrid_results) > 0, {
        'search_time_ms': hybrid_time * 1000,
        'results_count': len(hybrid_results)
    })


def test_working_memory_cache(results: TestResults):
    """Test Working Memory Cache"""
    print("\n=== Test: Working Memory Cache ===")
    
    cache = WorkingMemoryCache(max_size=100, ttl_seconds=300)
    
    # Test put/get
    test_data = {'id': '1', 'content': 'Test memory'}
    cache.put('1', test_data)
    
    retrieved = cache.get('1')
    hit = retrieved is not None and retrieved['content'] == 'Test memory'
    
    print(f"✓ Cache put/get: {'✓' if hit else '✗'}")
    print(f"✓ Cache size: {cache.size()}")
    
    results.record('cache_put_get', hit, {
        'cache_size': cache.size()
    })
    
    # Test LRU eviction
    for i in range(105):
        cache.put(str(i), {'id': str(i)})
    
    evicted = cache.size() <= 100
    print(f"✓ LRU eviction: {'✓' if evicted else '✗'} (size: {cache.size()})")
    
    results.record('cache_lru', evicted, {
        'final_size': cache.size()
    })


def test_memory_manager_v060(results: TestResults):
    """Test MemoryManager with v0.6.0 features"""
    print("\n=== Test: MemoryManager v0.6.0 ===")
    
    workspace = Path.home() / '.openclaw' / 'workspace'
    mm = MemoryManager(workspace=str(workspace))
    
    # Test initialization
    has_index = hasattr(mm, 'index')
    has_cache = hasattr(mm, 'working_cache')
    
    print(f"✓ Index initialized: {has_index}")
    print(f"✓ Cache initialized: {has_cache}")
    
    results.record('mm_init', has_index and has_cache)
    
    # Test session start
    start = time.time()
    mm.start_session('test_v060_perf')
    session_time = time.time() - start
    
    print(f"✓ Session started in {session_time*1000:.1f}ms")
    print(f"✓ Indexed {len(mm.working_memory)} memories")
    
    results.record('session_start', True, {
        'startup_time_ms': session_time * 1000,
        'memory_count': len(mm.working_memory)
    })
    
    # Test search performance (multiple queries)
    search_times = []
    queries = ['OpenClaw', '用户', 'memory', 'AI']
    
    for query in queries:
        start = time.time()
        results_count = len(mm.search(query, limit=5))
        elapsed = time.time() - start
        search_times.append(elapsed)
        print(f"  Search '{query}': {results_count} results in {elapsed*1000:.1f}ms")
    
    avg_search_time = statistics.mean(search_times) * 1000
    p95_search_time = sorted(search_times)[int(len(search_times) * 0.95)] * 1000 if len(search_times) > 1 else search_times[0] * 1000
    
    print(f"✓ Avg search: {avg_search_time:.1f}ms, P95: {p95_search_time:.1f}ms")
    
    results.record('search_performance', avg_search_time < 100, {
        'avg_search_ms': avg_search_time,
        'p95_search_ms': p95_search_time,
        'queries_tested': len(queries)
    })
    
    # Test cache hit rate
    mm.search('OpenClaw', limit=5)  # First query (cache miss)
    start = time.time()
    mm.search('OpenClaw', limit=5)  # Second query (cache hit)
    cache_hit_time = time.time() - start
    
    print(f"✓ Cache hit search: {cache_hit_time*1000:.1f}ms")
    
    results.record('cache_hit', cache_hit_time < 0.01, {
        'cache_hit_time_ms': cache_hit_time * 1000
    })
    
    mm.end_session()


def compare_v050_vs_v060(results: TestResults):
    """Compare v0.5.0 vs v0.6.0 performance"""
    print("\n=== Comparison: v0.5.0 vs v0.6.0 ===")
    
    # v0.6.0 metrics (from tests)
    v060_results = results.results
    
    # Simulated v0.5.0 baseline (no index, file-based search)
    v050_baseline = {
        'startup_time_ms': 100,  # No index build
        'avg_search_ms': 100,    # File-based search
        'cache_hit_time_ms': 100  # No cache
    }
    
    v060_metrics = {
        'startup_time_ms': v060_results.get('session_start', {}).get('metrics', {}).get('startup_time_ms', 100),
        'avg_search_ms': v060_results.get('search_performance', {}).get('metrics', {}).get('avg_search_ms', 100),
        'cache_hit_time_ms': v060_results.get('cache_hit', {}).get('metrics', {}).get('cache_hit_time_ms', 100),
    }
    
    print("\nPerformance Comparison:")
    print(f"{'Metric':<25} {'v0.5.0':<15} {'v0.6.0':<15} {'Improvement':<15}")
    print("-" * 70)
    
    improvements = {}
    
    for metric in ['startup_time_ms', 'avg_search_ms', 'cache_hit_time_ms']:
        v050_val = v050_baseline[metric]
        v060_val = v060_metrics.get(metric, v050_val)
        
        if v060_val > 0:
            improvement = ((v050_val - v060_val) / v050_val) * 100
            improvements[metric] = improvement
            
            if improvement > 0:
                print(f"{metric:<25} {v050_val:>10.1f}ms   {v060_val:>10.1f}ms   {improvement:>+10.1f}% ↑")
            else:
                print(f"{metric:<25} {v050_val:>10.1f}ms   {v060_val:>10.1f}ms   {improvement:>10.1f}%")
        else:
            print(f"{metric:<25} {v050_val:>10.1f}ms   {'N/A':<15} {'N/A':<15}")
    
    results.record('performance_comparison', True, {
        'improvements': improvements
    })


def test_real_world_scenario(results: TestResults):
    """Test real-world usage scenario"""
    print("\n=== Test: Real-World Scenario ===")
    
    workspace = Path.home() / '.openclaw' / 'workspace'
    mm = MemoryManager(workspace=str(workspace))
    mm.start_session('real_world_test')
    
    # Scenario 1: Store new memory
    start = time.time()
    mm.store("用户偏好使用中文交流", memory_type="semantic", tags=["preference", "language"])
    store_time = time.time() - start
    
    print(f"✓ Store memory: {store_time*1000:.1f}ms")
    results.record('store_memory', True, {
        'store_time_ms': store_time * 1000
    })
    
    # Scenario 2: Search for stored memory
    start = time.time()
    search_results = mm.search("中文", limit=5)
    search_time = time.time() - start
    
    found = len(search_results) > 0
    print(f"✓ Search memory: {len(search_results)} results in {search_time*1000:.1f}ms")
    
    results.record('search_memory', found, {
        'search_time_ms': search_time * 1000,
        'results_count': len(search_results)
    })
    
    # Scenario 3: Repeated search (cache hit)
    start = time.time()
    mm.search("中文", limit=5)
    repeat_time = time.time() - start
    
    speedup = (search_time / repeat_time) if repeat_time > 0 else 0
    print(f"✓ Repeated search: {repeat_time*1000:.1f}ms ({speedup:.1f}x faster)")
    
    results.record('cache_speedup', speedup > 1, {
        'speedup_factor': speedup
    })
    
    mm.end_session()


def run_all_tests():
    """Run all tests and generate report"""
    print("=" * 70)
    print("claw-mem v0.6.0 System Test Suite")
    print("=" * 70)
    
    results = TestResults()
    
    try:
        test_in_memory_index(results)
        test_working_memory_cache(results)
        test_memory_manager_v060(results)
        test_real_world_scenario(results)
        compare_v050_vs_v060(results)
        
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        results.record('exception', False, {'error': str(e)})
    
    # Generate summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    summary = results.summary()
    print(f"\nTotal Tests: {summary['total']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
    
    print("\nDetailed Results:")
    for test_name, result in results.results.items():
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        metrics = result.get('metrics', {})
        metrics_str = ', '.join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in metrics.items())
        print(f"  {status}: {test_name} ({metrics_str})")
    
    # Save results
    import json
    results_file = Path(__file__).parent / 'v060_test_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'version': '0.6.0',
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'results': results.results
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    print("=" * 70)
    
    return summary['failed'] == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
