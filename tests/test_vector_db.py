# Copyright 2026 Peter Cheng
"""Unit tests for vector_db module."""

import pytest


class TestVectorDBPlugin:
    def test_import_plugin(self):
        from claw_mem.vector_db.plugin import VectorDBFactory, VectorDBType
        assert VectorDBFactory is not None
        assert VectorDBType is not None

    def test_import_chromadb(self):
        from claw_mem.vector_db.chromadb_plugin import ChromaDBPlugin
        assert ChromaDBPlugin is not None
