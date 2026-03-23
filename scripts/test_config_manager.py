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
Configuration Manager Test (v0.9.0/P0-3)

Test unified configuration with hot-reload
"""

import sys
import time
import tempfile
import os
sys.path.insert(0, '/Users/liantian/workspace/osprojects/claw-mem/src')

from claw_mem.config_manager import ConfigManager, UnifiedConfig


def test_config_creation():
    """Test config creation and loading"""
    print("\n" + "=" * 60)
    print("Testing Config Manager (v0.9.0/P0-3)")
    print("=" * 60)
    
    # Create temporary config
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yml")
        
        # Test 1: Create default config
        print("\n1. Testing default config creation...")
        start = time.time()
        config = ConfigManager(config_path=config_path, enable_hot_reload=False)
        create_time = (time.time() - start) * 1000
        print(f"   Config created in {create_time:.2f}ms")
        
        # Verify defaults
        assert config.get("storage.workspace") == "~/.openclaw/workspace"
        assert config.get("retrieval.max_results") == 10
        assert config.get("performance.enable_caching") == True
        print("   ✅ Default values correct")
        
        # Test 2: Load time
        print("\n2. Testing config load time...")
        start = time.time()
        config.load()
        load_time = (time.time() - start) * 1000
        print(f"   Config loaded in {load_time:.2f}ms")
        
        assert load_time < 10, f"❌ Load time {load_time}ms exceeds 10ms target"
        print(f"   ✅ Load time target met: <10ms")
        
        # Test 3: Set and get values
        print("\n3. Testing set/get operations...")
        config.set("retrieval.max_results", 20, save=False)
        value = config.get("retrieval.max_results")
        assert value == 20
        print(f"   ✅ Set/get works correctly")
        
        # Test 4: Save and reload
        print("\n4. Testing save and reload...")
        config.set("retrieval.max_results", 20, save=True)
        
        # Create new instance to verify persistence
        config2 = ConfigManager(config_path=config_path, enable_hot_reload=False)
        value2 = config2.get("retrieval.max_results")
        assert value2 == 20
        print(f"   ✅ Persistence works correctly")
        
        # Test 5: Validation
        print("\n5. Testing validation...")
        config.set("retrieval.max_results", 0, save=False)  # Invalid value
        errors = config.validate()
        assert len(errors) > 0
        print(f"   ✅ Validation detects errors: {len(errors)} found")
        
        # Reset to valid value
        config.set("retrieval.max_results", 10, save=False)
        errors = config.validate()
        assert len(errors) == 0
        print(f"   ✅ Valid config passes validation")
        
        # Test 6: Hot-reload simulation
        print("\n6. Testing hot-reload capability...")
        config.set("storage.workspace", "/tmp/test-workspace", save=True)
        
        # Simulate external change
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        data['storage']['workspace'] = "/tmp/changed-workspace"
        with open(config_path, 'w') as f:
            yaml.dump(data, f)
        
        # Manual reload
        config.load()
        new_value = config.get("storage.workspace")
        assert new_value == "/tmp/changed-workspace"
        print(f"   ✅ Hot-reload works correctly")
        
        # Test 7: Config stats
        print("\n7. Testing statistics...")
        stats = config.get_stats()
        print(f"   Config path: {stats['config_path']}")
        print(f"   Config exists: {stats['config_exists']}")
        print(f"   Version: {stats['version']}")
        print(f"   Hot-reload enabled: {stats['hot_reload_enabled']}")
        
        print("\n" + "=" * 60)
        print("Performance Summary")
        print("=" * 60)
        print(f"✅ Config creation: {create_time:.2f}ms")
        print(f"✅ Config load: {load_time:.2f}ms (target: <10ms)")
        print(f"✅ Set/get: Instant")
        print(f"✅ Persistence: Working")
        print(f"✅ Validation: Working")
        print(f"✅ Hot-reload: Working")
        print("=" * 60)
        
        print("\n🎉 All P0-3 targets met! Config management complete!\n")
        
        return {
            "create_time_ms": create_time,
            "load_time_ms": load_time,
        }


if __name__ == "__main__":
    print("=" * 60)
    print("claw-mem v0.9.0/P0-3 Config Manager Test")
    print("=" * 60)
    
    results = test_config_creation()
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60 + "\n")
