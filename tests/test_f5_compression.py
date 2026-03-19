#!/usr/bin/env python3
"""
Test script for claw-mem v0.7.0 F5: Index Compression

Tests:
1. Create large index with many memories
2. Test pickle vs gzip compression
3. Verify compression ratio >50%
4. Verify decompression overhead <10ms
"""

import sys
import time
import pickle
import gzip
import zlib
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from claw_mem.storage.index import InMemoryIndex


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


def test_compression():
    """Test index compression functionality"""
    print("=" * 60)
    print("claw-mem v0.7.0 F5: Index Compression Test")
    print("=" * 60)
    
    # Generate test memories
    print(f"\n📝 Generating {1000} test memories...")
    test_memories = generate_test_memories(1000)
    print(f"✅ Generated {len(test_memories)} memories\n")
    
    # Build index
    print("Building index...")
    start = time.time()
    index = InMemoryIndex(ngram_size=3, enable_persistence=True)
    index.build(test_memories, save_index=True)
    build_time = time.time() - start
    print(f"⏱️  Build time: {build_time:.3f}s\n")
    
    # Get original file size
    original_size = index.index_file.stat().st_size
    print(f"📦 Original index size: {original_size / 1024:.2f} KB")
    
    # Test compression methods
    print("\nTesting compression methods...")
    
    # Load index data
    with open(index.index_file, 'rb') as f:
        index_data = pickle.load(f)
    
    # Serialize for compression testing
    serialized = pickle.dumps(index_data, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Serialized size: {len(serialized) / 1024:.2f} KB")
    
    # Test gzip
    start = time.time()
    buf = gzip.compress(serialized, compresslevel=9)
    gzip_time = time.time() - start
    gzip_size = len(buf)
    print(f"\nGzip (level 9):")
    print(f"  Compressed size: {gzip_size / 1024:.2f} KB")
    print(f"  Compression ratio: {gzip_size/len(serialized)*100:.1f}%")
    print(f"  Compression time: {gzip_time*1000:.2f}ms")
    
    # Test decompression
    start = time.time()
    decompressed = gzip.decompress(buf)
    decompress_time = time.time() - start
    print(f"  Decompression time: {decompress_time*1000:.2f}ms")
    
    # Verify integrity
    assert decompressed == serialized, "Decompressed data mismatch!"
    print(f"  ✅ Integrity verified")
    
    # Test zlib
    start = time.time()
    zlib_compressed = zlib.compress(serialized, level=9)
    zlib_compress_time = time.time() - start
    zlib_size = len(zlib_compressed)
    print(f"\nZlib (level 9):")
    print(f"  Compressed size: {zlib_size / 1024:.2f} KB")
    print(f"  Compression ratio: {zlib_size/len(serialized)*100:.1f}%")
    print(f"  Compression time: {zlib_compress_time*1000:.2f}ms")
    
    # Test decompression
    start = time.time()
    zlib_decompressed = zlib.decompress(zlib_compressed)
    zlib_decompress_time = time.time() - start
    print(f"  Decompression time: {zlib_decompress_time*1000:.2f}ms")
    
    # Verify integrity
    assert zlib_decompressed == serialized, "Zlib decompressed data mismatch!"
    print(f"  ✅ Integrity verified")
    
    # Summary
    print("\n" + "=" * 60)
    print("Compression Summary")
    print("=" * 60)
    print(f"Original size:     {len(serialized) / 1024:.2f} KB")
    print(f"Gzip size:         {gzip_size / 1024:.2f} KB ({gzip_size/len(serialized)*100:.1f}%)")
    print(f"Zlib size:         {zlib_size / 1024:.2f} KB ({zlib_size/len(serialized)*100:.1f}%)")
    print(f"Best compression:  {'Gzip' if gzip_size < zlib_size else 'Zlib'}")
    print(f"Decompression overhead: {min(decompress_time, zlib_decompress_time)*1000:.2f}ms")
    
    # Verify targets
    compression_ratio = min(gzip_size, zlib_size) / len(serialized)
    decompress_overhead = min(decompress_time, zlib_decompress_time)
    
    print("\n" + "=" * 60)
    if compression_ratio < 0.5:
        print(f"✅ Compression ratio meets target (<50%): {compression_ratio*100:.1f}%")
    else:
        print(f"⚠️  Compression ratio above target (<50%): {compression_ratio*100:.1f}%")
    
    if decompress_overhead < 0.01:
        print(f"✅ Decompression overhead meets target (<10ms): {decompress_overhead*1000:.2f}ms")
    else:
        print(f"⚠️  Decompression overhead above target (<10ms): {decompress_overhead*1000:.2f}ms")
    print("=" * 60)
    
    return {
        "original_size": len(serialized),
        "gzip_size": gzip_size,
        "zlib_size": zlib_size,
        "compression_ratio": compression_ratio,
        "decompress_time": min(decompress_time, zlib_decompress_time),
    }


if __name__ == "__main__":
    results = test_compression()
    
    print(f"\n📊 F5 Test Results:")
    print(f"  - Original:  {results['original_size'] / 1024:.2f} KB")
    print(f"  - Compressed: {results['gzip_size'] / 1024:.2f} KB")
    print(f"  - Ratio:     {results['compression_ratio']*100:.1f}%")
    print(f"  - Overhead:  {results['decompress_time']*1000:.2f}ms")
