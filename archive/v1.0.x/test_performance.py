#!/usr/bin/env python3
"""
Performance Tests for claw-mem v1.0.4

Red Hat RHEL Style Performance Benchmarking
"""

import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'skills' / 'claw-mem' / 'core'))

from semantic_detector import SemanticViolationDetector
from rule_engine import RuleEngine

def test_detection_latency():
    """Test violation detection latency"""
    print("Testing detection latency...")
    
    detector = SemanticViolationDetector()
    
    # Warm up
    for _ in range(10):
        detector.detect_violations("test")
    
    # Benchmark
    start = time.perf_counter()
    for _ in range(100):
        detector.detect_violations("Create package neorl")
    end = time.perf_counter()
    
    avg_latency_ms = (end - start) / 100 * 1000
    
    print(f"  Average latency: {avg_latency_ms:.2f}ms")
    
    if avg_latency_ms < 50:
        print("  ✅ PASSED (<50ms target)")
        return True
    else:
        print("  ❌ FAILED (>50ms target)")
        return False

def test_rule_engine_latency():
    """Test rule engine latency"""
    print("Testing rule engine latency...")
    
    engine = RuleEngine()
    
    # Warm up
    for _ in range(10):
        engine.validate("test")
    
    # Benchmark
    start = time.perf_counter()
    for _ in range(100):
        engine.validate("Create package neorl")
    end = time.perf_counter()
    
    avg_latency_ms = (end - start) / 100 * 1000
    
    print(f"  Average latency: {avg_latency_ms:.2f}ms")
    
    if avg_latency_ms < 50:
        print("  ✅ PASSED (<50ms target)")
        return True
    else:
        print("  ❌ FAILED (>50ms target)")
        return False

def test_memory_usage():
    """Test memory usage"""
    print("Testing memory usage...")
    
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    print(f"  Memory usage: {memory_mb:.2f}MB")
    
    if memory_mb < 100:
        print("  ✅ PASSED (<100MB target)")
        return True
    else:
        print("  ❌ FAILED (>100MB target)")
        return False

def main():
    print("="*70)
    print("claw-mem v1.0.4 Performance Tests")
    print("="*70)
    print()
    
    results = []
    
    results.append(("Detection Latency", test_detection_latency()))
    print()
    
    results.append(("Rule Engine Latency", test_rule_engine_latency()))
    print()
    
    results.append(("Memory Usage", test_memory_usage()))
    print()
    
    print("="*70)
    print("Performance Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
    
    print()
    print(f"Total: {passed}/{total} passed")
    
    if passed == total:
        print()
        print("✅ ALL PERFORMANCE TESTS PASSED")
        return 0
    else:
        print()
        print("❌ SOME PERFORMANCE TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
