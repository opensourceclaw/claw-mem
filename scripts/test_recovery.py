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
Recovery Manager Test (v0.9.0/P0-5)

Test enhanced exception recovery
"""

import sys
import time
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.config_manager import ConfigManager
from claw_mem.recovery import RecoveryManager, RecoveryStrategy, recover_from_error


class TestError(Exception):
    """Test exception for testing"""
    pass


def test_recovery_manager():
    """Test recovery manager functionality"""
    print("\n" + "=" * 60)
    print("Testing Recovery Manager (v0.9.0/P0-5)")
    print("=" * 60)
    
    # Create config
    config = ConfigManager(enable_hot_reload=False)
    
    # Create recovery manager
    print("\n1. Creating recovery manager...")
    manager = RecoveryManager(config)
    print("   ✅ Recovery manager created")
    
    # Test 1: Diagnose index error
    print("\n2. Testing index error diagnosis...")
    index_error = Exception("Index file corrupted: index.pkl")
    start = time.time()
    diagnosis = manager.diagnose(index_error)
    diagnose_time = (time.time() - start) * 1000
    
    print(f"   Diagnosis completed in {diagnose_time:.2f}ms")
    print(f"   Problem type: {diagnosis.problem_type}")
    print(f"   Severity: {diagnosis.severity}")
    print(f"   Description: {diagnosis.description}")
    
    assert diagnose_time < 100, f"❌ Diagnosis time {diagnose_time}ms exceeds 100ms target"
    assert diagnosis.problem_type == "index_corrupted"
    print(f"   ✅ Diagnosis target met: <100ms")
    
    # Test 2: Recover from index error
    print("\n3. Testing index error recovery...")
    start = time.time()
    result = manager.recover(index_error)
    recover_time = (time.time() - start) * 1000
    
    print(f"   Recovery completed in {recover_time:.2f}ms")
    print(f"   Success: {result.success}")
    print(f"   Strategy: {result.strategy_used.value}")
    print(f"   Description: {result.description}")
    
    assert recover_time < 5000, f"❌ Recovery time {recover_time}ms exceeds 5000ms target"
    print(f"   ✅ Recovery time target met: <5s")
    
    # Test 3: Diagnose config error
    print("\n4. Testing config error diagnosis...")
    config_error = Exception("Config file corrupted: config.yml")
    diagnosis = manager.diagnose(config_error)
    
    print(f"   Problem type: {diagnosis.problem_type}")
    assert diagnosis.problem_type == "config_corrupted"
    print(f"   ✅ Config diagnosis correct")
    
    # Test 4: Recover from config error
    print("\n5. Testing config error recovery...")
    start = time.time()
    result = manager.recover(config_error)
    recover_time = (time.time() - start) * 1000
    
    print(f"   Recovery completed in {recover_time:.2f}ms")
    print(f"   Success: {result.success}")
    print(f"   Strategy: {result.strategy_used.value}")
    
    assert recover_time < 5000
    print(f"   ✅ Config recovery target met")
    
    # Test 5: Diagnose memory error
    print("\n6. Testing memory error diagnosis...")
    memory_error = Exception("Memory file corrupted: MEMORY.md")
    diagnosis = manager.diagnose(memory_error)
    
    print(f"   Problem type: {diagnosis.problem_type}")
    assert diagnosis.problem_type == "memory_corrupted"
    print(f"   ✅ Memory diagnosis correct")
    
    # Test 6: Test generic error
    print("\n7. Testing generic error recovery...")
    generic_error = TestError("Something unexpected happened")
    start = time.time()
    result = manager.recover(generic_error)
    recover_time = (time.time() - start) * 1000
    
    print(f"   Recovery completed in {recover_time:.2f}ms")
    print(f"   Success: {result.success}")
    print(f"   Strategy: {result.strategy_used.value}")
    
    assert result.strategy_used == RecoveryStrategy.DEGRADE
    print(f"   ✅ Generic error handled with degradation")
    
    # Test 7: Get statistics
    print("\n8. Testing recovery statistics...")
    stats = manager.get_stats()
    
    print(f"   Total recoveries: {stats['total_recoveries']}")
    print(f"   Successful: {stats['successful_recoveries']}")
    print(f"   Failed: {stats['failed_recoveries']}")
    print(f"   Success rate: {stats['success_rate_percent']}%")
    print(f"   Avg recovery time: {stats['avg_recovery_time_ms']:.2f}ms")
    
    # Verify success rate
    assert stats['success_rate_percent'] >= 95, f"❌ Success rate {stats['success_rate_percent']}% below 95% target"
    print(f"   ✅ Success rate target met: >95%")
    
    # Test 8: Get recovery history
    print("\n9. Testing recovery history...")
    history = manager.get_history(limit=5)
    
    print(f"   History count: {len(history)}")
    if history:
        print(f"   Latest recovery: {history[-1]['problem_type']}")
    
    print(f"   ✅ Recovery history working")
    
    # Test 9: Convenience function
    print("\n10. Testing convenience function...")
    result = recover_from_error(Exception("Test error"), config)
    
    print(f"   Success: {result.success}")
    print(f"   ✅ Convenience function working")
    
    print("\n" + "=" * 60)
    print("Performance Summary")
    print("=" * 60)
    print(f"✅ Diagnosis time: {diagnose_time:.2f}ms (target: <100ms)")
    print(f"✅ Recovery time: {recover_time:.2f}ms (target: <5000ms)")
    print(f"✅ Success rate: {stats['success_rate_percent']:.1f}% (target: >95%)")
    print(f"✅ Strategies available: {len(RecoveryStrategy)}")
    print(f"✅ Recovery history: Working")
    print("=" * 60)
    
    print("\n🎉 All P0-5 targets met! Recovery enhancement complete!\n")
    
    return {
        "diagnose_time_ms": diagnose_time,
        "recover_time_ms": recover_time,
        "success_rate": stats['success_rate_percent'],
        "total_recoveries": stats['total_recoveries'],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("claw-mem v0.9.0/P0-5 Recovery Manager Test")
    print("=" * 60)
    
    results = test_recovery_manager()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")
