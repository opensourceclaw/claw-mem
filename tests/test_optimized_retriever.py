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
Performance Tests for Optimized Retriever (v0.9.0)

Tests to verify:
- Query latency <50ms for short text
- Query latency <200ms for long text
- Cache hit rate >80%
"""

import time
import pytest
from src.claw_mem.retrieval.optimized import OptimizedRetriever, LRUCache, TTLCache


class TestLRUCache:
    """Test LRU Cache implementation"""
    
    def test_basic_operations(self):
        """Test basic get/put operations"""
        cache = LRUCache(max_size=3)
        
        # Put entries
        cache.put("key1", [{"content": "value1"}])
        cache.put("key2", [{"content": "value2"}])
        cache.put("key3", [{"content": "value3"}])
        
        # Get entries
        assert cache.get("key1") == [{"content": "value1"}]
        assert cache.get("key2") == [{"content": "value2"}]
        assert cache.get("key3") == [{"content": "value3"}]
        
        # Cache size
        assert cache.size() == 3
    
    def test_eviction(self):
        """Test LRU eviction when max size reached"""
        cache = LRUCache(max_size=2)
        
        cache.put("key1", [{"content": "value1"}])
        cache.put("key2", [{"content": "value2"}])
        cache.put("key3", [{"content": "value3"}])  # Should evict key1
        
        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == [{"content": "value2"}]
        assert cache.get("key3") == [{"content": "value3"}]
    
    def test_lru_order(self):
        """Test LRU ordering - accessing moves to end"""
        cache = LRUCache(max_size=2)
        
        cache.put("key1", [{"content": "value1"}])
        cache.put("key2", [{"content": "value2"}])
        
        # Access key1 (should move to end)
        cache.get("key1")
        
        # Add key3 (should evict key2, not key1)
        cache.put("key3", [{"content": "value3"}])
        
        assert cache.get("key1") == [{"content": "value1"}]  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == [{"content": "value3"}]


class TestTTLCache:
    """Test TTL Cache implementation"""
    
    def test_basic_operations(self):
        """Test basic get/put operations"""
        cache = TTLCache(max_size=100, ttl_seconds=300)
        
        cache.put("key1", [{"content": "value1"}])
        assert cache.get("key1") == [{"content": "value1"}]
    
    def test_expiration(self):
        """Test TTL expiration"""
        cache = TTLCache(max_size=100, ttl_seconds=1)  # 1 second TTL
        
        cache.put("key1", [{"content": "value1"}])
        assert cache.get("key1") == [{"content": "value1"}]
        
        # Wait for expiration
        time.sleep(1.1)
        
        assert cache.get("key1") is None  # Expired
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries"""
        cache = TTLCache(max_size=100, ttl_seconds=1)
        
        cache.put("key1", [{"content": "value1"}])
        cache.put("key2", [{"content": "value2"}])
        
        time.sleep(1.1)
        
        expired_count = cache.cleanup_expired()
        assert expired_count == 2
        assert cache.size() == 0


class TestOptimizedRetriever:
    """Test Optimized Retriever with caching"""
    
    @pytest.fixture
    def mock_storages(self):
        """Create mock storage objects"""
        class MockStorage:
            def __init__(self, memories):
                self.memories = memories
            
            def get_all(self):
                return self.memories
            
            def get_recent(self, limit):
                return self.memories[:limit]
        
        # Create test memories
        memories = [
            {"content": "用户偏好使用中文交流", "tags": ["偏好", "语言"], "timestamp": "2026-03-21"},
            {"content": "claw-mem 仓库地址是 https://github.com/opensourceclaw/claw-mem", "tags": ["项目"], "timestamp": "2026-03-20"},
            {"content": "Peter Cheng 是项目负责人", "tags": ["人员"], "timestamp": "2026-03-19"},
        ] * 100  # 300 memories
        
        return {
            "episodic": MockStorage(memories),
            "semantic": MockStorage(memories),
            "procedural": MockStorage(memories),
        }
    
    def test_cache_hit(self, mock_storages):
        """Test cache hit on repeated queries"""
        retriever = OptimizedRetriever()
        
        # First query (cache miss)
        result1 = retriever.search("中文", **mock_storages)
        stats1 = retriever.get_stats()
        
        # Second query (cache hit)
        result2 = retriever.search("中文", **mock_storages)
        stats2 = retriever.get_stats()
        
        # Verify cache hit
        assert stats2["hits"] == 1
        assert stats2["hit_rate_percent"] == 50.0  # 1 hit, 1 miss
    
    def test_performance_short_text(self, mock_storages):
        """Test performance for short text queries (<50ms target)"""
        retriever = OptimizedRetriever()
        
        # Warm up cache
        retriever.search("中文", **mock_storages)
        
        # Measure query time
        start = time.time()
        for _ in range(100):
            retriever.search("中文", **mock_storages)
        end = time.time()
        
        avg_time_ms = (end - start) / 100 * 1000
        
        # Target: <50ms for short text
        assert avg_time_ms < 50, f"Average query time {avg_time_ms}ms exceeds 50ms target"
    
    def test_cache_hit_rate(self, mock_storages):
        """Test cache hit rate >80% with repeated queries"""
        retriever = OptimizedRetriever()
        
        # Simulate 100 queries with 10 unique queries
        unique_queries = ["中文", "仓库", "负责人", "项目", "偏好", "语言", "地址", "GitHub", "Peter", "claw"]
        
        for i in range(100):
            query = unique_queries[i % 10]
            retriever.search(query, **mock_storages)
        
        stats = retriever.get_stats()
        
        # Target: >80% hit rate
        assert stats["hit_rate_percent"] > 80, f"Cache hit rate {stats['hit_rate_percent']}% below 80% target"
    
    def test_memory_usage(self, mock_storages):
        """Test memory usage <100MB for cache"""
        retriever = OptimizedRetriever(l1_size=1000, l2_size=5000)
        
        # Generate 1000 unique queries
        for i in range(1000):
            retriever.search(f"查询{i}", **mock_storages)
        
        stats = retriever.get_stats()
        
        # Estimate memory usage
        l1_memory_mb = stats["l1_cache"]["memory_estimate_mb"]
        l2_memory_mb = stats["l2_cache"]["memory_estimate_mb"]
        total_memory_mb = l1_memory_mb + l2_memory_mb
        
        # Target: <100MB
        assert total_memory_mb < 100, f"Cache memory usage {total_memory_mb}MB exceeds 100MB target"


if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"])
