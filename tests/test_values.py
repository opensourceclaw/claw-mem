#!/usr/bin/env python3
"""
Tests for UserValueStore
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from claw_mem.values import UserValue, UserValueStore


class TestUserValue:
    """Test UserValue dataclass"""

    def test_creation(self):
        """Test UserValue creation"""
        uv = UserValue(user_id="test-user")

        assert uv.user_id == "test-user"
        assert uv.principles == []
        assert uv.preferences == {}
        assert uv.red_lines == []

    def test_to_dict(self):
        """Test to_dict conversion"""
        uv = UserValue(
            user_id="test",
            principles=["test principle"],
            preferences={"key": "value"},
            red_lines=["no lying"]
        )

        d = uv.to_dict()
        assert d["user_id"] == "test"
        assert d["principles"] == ["test principle"]
        assert d["preferences"] == {"key": "value"}

    def test_from_dict(self):
        """Test from_dict creation"""
        data = {
            "user_id": "test",
            "principles": ["p1"],
            "preferences": {"k": "v"},
            "red_lines": ["r1"],
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
        }

        uv = UserValue.from_dict(data)
        assert uv.user_id == "test"
        assert uv.principles == ["p1"]


class TestUserValueStore:
    """Test UserValueStore"""

    @pytest.fixture
    def store(self):
        """Create temporary store"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield UserValueStore(storage_path=Path(tmpdir))

    def test_save_principle(self, store):
        """Test save principle"""
        result = store.save_principle("user1", "Be honest")

        assert "Be honest" in result.principles

    def test_save_duplicate_principle(self, store):
        """Test save duplicate principle"""
        store.save_principle("user1", "Be honest")
        result = store.save_principle("user1", "Be honest")

        # Should only have one
        assert result.principles.count("Be honest") == 1

    def test_save_preference(self, store):
        """Test save preference"""
        result = store.save_preference("user1", "language", "Chinese")

        assert result.preferences["language"] == "Chinese"

    def test_save_red_line(self, store):
        """Test save red line"""
        result = store.save_red_line("user1", "No violence")

        assert "No violence" in result.red_lines

    def test_get_user_values(self, store):
        """Test get user values"""
        store.save_principle("user1", "Test principle")
        store.save_preference("user1", "key", "value")

        result = store.get_user_values("user1")

        assert result is not None
        assert "Test principle" in result.principles
        assert result.preferences["key"] == "value"

    def test_get_nonexistent_user(self, store):
        """Test get nonexistent user"""
        result = store.get_user_values("nonexistent")
        assert result is None

    def test_delete_principle(self, store):
        """Test delete principle"""
        store.save_principle("user1", "To delete")
        result = store.delete_principle("user1", "To delete")

        assert "To delete" not in result.principles

    def test_delete_red_line(self, store):
        """Test delete red line"""
        store.save_red_line("user1", "To delete")
        result = store.delete_red_line("user1", "To delete")

        assert "To delete" not in result.red_lines

    def test_delete_preference(self, store):
        """Test delete preference"""
        store.save_preference("user1", "key", "value")
        result = store.delete_preference("user1", "key")

        assert "key" not in result.preferences

    def test_list_users(self, store):
        """Test list users"""
        store.save_principle("user1", "p1")
        store.save_principle("user2", "p2")

        users = store.list_users()
        assert "user1" in users
        assert "user2" in users
