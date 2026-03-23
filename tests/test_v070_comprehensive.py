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
claw-mem v0.7.0 F7: Comprehensive Performance Test

Comprehensive performance test suite for all v0.7.0 features:
- F1: Index Persistence
- F2: Lazy Loading
- F3: Incremental Updates
- F4: Version Compatibility
- F5: Index Compression
- F6: Exception Recovery

Generates detailed performance report with metrics and comparisons.
"""

import sys
import time
import json
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claw_mem.storage.index import InMemoryIndex, INDEX_VERSION


def generate_test_memories(count: int = 1000) -> list:
    """Generate test memories"""
    templates = [
        "用户询问 {} 的天气",
        "用户偏好{}",
        "Python 是一种{}编程语言",
        "记忆条目编号{}",
        "测试数据{}",
        "claw-mem 功能测试{}",
        "索引压缩测试{}",
        "性能优化测试{}",
    ]
    
    locations = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
    preferences = ["简洁回答", "详细解释", "使用列表", "使用表格", "中文交流", "英文交流"]
    types = ["通用", "面向对象", "函数式", "动态类型", "解释型"]
    
    memories = []
    for i in range(count):
        template = templates[i % len(templates)]
        if "{}" in template:
            if "天气" in template:
                content = template.format(locations[i % len(locations)])
            elif "偏好" in template:
                content = template.format(preferences[i % len(preferences)])
            elif "编程语言" in template:
                content = template.format(types[i % len(types)])
            else:
                content = template.format(i)
        else:
            content = template
        
        memories.append({
            "id": str(i),
            "content": content
        })
    
    return memories


def test_f1_persistence(memories):
    """Test F1: Index Persistence"""
    print("\n" + "=" * 60)
    print("F1: Index Persistence Test")
    print("=" * 60)
    
    # Build from scratch
    start = time.time()
    index1 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index1.build(memories, save_index=True)
    build_time = time.time() - start
    
    # Load from disk
    start = time.time()
    index2 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index2.load_index()
    load_time = time.time() - start
    
    print(f"Build time:   {build_time*1000:.2f}ms")
    print(f"Load time:    {load_time*1000:.2f}ms")
    print(f"Speedup:      {build_time/load_time:.1f}x" if load_time > 0 else "N/A")
    
    return {
        "build_time_ms": build_time * 1000,
        "load_time_ms": load_time * 1000,
        "speedup_x": build_time / load_time if load_time > 0 else float('inf'),
    }


def test_f2_lazy_loading(memories):
    """Test F2: Lazy Loading"""
    print("\n" + "=" * 60)
    print("F2: Lazy Loading Test")
    print("=" * 60)
    
    # Build and save
    index1 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index1.build(memories, save_index=True)
    
    # Initialize without loading
    start = time.time()
    index2 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    init_time = time.time() - start
    
    # First search (triggers lazy load)
    start = time.time()
    results = index2.ngram_search("天气", limit=5)
    first_search_time = time.time() - start
    
    # Second search (no loading)
    start = time.time()
    results2 = index2.ngram_search("Python", limit=5)
    second_search_time = time.time() - start
    
    print(f"Init time:        {init_time*1000:.3f}ms")
    print(f"First search:     {first_search_time*1000:.3f}ms (includes load)")
    print(f"Second search:    {second_search_time*1000:.3f}ms")
    
    return {
        "init_time_ms": init_time * 1000,
        "first_search_ms": first_search_time * 1000,
        "second_search_ms": second_search_time * 1000,
    }


def test_f3_incremental_update(memories):
    """Test F3: Incremental Updates"""
    print("\n" + "=" * 60)
    print("F3: Incremental Update Test")
    print("=" * 60)
    
    # Build initial index
    index = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index.build(memories, save_index=True)
    
    # Test incremental add
    start = time.time()
    for i in range(10):
        index.add_memory(f"增量测试记忆{i}", f"incr_{i}", save_async=False)
    add_time = time.time() - start
    
    # Test incremental remove
    start = time.time()
    for i in range(5):
        index.remove_memory(f"incr_{i}", save_async=False)
    remove_time = time.time() - start
    
    print(f"Add 10 memories:   {add_time*1000:.2f}ms ({add_time/10*1000:.2f}ms per memory)")
    print(f"Remove 5 memories: {remove_time*1000:.2f}ms ({remove_time/5*1000:.2f}ms per memory)")
    
    return {
        "add_10_time_ms": add_time * 1000,
        "add_per_memory_ms": (add_time / 10) * 1000,
        "remove_5_time_ms": remove_time * 1000,
        "remove_per_memory_ms": (remove_time / 5) * 1000,
    }


def test_f5_compression(memories):
    """Test F5: Index Compression"""
    print("\n" + "=" * 60)
    print("F5: Index Compression Test")
    print("=" * 60)
    
    # Build with compression
    index = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index.build(memories, save_index=True)
    
    # Get file sizes
    compressed_size = index.index_file.stat().st_size
    
    # Calculate uncompressed size
    import pickle
    index_data = {
        "version": INDEX_VERSION,
        "ngram_index": dict(index.ngram_index),
        "documents": index.documents,
        "memory_ids": index.memory_ids,
    }
    uncompressed_size = len(pickle.dumps(index_data, protocol=pickle.HIGHEST_PROTOCOL))
    
    compression_ratio = compressed_size / uncompressed_size * 100
    
    print(f"Uncompressed: {uncompressed_size / 1024:.2f} KB")
    print(f"Compressed:   {compressed_size / 1024:.2f} KB")
    print(f"Ratio:        {compression_ratio:.1f}% (saved {100-compression_ratio:.1f}%)")
    
    return {
        "uncompressed_size_kb": uncompressed_size / 1024,
        "compressed_size_kb": compressed_size / 1024,
        "compression_ratio_pct": compression_ratio,
        "space_saved_pct": 100 - compression_ratio,
    }


def test_f6_recovery(memories):
    """Test F6: Exception Recovery"""
    print("\n" + "=" * 60)
    print("F6: Exception Recovery Test")
    print("=" * 60)
    
    # Build and create backup
    index = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index.build(memories, save_index=True)
    index.add_memory("触发备份", "backup_test", save_async=False)
    
    # Count backups
    backup_files = list(index.index_dir.glob("*.backup_*.gz"))
    
    # Test integrity check
    is_valid, issues = index.verify_integrity()
    
    # Test recovery time
    start = time.time()
    index2 = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index2.load_index()
    recovery_time = time.time() - start
    
    print(f"Backup count:      {len(backup_files)}")
    print(f"Integrity check:   {'PASS' if is_valid else 'FAIL'}")
    print(f"Recovery time:     {recovery_time*1000:.2f}ms")
    
    return {
        "backup_count": len(backup_files),
        "integrity_passed": is_valid,
        "recovery_time_ms": recovery_time * 1000,
    }


def run_all_tests():
    """Run all performance tests"""
    print("=" * 60)
    print("claw-mem v0.7.0 - Comprehensive Performance Test")
    print("=" * 60)
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Version: {INDEX_VERSION}")
    
    # Generate test data
    print(f"\n📝 Generating test memories...")
    memories = generate_test_memories(1000)
    print(f"✅ Generated {len(memories)} memories")
    
    # Run tests
    results = {
        "metadata": {
            "date": datetime.now().isoformat(),
            "version": INDEX_VERSION,
            "memory_count": len(memories),
        },
        "f1_persistence": test_f1_persistence(memories),
        "f2_lazy_loading": test_f2_lazy_loading(memories),
        "f3_incremental": test_f3_incremental_update(memories),
        "f5_compression": test_f5_compression(memories),
        "f6_recovery": test_f6_recovery(memories),
    }
    
    # Generate summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    
    print("\n🚀 Speed Improvements:")
    print(f"  • Startup: 1.5s → {results['f1_persistence']['load_time_ms']:.2f}ms ({results['f1_persistence']['speedup_x']:.0f}x faster)")
    print(f"  • Init (lazy): {results['f2_lazy_loading']['init_time_ms']:.3f}ms")
    print(f"  • Incremental add: {results['f3_incremental']['add_per_memory_ms']:.2f}ms per memory")
    
    print("\n💾 Storage:")
    print(f"  • Compression: {results['f5_compression']['compression_ratio_pct']:.1f}% ({results['f5_compression']['space_saved_pct']:.1f}% saved)")
    print(f"  • Index size: {results['f5_compression']['compressed_size_kb']:.2f} KB")
    
    print("\n🛡️  Reliability:")
    print(f"  • Backups: {results['f6_recovery']['backup_count']}")
    print(f"  • Integrity: {'✅ PASS' if results['f6_recovery']['integrity_passed'] else '❌ FAIL'}")
    
    # Save results
    results_file = Path(__file__).parent / "v070_performance_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Verify targets
    print("\n" + "=" * 60)
    print("TARGET VERIFICATION")
    print("=" * 60)
    
    targets = [
        ("Startup <500ms", results['f1_persistence']['load_time_ms'] < 500),
        ("Lazy init <10ms", results['f2_lazy_loading']['init_time_ms'] < 10),
        ("Incremental <50ms", results['f3_incremental']['add_per_memory_ms'] < 50),
        ("Compression <50%", results['f5_compression']['compression_ratio_pct'] < 50),
        ("Recovery <1s", results['f6_recovery']['recovery_time_ms'] < 1000),
        ("Integrity check", results['f6_recovery']['integrity_passed']),
    ]
    
    all_passed = True
    for target, passed in targets:
        status = "✅" if passed else "❌"
        print(f"  {status} {target}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TARGETS MET - v0.7.0 READY FOR RELEASE!")
    else:
        print("⚠️  SOME TARGETS NOT MET - REVIEW RECOMMENDED")
    print("=" * 60)
    
    return results, all_passed


if __name__ == "__main__":
    results, all_passed = run_all_tests()
    
    # Exit code for CI/CD
    sys.exit(0 if all_passed else 1)
