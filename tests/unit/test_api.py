"""Tests for claw-mem API module."""

from claw_mem.api.server import ClawMemHandler, create_server
from claw_mem.types import MemoryRecord, MemoryType, SearchResult


class TestCreateServer:
    """Tests for server creation."""

    def test_create_server(self):
        server = create_server("localhost", 0)
        assert server is not None
        server.server_close()


class TestMemoryType:
    """Tests for MemoryType enum."""

    def test_values(self):
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.PROCEDURAL.value == "procedural"


class TestMemoryRecord:
    """Tests for MemoryRecord dataclass."""

    def test_create_record(self):
        record = MemoryRecord(
            id="mem-1",
            content="test content",
            memory_type=MemoryType.SEMANTIC,
            metadata={"source": "test"},
        )
        assert record.id == "mem-1"
        assert record.memory_type == MemoryType.SEMANTIC

    def test_episodic_record(self):
        record = MemoryRecord(
            id="ep-1",
            content="event happened",
            memory_type=MemoryType.EPISODIC,
        )
        assert record.memory_type == MemoryType.EPISODIC

    def test_procedural_record(self):
        record = MemoryRecord(
            id="proc-1",
            content="how to do X",
            memory_type=MemoryType.PROCEDURAL,
        )
        assert record.memory_type == MemoryType.PROCEDURAL


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_defaults(self):
        result = SearchResult()
        assert result.records == []
        assert result.score == 0.0
        assert result.total == 0

    def test_with_results(self):
        records = [
            MemoryRecord("1", "content", MemoryType.SEMANTIC),
        ]
        result = SearchResult(records=records, score=0.9, total=1)
        assert result.total == 1
        assert result.score == 0.9
