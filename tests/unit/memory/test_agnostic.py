"""Tests for claw_mem.memory.agnostic (AgentAgnosticMemory)."""

import pytest
from claw_mem.memory.agnostic import AgentAgnosticMemory, MemoryRecord


class TestMemoryRecord:
    def test_create(self):
        r = MemoryRecord(
            id="r1", agent_id="a1", memory_type="episodic",
            content="hello", tags=["greeting"], timestamp=100.0,
        )
        assert r.id == "r1"
        assert r.agent_id == "a1"
        assert r.memory_type == "episodic"
        assert r.source == "local"


class TestToSharedFormat:
    def test_basic_conversion(self):
        record = AgentAgnosticMemory.to_shared_format(
            {"content": "Hello world", "tags": ["greeting"]},
            agent_id="agent1",
        )
        assert isinstance(record, MemoryRecord)
        assert record.agent_id == "agent1"
        assert record.content == "Hello world"
        assert "greeting" in record.tags
        assert record.source == "shared"

    def test_empty_content_raises(self):
        with pytest.raises(ValueError):
            AgentAgnosticMemory.to_shared_format(
                {"content": "   "}, agent_id="a1",
            )

    def test_pii_filtering(self):
        record = AgentAgnosticMemory.to_shared_format(
            {"content": "Contact me at user@example.com or call 555-123-4567"},
            agent_id="a1",
        )
        assert "user@example.com" not in record.content
        assert "[EMAIL]" in record.content
        assert "555-123-4567" not in record.content
        assert "[PHONE]" in record.content

    def test_pii_api_key_filtered(self):
        record = AgentAgnosticMemory.to_shared_format(
            {"content": "My key is sk-abc123def456ghi789jkl"},
            agent_id="a1",
        )
        assert "sk-" not in record.content
        assert "[API_KEY]" in record.content


class TestFromSharedFormat:
    def test_roundtrip(self):
        original = {"content": "Hello", "tags": ["a", "b"]}
        record = AgentAgnosticMemory.to_shared_format(original, "a1")
        back = AgentAgnosticMemory.from_shared_format(record)
        assert back["content"] == original["content"]
        assert set(back["tags"]) == set(original["tags"])
        assert back["agent_id"] == "a1"
        assert back["source"] == "shared"


class TestCreateFilter:
    def test_empty_filter(self):
        f = AgentAgnosticMemory.create_filter()
        assert f == {}

    def test_full_filter(self):
        f = AgentAgnosticMemory.create_filter(
            agent_id="a1",
            memory_type="episodic",
            tags=["work"],
            since=100.0,
            until=200.0,
            min_confidence=0.8,
        )
        assert f["agent_id"] == "a1"
        assert f["memory_type"] == "episodic"
        assert f["tags"] == ["work"]
        assert f["since"] == 100.0
        assert f["until"] == 200.0
        assert f["min_confidence"] == 0.8

    def test_partial_filter(self):
        f = AgentAgnosticMemory.create_filter(memory_type="semantic")
        assert f["memory_type"] == "semantic"
        assert "agent_id" not in f
