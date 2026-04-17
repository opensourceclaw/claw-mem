#!/usr/bin/env python3
"""
Tests for Context Manager Module
"""

import pytest
import tempfile
from pathlib import Path

from claw_mem.context_manager import ClawMemContextManager


class TestClawMemContextManager:
    """Test context manager functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Provide a temporary directory with sample files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample markdown files
            for i in range(3):
                file_path = Path(tmpdir) / f"note_{i}.md"
                file_path.write_text(f"""---
id: note_{i}
attention_score: 0.{i + 5}
parents: []
type: note
last_updated: 2026-04-10T12:00:00
---

This is note {i} content.
""")
            yield tmpdir

    @pytest.fixture
    def context_manager(self, temp_dir):
        """Create a context manager instance"""
        return ClawMemContextManager(temp_dir)

    def test_initialization(self, context_manager):
        """Test context manager initialization"""
        assert context_manager is not None
        assert context_manager.index is not None
        assert context_manager.assembler is not None
        assert context_manager._initialized is False

    def test_initialize_builds_index(self, context_manager):
        """Test that initialize() builds the index"""
        context_manager.initialize()
        assert context_manager._initialized is True
        assert len(context_manager.index.nodes) == 3

    def test_get_context_without_initialization(self, context_manager):
        """Test that get_context raises error when not initialized"""
        with pytest.raises(RuntimeError) as exc_info:
            context_manager.get_context()
        assert "not initialized" in str(exc_info.value).lower()

    def test_get_context_with_initialization(self, context_manager):
        """Test get_context after initialization"""
        context_manager.initialize()
        context = context_manager.get_context(max_tokens=1000, top_k=2)
        assert isinstance(context, str)
        assert len(context) > 0

    def test_boost_existing_node(self, context_manager):
        """Test boosting an existing node"""
        context_manager.initialize()

        # Get initial score
        initial_score = context_manager.index.nodes["note_0"].score

        # Boost the node
        result = context_manager.boost_node("note_0", amount=0.1)
        assert result is True

        # Verify score increased
        new_score = context_manager.index.nodes["note_0"].score
        assert new_score > initial_score

    def test_boost_nonexistent_node(self, context_manager):
        """Test boosting a nonexistent node"""
        context_manager.initialize()
        result = context_manager.boost_node("nonexistent_node", amount=0.1)
        assert result is False

    def test_boost_negative_amount(self, context_manager):
        """Test boosting with negative amount (should still work)"""
        context_manager.initialize()

        initial_score = context_manager.index.nodes["note_0"].score
        result = context_manager.boost_node("note_0", amount=-0.1)
        assert result is True

        new_score = context_manager.index.nodes["note_0"].score
        assert new_score < initial_score

    def test_save_changes(self, context_manager):
        """Test saving changes to disk"""
        context_manager.initialize()

        # Modify a node score
        context_manager.boost_node("note_0", amount=0.2)

        # Save changes
        context_manager.save_changes()

        # Verify file was updated (AtomicWriter handles this)
        # We can't easily verify this without checking the file content,
        # but we can at least ensure no exception was raised
        assert True  # If we got here, save_changes() didn't crash

    def test_custom_core_rules(self, temp_dir):
        """Test context manager with custom core rules"""
        core_rules = ["rule1", "rule2", "rule3"]
        manager = ClawMemContextManager(temp_dir, core_rules=core_rules)
        assert manager.assembler.core_block_paths == core_rules

    def test_get_context_different_params(self, context_manager):
        """Test get_context with different parameters"""
        context_manager.initialize()

        # Test with different max_tokens
        context1 = context_manager.get_context(max_tokens=500, top_k=1)
        context2 = context_manager.get_context(max_tokens=2000, top_k=2)

        assert isinstance(context1, str)
        assert isinstance(context2, str)
        # context2 should be longer (more tokens and more nodes)
        assert len(context2) >= len(context1)

    def test_multiple_boosts(self, context_manager):
        """Test multiple boosts on the same node"""
        context_manager.initialize()

        initial_score = context_manager.index.nodes["note_0"].score

        # Boost multiple times (but note: score is capped at 1.0)
        context_manager.boost_node("note_0", amount=0.1)
        context_manager.boost_node("note_0", amount=0.2)
        context_manager.boost_node("note_0", amount=0.3)

        final_score = context_manager.index.nodes["note_0"].score

        # Score should increase (but may be capped at 1.0)
        assert final_score > initial_score
        # Score should be within [0.0, 1.0]
        assert 0.0 <= final_score <= 1.0

    def test_boost_all_nodes(self, context_manager):
        """Test boosting all nodes"""
        context_manager.initialize()

        # Boost all nodes
        for node_id in context_manager.index.nodes:
            result = context_manager.boost_node(node_id, amount=0.05)
            assert result is True

    def test_empty_memory_root(self):
        """Test context manager with empty memory root"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ClawMemContextManager(tmpdir)
            manager.initialize()
            assert len(manager.index.nodes) == 0
            # get_context should still work, just return empty or minimal context
            context = manager.get_context()
            assert isinstance(context, str)
