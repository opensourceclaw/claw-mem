# Copyright 2026 Peter Cheng
"""Unit tests for health_checker, attention, and links modules."""

import pytest
from pathlib import Path


class TestHealthChecker:
    def test_import(self):
        from claw_mem.health_checker import HealthChecker

        assert HealthChecker is not None


class TestAttentionIndex:
    def test_import(self):
        from claw_mem.attention_index import AttentionIndex

        assert AttentionIndex is not None

    def test_init(self, tmp_path):
        from claw_mem.attention_index import AttentionIndex

        idx = AttentionIndex(memory_root=str(tmp_path))
        assert idx is not None


class TestAttentionNode:
    def test_import(self):
        from claw_mem.attention_node import AttentionNode

        assert AttentionNode is not None


class TestMemoryLinks:
    def test_imports(self):
        from claw_mem.links.memory_links import MemoryLinkManager, MemoryLinkParser

        assert MemoryLinkManager is not None
        assert MemoryLinkParser is not None

    def test_link_manager(self):
        from claw_mem.links.memory_links import MemoryLinkManager

        mlm = MemoryLinkManager()
        assert mlm is not None

    def test_parse_links(self):
        from claw_mem.links.memory_links import MemoryLinkParser

        parser = MemoryLinkParser()
        refs = parser.parse_links("See [[mem1]]", "src")
        assert isinstance(refs, list)
