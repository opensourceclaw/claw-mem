"""Tests for critical_rules memory type (v2.13.0)."""

import os
import pytest
import tempfile
from pathlib import Path

from claw_mem.memory_manager import MemoryManager

# Path to the shared critical rules file
CRITICAL_RULES_PATH = os.path.join(os.path.expanduser("~/.claw-mem"), "critical_rules.json")


@pytest.fixture(autouse=True)
def clean_critical_rules():
    """Ensure critical rules are clean before and after each test."""
    backup = None
    if os.path.exists(CRITICAL_RULES_PATH):
        with open(CRITICAL_RULES_PATH, "r") as f:
            backup = f.read()
    if os.path.exists(CRITICAL_RULES_PATH):
        os.remove(CRITICAL_RULES_PATH)
    yield
    if backup is not None:
        os.makedirs(os.path.dirname(CRITICAL_RULES_PATH), exist_ok=True)
        with open(CRITICAL_RULES_PATH, "w") as f:
            f.write(backup)
    elif os.path.exists(CRITICAL_RULES_PATH):
        os.remove(CRITICAL_RULES_PATH)


class TestCriticalRulesStorage:
    """Test critical rule CRUD operations."""

    @pytest.fixture
    def workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def mem(self, workspace):
        mm = MemoryManager(str(workspace), auto_detect=False)
        mm.start_session("test_critical")
        return mm

    def test_store_critical_rule(self, mem):
        """Store a critical rule and verify it's returned."""
        rule_id = mem.store_critical_rule(
            "Never use sessions_spawn for Jarvis tasks",
            metadata={"tool": "sessions_spawn"},
        )
        assert rule_id is not None
        assert len(rule_id) == 8

        rules = mem.get_critical_rules()
        assert len(rules) == 1
        assert rules[0]["text"] == "Never use sessions_spawn for Jarvis tasks"
        assert rules[0]["metadata"]["tool"] == "sessions_spawn"
        assert rules[0]["id"] == rule_id

    def test_get_critical_rules_empty(self, mem):
        """Empty critical rules returns empty list."""
        rules = mem.get_critical_rules()
        assert rules == []

    def test_get_critical_rules_multiple(self, mem):
        """Multiple critical rules are all returned."""
        mem.store_critical_rule("Rule 1")
        mem.store_critical_rule("Rule 2")
        mem.store_critical_rule("Rule 3")

        rules = mem.get_critical_rules()
        assert len(rules) == 3

    def test_delete_critical_rule(self, mem):
        """Delete a critical rule and verify removal."""
        rule_id = mem.store_critical_rule("Rule to delete")

        assert mem.delete_critical_rule(rule_id) is True
        rules = mem.get_critical_rules()
        assert len(rules) == 0

    def test_delete_critical_rule_not_found(self, mem):
        """Deleting a non-existent rule returns False."""
        assert mem.delete_critical_rule("nonexistent") is False

    def test_delete_only_target_rule(self, mem):
        """Deleting one rule does not affect others."""
        r1 = mem.store_critical_rule("Keep me")
        r2 = mem.store_critical_rule("Delete me")

        mem.delete_critical_rule(r2)

        rules = mem.get_critical_rules()
        assert len(rules) == 1
        assert rules[0]["id"] == r1

    def test_critical_rules_persist_across_instances(self, workspace):
        """Critical rules survive Manager re-creation (persisted to disk)."""
        mm1 = MemoryManager(str(workspace), auto_detect=False)
        mm1.start_session("test_persist")
        mm1.store_critical_rule("Persistent rule")

        # Create a new MemoryManager (same workspace)
        mm2 = MemoryManager(str(workspace), auto_detect=False)
        mm2.start_session("test_persist2")

        rules = mm2.get_critical_rules()
        assert len(rules) == 1
        assert rules[0]["text"] == "Persistent rule"


class TestCriticalRulesSearch:
    """Test critical rule integration with search()."""

    @pytest.fixture
    def workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def mem(self, workspace):
        mm = MemoryManager(str(workspace), auto_detect=False)
        mm.start_session("test_search")
        return mm

    def test_search_includes_critical_rules(self, mem):
        """Critical rules are prepended to search results."""
        mem.store_critical_rule("Critical: Always check inbox")

        # Store some normal memories
        mem.store("Normal memory 1", memory_type="episodic")
        mem.store("Normal memory 2", memory_type="episodic")

        results = mem.search("memory", limit=10, include_critical=True)

        # Critical rule should be prepended
        assert any("Critical: Always check inbox" in str(r.get("text", "")) for r in results)

    def test_search_excludes_critical_rules_when_disabled(self, mem):
        """Critical rules not included when include_critical=False."""
        mem.store_critical_rule("Critical: Always check inbox")
        mem.store("Normal memory", memory_type="episodic")

        results = mem.search("memory", limit=10, include_critical=False)

        assert not any("Critical: Always check inbox" in str(r.get("text", "")) for r in results)

    def test_search_critical_rules_prepended_first(self, mem):
        """Critical rules appear at the start of results."""
        mem.store_critical_rule("CRITICAL FIRST")

        # Store enough normal memories
        for i in range(5):
            mem.store(f"Normal memory {i}", memory_type="episodic")

        results = mem.search("memory", limit=10, include_critical=True)

        # First result should be the critical rule
        assert "CRITICAL FIRST" in str(results[0])

    def test_critical_rules_not_counted_toward_limit(self, mem):
        """Critical rules don't count toward the limit parameter."""
        mem.store_critical_rule("Rule 1")
        mem.store_critical_rule("Rule 2")

        for i in range(20):
            mem.store(f"Normal memory {i}", memory_type="episodic")

        results = mem.search("memory", limit=3, include_critical=True)

        # Should have 2 critical rules + 3 search results = 5 total
        assert len(results) == 5
        # First two should be critical rules
        assert "Rule 1" in str(results[0])
        assert "Rule 2" in str(results[1])


class TestCriticalRulesCompression:
    """Test critical rules survive compression."""

    @pytest.fixture
    def workspace(self):
        return Path(tempfile.mkdtemp())

    @pytest.fixture
    def mem(self, workspace):
        mm = MemoryManager(str(workspace), enable_compression=True, auto_detect=False)
        mm.start_session("test_compression")
        return mm

    @pytest.mark.skip(
        reason="Test passes alone, fails in full suite — known test isolation issue (v3.0.0-rc.14)"
    )
    def test_critical_rules_survive_compression(self, mem):
        """Critical rules remain intact after compression."""
        mem.store_critical_rule("Critical rule survives compression")

        # Store many memories to trigger compression
        for i in range(50):
            mem.store(f"Memory content {i}", memory_type="episodic")

        # Force compression
        mem.compress(force=True)

        # Critical rules should still be there
        rules = mem.get_critical_rules()
        assert len(rules) == 1
        assert rules[0]["text"] == "Critical rule survives compression"

    def test_critical_rules_not_affected_by_memory_ops(self, mem):
        """Storing/deleting normal memories doesn't touch critical rules."""
        mem.store_critical_rule("Critical for testing")

        mem.store("Some episodic memory", memory_type="episodic")
        mem.store("Some semantic memory", memory_type="semantic")

        rules = mem.get_critical_rules()
        assert len(rules) == 1
        assert rules[0]["text"] == "Critical for testing"
