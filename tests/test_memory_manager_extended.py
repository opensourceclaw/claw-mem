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
Extended MemoryManager Tests for Coverage Improvement

Tests for:
- All search modes (bm25, hybrid, entity, hybrid_entity, heuristic, smart, enhanced_smart)
- Cross-session search
- Memory type filtering
- Procedural memory storage
- Session management with initial context
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from claw_mem.memory_manager import MemoryManager


class TestMemoryManagerExtended:
    """Extended tests for Memory Manager to improve coverage"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create necessary directories
        (workspace / "memory").mkdir()

        yield workspace

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_store_procedural_memory(self, temp_workspace):
        """Test storing procedural memory"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        result = memory.store("Fix bugs by adding unit tests", memory_type="procedural")
        assert result is True

        # Verify procedural count
        stats = memory.get_stats()
        assert stats["procedural_count"] > 0

    def test_search_all_modes(self, temp_workspace):
        """Test all search modes"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        # Store memories
        memory.store("User prefers Python for development", memory_type="semantic")
        memory.store("Daily log: worked on claw-mem project", memory_type="episodic")

        # Test all search modes
        search_modes = [
            "keyword",
            "bm25",
            "hybrid",
            "entity",
            "hybrid_entity",
            "heuristic",
            "smart",
            "enhanced_smart",
        ]

        for mode in search_modes:
            results = memory.search("Python", mode=mode, limit=5)
            # All modes should return some results (mode-specific)
            assert isinstance(results, list), f"Mode {mode} should return list"
            print(f"Mode {mode}: {len(results)} results")

    def test_search_with_memory_type_filter(self, temp_workspace):
        """Test search with memory type filter"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        # Store different types
        memory.store("User likes Python", memory_type="semantic")
        memory.store("Fixed bug today", memory_type="episodic")
        memory.store("How to debug code", memory_type="procedural")

        # Search with memory_type filter
        results = memory.search("Python", memory_type="semantic", mode="keyword")
        assert len(results) > 0
        assert all(r.get("type") == "semantic" for r in results)

        # Test episodic filter
        results = memory.search("Fixed", memory_type="episodic", mode="keyword")
        assert len(results) > 0

        # Test procedural filter
        results = memory.search("debug", memory_type="procedural", mode="keyword")
        assert len(results) > 0

    def test_cross_session_search(self, temp_workspace):
        """Test cross-session search"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("session1")

        # Store memories
        memory.store("Project Neo vision: digital memory", memory_type="semantic")

        # End session
        memory.end_session()

        # Start new session and cross-session search
        memory.start_session("session2")

        results = memory.cross_session_search(
            query="Project Neo",
            layers=["l2", "l3"],
            limit=5,
        )

        assert len(results) > 0
        # Results should be from previous session
        assert any("Neo" in r.get("content", "") for r in results)

    def test_start_session_with_initial_context(self, temp_workspace):
        """Test start session with initial context"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("session1")

        # Store contextual memories
        memory.store("User works on tech projects", memory_type="semantic")
        memory.end_session()

        # Start new session with context
        memory.start_session("session2", initial_context="tech projects")

        # Verify session started
        assert memory.session_id == "session2"
        assert memory.session_start is not None

        # Memories should be retrieved based on context
        results = memory.search("tech", mode="keyword")
        assert len(results) > 0

    def test_multiple_memories_with_tags(self, temp_workspace):
        """Test storing multiple memories with tags"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        # Store memories with tags
        memory.store("Memory 1", memory_type="episodic", tags=["test", "demo"])
        memory.store("Memory 2", memory_type="semantic", tags=["important", "work"])

        # Search and verify tags
        results = memory.search("Memory", mode="keyword")
        assert len(results) > 0

        # Check tags exist
        for result in results:
            assert "tags" in result
            assert isinstance(result["tags"], list)

    def test_search_with_limit(self, temp_workspace):
        """Test search with different limits"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        # Store multiple memories
        for i in range(10):
            memory.store(f"Test memory {i}", memory_type="episodic")

        # Search with limit
        results = memory.search("Test", limit=3, mode="keyword")
        assert len(results) <= 3

        # Search with larger limit
        results = memory.search("Test", limit=10, mode="keyword")
        assert len(results) <= 10

    def test_store_without_update_index(self, temp_workspace):
        """Test store without updating index"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        # Store without updating index
        result = memory.store("Test memory", memory_type="episodic", update_index=False)
        assert result is True

        # Manually rebuild index
        memory._load_and_build_index()

        # Now should be able to search
        results = memory.search("Test", mode="keyword")
        assert len(results) > 0

    def test_multiple_sessions(self, temp_workspace):
        """Test multiple sessions"""
        memory = MemoryManager(str(temp_workspace))

        # Start first session
        memory.start_session("session1")
        memory.store("Session 1 memory", memory_type="episodic")
        memory.end_session()

        # Start second session
        memory.start_session("session2")
        memory.store("Session 2 memory", memory_type="episodic")

        # Verify session 2 is active
        assert memory.session_id == "session2"

        # Cross-session search should find both
        results = memory.cross_session_search("memory", limit=10)
        assert len(results) > 0

    def test_search_empty_query(self, temp_workspace):
        """Test search with empty query"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        memory.store("Test memory", memory_type="episodic")

        # Search with empty query
        results = memory.search("", mode="keyword")
        assert isinstance(results, list)

    def test_get_stats_after_operations(self, temp_workspace):
        """Test get_stats after various operations"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        # Store memories
        memory.store("Episodic memory", memory_type="episodic")
        memory.store("Semantic memory", memory_type="semantic")
        memory.store("Procedural memory", memory_type="procedural")

        # Get stats
        stats = memory.get_stats()

        assert stats["session_id"] == "test_session"
        assert stats["episodic_count"] > 0
        assert stats["semantic_count"] > 0
        assert stats["procedural_count"] > 0
        assert stats["working_memory_count"] > 0
        assert stats["index_built"] is True

    def test_repr(self, temp_workspace):
        """Test __repr__ method"""
        memory = MemoryManager(str(temp_workspace))
        memory.start_session("test_session")

        repr_str = repr(memory)
        assert "MemoryManager" in repr_str
        assert "workspace" in repr_str
        assert "session" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
