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
Extended Retrieval Tests for Coverage Improvement

Tests for:
- Enhanced Smart Retriever
"""

import pytest
from claw_mem.retrieval.enhanced_smart_retriever import EnhancedSmartRetriever


class TestEnhancedSmartRetriever:
    """Test Enhanced Smart Retriever"""

    @pytest.fixture
    def sample_memories(self):
        """Sample memories for testing"""
        return [
            {"id": "1", "content": "User likes Python programming", "tags": ["preference"]},
            {"id": "2", "content": "Yesterday's weather was sunny", "tags": ["log"]},
            {"id": "3", "content": "Last week I worked on claw-mem", "tags": ["work"]},
            {"id": "4", "content": "Tomorrow's meeting is at 10am", "tags": ["schedule"]},
            {"id": "5", "content": "User hates waiting for slow code", "tags": ["preference"]},
        ]

    def test_enhanced_smart_initialization(self):
        """Test EnhancedSmartRetriever initialization"""
        retriever = EnhancedSmartRetriever()
        assert retriever is not None

    def test_enhanced_smart_search(self, sample_memories):
        """Test enhanced smart search"""
        retriever = EnhancedSmartRetriever()
        results = retriever.search("Python", sample_memories, limit=5)
        assert isinstance(results, list)

    def test_enhanced_smart_search_with_preferences(self, sample_memories):
        """Test enhanced smart search with preference detection"""
        retriever = EnhancedSmartRetriever()
        results = retriever.search("I like Python", sample_memories, limit=5)
        assert isinstance(results, list)

    def test_enhanced_smart_search_with_time_expressions(self, sample_memories):
        """Test enhanced smart search with time expressions"""
        retriever = EnhancedSmartRetriever()
        results = retriever.search("yesterday weather", sample_memories, limit=5)
        assert isinstance(results, list)

    def test_enhanced_smart_search_empty_query(self, sample_memories):
        """Test enhanced smart search with empty query"""
        retriever = EnhancedSmartRetriever()
        results = retriever.search("", sample_memories, limit=5)
        assert isinstance(results, list)

    def test_enhanced_smart_search_empty_memories(self):
        """Test enhanced smart search with empty memories"""
        retriever = EnhancedSmartRetriever()
        results = retriever.search("test", [], limit=5)
        assert results == []

    def test_enhanced_smart_search_limit(self, sample_memories):
        """Test enhanced smart search with limit"""
        retriever = EnhancedSmartRetriever()
        results = retriever.search("Python", sample_memories, limit=2)
        assert len(results) <= 2

    def test_enhanced_smart_search_rank_by_importance(self, sample_memories):
        """Test enhanced smart search with importance ranking"""
        retriever = EnhancedSmartRetriever()

        # Add importance to memories
        memories_with_importance = []
        for m in sample_memories:
            m_copy = m.copy()
            m_copy["importance"] = 0.8
            memories_with_importance.append(m_copy)

        results = retriever.search("Python", memories_with_importance, limit=5, rank_by_importance=True)
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
