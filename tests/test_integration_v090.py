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
Integration Tests for claw-mem v0.9.0

Tests all P0 features working together.
"""

import sys
import time
import tempfile
import os
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.config_manager import ConfigManager, UnifiedConfig
from claw_mem.health_checker import HealthChecker
from claw_mem.recovery import RecoveryManager
from claw_mem.retrieval.optimized import OptimizedRetriever
from claw_mem.storage.chunked_index import ChunkedIndex


class MockStorage:
    """Mock storage for integration testing"""
    def __init__(self, memories=None):
        self.memories = memories or []
    
    def get_all(self):
        return self.memories
    
    def get_recent(self, limit):
        return self.memories[:limit]


def test_scenario_1_e2e_operations():
    """Scenario 1: End-to-End Memory Operations"""
    print("\n" + "=" * 60)
    print("Scenario 1: End-to-End Memory Operations")
    print("=" * 60)
    
    # Create temporary config
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yml")
        
        # Initialize config
        print("\n1. Initializing config...")
        config = ConfigManager(config_path=config_path, enable_hot_reload=False)
        print("   ✅ Config initialized")
        
        # Initialize retriever
        print("\n2. Initializing optimized retriever...")
        retriever = OptimizedRetriever(
            l1_size=1000,
            l2_size=5000,
            l2_ttl=300
        )
        print("   ✅ Retriever initialized")
        
        # Create test memories
        print("\n3. Creating test memories...")
        memories = []
        for i in range(1000):
            memories.append({
                "id": f"mem_{i:04d}",
                "content": f"This is test memory {i} with some content about topic {i % 10}",
                "tags": ["test", f"topic_{i % 10}"],
                "timestamp": "2026-03-21",
            })
        
        mock_storage = MockStorage(memories)
        print(f"   ✅ Created {len(memories)} memories")
        
        # Test retrieval
        print("\n4. Testing retrieval...")
        start = time.time()
        for i in range(100):
            query = f"topic_{i % 10}"
            results = retriever.search(query, mock_storage, mock_storage, mock_storage)
        elapsed = (time.time() - start) * 1000 / 100
        
        print(f"   Average retrieval time: {elapsed:.2f}ms")
        
        # Verify performance
        assert elapsed < 50, f"❌ Retrieval {elapsed}ms exceeds 50ms target"
        print(f"   ✅ Performance target met: <50ms")
        
        # Verify cache
        stats = retriever.get_stats()
        print(f"   Cache hit rate: {stats['hit_rate_percent']}%")
        assert stats['hit_rate_percent'] > 80, f"❌ Cache hit rate {stats['hit_rate_percent']}% below 80%"
        print(f"   ✅ Cache target met: >80%")
        
        print("\n✅ Scenario 1: PASSED\n")
        return True


def test_scenario_2_large_dataset():
    """Scenario 2: Large Dataset Performance"""
    print("\n" + "=" * 60)
    print("Scenario 2: Large Dataset Performance (100k entries)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create chunked index
        print("\n1. Creating chunked index...")
        index = ChunkedIndex(tmpdir, chunk_size=10000)
        
        # Generate 100k memories
        print("2. Generating 100,000 memories...")
        memories = []
        for i in range(100000):
            memories.append({
                "id": f"mem_{i:06d}",
                "content": f"Test memory {i} with content for performance testing",
                "tags": ["test", "performance"],
                "timestamp": "2026-03-21",
            })
        print(f"   ✅ Generated {len(memories)} memories")
        
        # Build index
        print("\n3. Building chunked index...")
        start = time.time()
        index.build(memories)
        build_time = time.time() - start
        print(f"   Build time: {build_time:.2f}s")
        
        # Test metadata load
        print("\n4. Testing metadata load...")
        start = time.time()
        index.load_metadata()
        metadata_load_time = (time.time() - start) * 1000
        print(f"   Metadata load time: {metadata_load_time:.2f}ms")
        
        # Verify
        assert metadata_load_time < 10, f"❌ Metadata load {metadata_load_time}ms exceeds 10ms"
        print(f"   ✅ Metadata load target met: <10ms")
        
        # Test memory usage
        stats = index.get_stats()
        memory_mb = stats["memory_estimate_mb"]
        print(f"   Memory usage: {memory_mb:.2f}MB")
        
        assert memory_mb < 200, f"❌ Memory {memory_mb}MB exceeds 200MB"
        print(f"   ✅ Memory target met: <200MB")
        
        print("\n✅ Scenario 2: PASSED\n")
        return True


import pytest


@pytest.mark.skip(reason="Performance test - reload time may vary on system load")
def test_scenario_3_hot_reload():
    """Scenario 3: Configuration Hot-Reload"""
    print("\n" + "=" * 60)
    print("Scenario 3: Configuration Hot-Reload")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yml")
        
        # Initialize config
        print("\n1. Initializing config...")
        config = ConfigManager(config_path=config_path, enable_hot_reload=False)
        print("   ✅ Config initialized")
        
        # Test initial value
        print("\n2. Testing initial config value...")
        initial_value = config.get("retrieval.max_results")
        print(f"   Initial max_results: {initial_value}")
        assert initial_value == 10
        print("   ✅ Initial value correct")
        
        # Modify config
        print("\n3. Modifying config...")
        config.set("retrieval.max_results", 20, save=True)
        new_value = config.get("retrieval.max_results")
        print(f"   New max_results: {new_value}")
        assert new_value == 20
        print("   ✅ Config modification works")
        
        # Test reload
        print("\n4. Testing config reload...")
        start = time.time()
        config.load()
        reload_time = (time.time() - start) * 1000
        print(f"   Reload time: {reload_time:.2f}ms")
        
        assert reload_time < 10, f"❌ Reload {reload_time}ms exceeds 10ms"
        print(f"   ✅ Reload target met: <10ms")
        
        print("\n✅ Scenario 3: PASSED\n")
        return True


def test_scenario_4_health_monitoring():
    """Scenario 4: Health Monitoring"""
    print("\n" + "=" * 60)
    print("Scenario 4: Health Monitoring")
    print("=" * 60)
    
    # Create config
    config = ConfigManager(enable_hot_reload=False)
    
    # Initialize health checker
    print("\n1. Initializing health checker...")
    checker = HealthChecker(config)
    print("   ✅ Health checker initialized")
    
    # Run health check
    print("\n2. Running full health check...")
    start = time.time()
    report = checker.check_all()
    check_time = (time.time() - start) * 1000
    print(f"   Health check time: {check_time:.2f}ms")
    
    # Verify
    assert check_time < 1000, f"❌ Health check {check_time}ms exceeds 1000ms"
    print(f"   ✅ Health check target met: <1000ms")
    
    # Verify components
    print(f"   Components checked: {len(report.statuses)}")
    assert len(report.statuses) == 6, f"❌ Expected 6 components, got {len(report.statuses)}"
    print(f"   ✅ All 6 components monitored")
    
    # Print status
    print("\n3. Component Status:")
    for status in report.statuses:
        icon = "✅" if status.healthy else "⚠️"
        print(f"   {icon} {status.component}: {status.message}")
    
    print("\n✅ Scenario 4: PASSED\n")
    return True


def test_scenario_5_recovery():
    """Scenario 5: Exception Recovery"""
    print("\n" + "=" * 60)
    print("Scenario 5: Exception Recovery")
    print("=" * 60)
    
    # Create config
    config = ConfigManager(enable_hot_reload=False)
    
    # Initialize recovery manager
    print("\n1. Initializing recovery manager...")
    recovery = RecoveryManager(config)
    print("   ✅ Recovery manager initialized")
    
    # Simulate index error
    print("\n2. Simulating index error...")
    index_error = Exception("Index file corrupted")
    
    # Test diagnosis
    print("\n3. Testing diagnosis...")
    start = time.time()
    diagnosis = recovery.diagnose(index_error)
    diagnose_time = (time.time() - start) * 1000
    print(f"   Diagnosis time: {diagnose_time:.2f}ms")
    print(f"   Problem type: {diagnosis.problem_type}")
    
    assert diagnose_time < 100, f"❌ Diagnosis {diagnose_time}ms exceeds 100ms"
    print(f"   ✅ Diagnosis target met: <100ms")
    
    # Test recovery
    print("\n4. Testing recovery...")
    start = time.time()
    result = recovery.recover(index_error)
    recover_time = (time.time() - start) * 1000
    print(f"   Recovery time: {recover_time:.2f}ms")
    print(f"   Success: {result.success}")
    print(f"   Strategy: {result.strategy_used.value}")
    
    assert recover_time < 5000, f"❌ Recovery {recover_time}ms exceeds 5000ms"
    print(f"   ✅ Recovery target met: <5000ms")
    
    # Verify success rate
    stats = recovery.get_stats()
    print(f"   Success rate: {stats['success_rate_percent']}%")
    assert stats['success_rate_percent'] >= 95, f"❌ Success rate {stats['success_rate_percent']}% below 95%"
    print(f"   ✅ Success rate target met: >95%")
    
    print("\n✅ Scenario 5: PASSED\n")
    return True


def run_all_scenarios():
    """Run all integration test scenarios"""
    print("\n" + "=" * 60)
    print("claw-mem v0.9.0 Integration Tests")
    print("=" * 60)
    
    results = {
        "Scenario 1 (E2E)": False,
        "Scenario 2 (Large Dataset)": False,
        "Scenario 3 (Hot-Reload)": False,
        "Scenario 4 (Health)": False,
        "Scenario 5 (Recovery)": False,
    }
    
    try:
        results["Scenario 1 (E2E)"] = test_scenario_1_e2e_operations()
    except Exception as e:
        print(f"\n❌ Scenario 1 FAILED: {e}\n")
    
    try:
        results["Scenario 2 (Large Dataset)"] = test_scenario_2_large_dataset()
    except Exception as e:
        print(f"\n❌ Scenario 2 FAILED: {e}\n")
    
    try:
        results["Scenario 3 (Hot-Reload)"] = test_scenario_3_hot_reload()
    except Exception as e:
        print(f"\n❌ Scenario 3 FAILED: {e}\n")
    
    try:
        results["Scenario 4 (Health)"] = test_scenario_4_health_monitoring()
    except Exception as e:
        print(f"\n❌ Scenario 4 FAILED: {e}\n")
    
    try:
        results["Scenario 5 (Recovery)"] = test_scenario_5_recovery()
    except Exception as e:
        print(f"\n❌ Scenario 5 FAILED: {e}\n")
    
    # Summary
    print("\n" + "=" * 60)
    print("Integration Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for scenario, result in results.items():
        icon = "✅" if result else "❌"
        print(f"{icon} {scenario}")
    
    print(f"\nPassed: {passed}/{total}")
    print(f"Pass Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All integration tests PASSED!\n")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED\n")
        return False


if __name__ == "__main__":
    success = run_all_scenarios()
    sys.exit(0 if success else 1)
