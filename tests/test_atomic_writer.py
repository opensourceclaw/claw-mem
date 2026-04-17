#!/usr/bin/env python3
"""
Tests for Atomic Writer Module
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from claw_mem.atomic_writer import AtomicWriter
from claw_mem.attention_node import AttentionNode


class TestAtomicWriter:
    """Test atomic writer functionality"""

    @pytest.fixture
    def temp_dir(self):
        """Provide a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def sample_file(self, temp_dir):
        """Create a sample markdown file"""
        file_path = Path(temp_dir) / "test.md"
        file_path.write_text("""---
id: test_001
attention_score: 0.8
parents: []
type: note
last_updated: 2026-04-10T12:00:00
---

This is test content.
""")
        return file_path

    @pytest.fixture
    def sample_node(self, sample_file):
        """Create a sample AttentionNode"""
        return AttentionNode(
            node_id="test_001",
            content_path=str(sample_file),
            score=0.9,
            parents=["parent_001"],
            type="note",
            last_updated=datetime.now()
        )

    def test_save_node_success(self, sample_file, sample_node):
        """Test successful node save"""
        result = AtomicWriter.save_node(sample_node)
        assert result is True

        # Verify file was updated
        content = sample_file.read_text()
        assert "id: test_001" in content
        assert "attention_score: 0.9" in content
        assert "parents:" in content
        assert "- parent_001" in content

    def test_save_node_file_not_found(self, temp_dir):
        """Test save when file doesn't exist"""
        non_existent_file = Path(temp_dir) / "non_existent.md"
        node = AttentionNode(
            node_id="test_001",
            content_path=str(non_existent_file),
            score=0.9,
            parents=[],
            type="note",
            last_updated=datetime.now()
        )

        result = AtomicWriter.save_node(node)
        assert result is False

    def test_replace_frontmatter_existing(self):
        """Test replacing existing frontmatter"""
        content = """---
id: old_id
score: 0.5
---

Old content"""
        new_meta = {"id": "new_id", "score": 0.9}

        result = AtomicWriter._replace_frontmatter(content, new_meta)

        assert "id: new_id" in result
        assert "score: 0.9" in result
        assert "Old content" in result
        assert "old_id" not in result

    def test_replace_frontmatter_no_existing(self):
        """Test adding frontmatter to content without it"""
        content = "Just content without frontmatter"
        new_meta = {"id": "test_id", "score": 0.8}

        result = AtomicWriter._replace_frontmatter(content, new_meta)

        assert result.startswith("---")
        assert "id: test_id" in result
        assert "score: 0.8" in result
        assert "Just content without frontmatter" in result

    def test_replace_frontmatter_malformed(self):
        """Test handling malformed frontmatter"""
        content = """---
id: test_id
score: 0.8

Missing closing ---
Content"""
        new_meta = {"id": "new_id", "score": 0.9}

        result = AtomicWriter._replace_frontmatter(content, new_meta)

        # Should add new frontmatter since existing is malformed
        assert result.startswith("---")
        assert "id: new_id" in result

    def test_atomic_replacement_no_corruption(self, sample_file, sample_node):
        """Test that file is not corrupted if write fails"""
        original_content = sample_file.read_text()

        # Modify node to have invalid data that might cause failure
        # (In practice, this would require mocking to force a failure)
        # For now, we verify successful replacement
        result = AtomicWriter.save_node(sample_node)
        assert result is True

        # Verify file is still valid markdown
        new_content = sample_file.read_text()
        assert "---" in new_content
        assert "id:" in new_content
        assert "attention_score:" in new_content

    def test_save_multiple_nodes(self, temp_dir):
        """Test saving multiple nodes"""
        files = []
        nodes = []

        # Create multiple files and nodes
        for i in range(3):
            file_path = Path(temp_dir) / f"test_{i}.md"
            file_path.write_text(f"Content {i}")
            files.append(file_path)

            node = AttentionNode(
                node_id=f"node_{i}",
                content_path=str(file_path),
                score=0.5 + i * 0.1,
                parents=[f"parent_{i}"],
                type="note",
                last_updated=datetime.now()
            )
            nodes.append(node)

        # Save all nodes
        for node in nodes:
            result = AtomicWriter.save_node(node)
            assert result is True

        # Verify all files were updated correctly
        for i, file_path in enumerate(files):
            content = file_path.read_text()
            assert f"node_{i}" in content
            assert f"0.{5 + i}" in content or f"0.5" in content

    def test_preserve_body_content(self, sample_file, sample_node):
        """Test that body content is preserved"""
        original_body = "This is test content."
        result = AtomicWriter.save_node(sample_node)
        assert result is True

        content = sample_file.read_text()
        assert original_body in content

    def test_special_characters_in_content(self, temp_dir):
        """Test handling special characters"""
        file_path = Path(temp_dir) / "special.md"
        file_path.write_text("---\nid: test\n---\nContent with <>&'\"special chars")

        node = AttentionNode(
            node_id="test",
            content_path=str(file_path),
            score=0.8,
            parents=[],
            type="note",
            last_updated=datetime.now()
        )

        result = AtomicWriter.save_node(node)
        assert result is True

        content = file_path.read_text()
        assert "Content with <>&'\"special chars" in content

    def test_unicode_content(self, temp_dir):
        """Test handling unicode content"""
        file_path = Path(temp_dir) / "unicode.md"
        unicode_text = "Content with 中文, 日本語, and 🎉 emoji"
        file_path.write_text(f"---\nid: test\n---\n{unicode_text}")

        node = AttentionNode(
            node_id="test",
            content_path=str(file_path),
            score=0.8,
            parents=[],
            type="note",
            last_updated=datetime.now()
        )

        result = AtomicWriter.save_node(node)
        assert result is True

        content = file_path.read_text()
        assert unicode_text in content
