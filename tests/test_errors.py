"""Tests for hierarchical exception types (v2.20.0)."""

import pytest
from claw_mem.errors import (
    ClawMemError, StorageError, MemoryNotFoundError,
    StorageFullError, StorageCorruptedError,
    RetrievalError, IndexNotReadyError, QueryTooLongError,
    CompressionError, CompressionDisabledError,
    InvalidThresholdError,
)


class TestErrorHierarchy:
    """Verify exception type inheritance."""

    def test_storage_error_is_clawmem(self):
        err = StorageError("test")
        assert isinstance(err, ClawMemError)
        assert isinstance(err, Exception)

    def test_memory_not_found_chain(self):
        err = MemoryNotFoundError("mem_123")
        assert isinstance(err, StorageError)
        assert isinstance(err, ClawMemError)

    def test_retrieval_error_chain(self):
        err = RetrievalError("test")
        assert isinstance(err, ClawMemError)

    def test_index_not_ready_chain(self):
        err = IndexNotReadyError("index not built")
        assert isinstance(err, RetrievalError)

    def test_query_too_long_chain(self):
        err = QueryTooLongError("query > 2000 chars")
        assert isinstance(err, RetrievalError)


class TestErrorUsage:
    """Verify error usage patterns."""

    def test_memory_not_found_contains_id(self):
        err = MemoryNotFoundError("mem_abc")
        assert "mem_abc" in str(err)

    def test_query_too_long_message(self):
        err = QueryTooLongError("Q too long")
        assert "too long" in str(err).lower()

    def test_storage_corrupted(self):
        err = StorageCorruptedError("Checksum mismatch")
        assert "Checksum" in str(err)

    def test_compress_disabled(self):
        err = CompressionDisabledError("Not enabled")
        assert isinstance(err, CompressionError)
        assert isinstance(err, ClawMemError)

    def test_invalid_threshold(self):
        err = InvalidThresholdError("purge_threshold must be 0-1")
        assert isinstance(err, ClawMemError)
