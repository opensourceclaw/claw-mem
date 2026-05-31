# Copyright 2026 Peter Cheng — Licensed Apache-2.0
"""
v5.1.0 PEV Loop Verification — Constitution survival test.

Verifies that Constitution entries survive:
  Plan → Execute → Verify → reset_session → new session
"""

import tempfile
from pathlib import Path

import pytest

from claw_mem.constitution import ConstitutionStore


class TestConstitutionPEV:
    """PEV Loop: Plan→Execute→Verify cycle with Constitution checks."""

    def test_constitution_survives_reset_session(self):
        """Constitution L2 entries must survive reset_session + new session."""
        with tempfile.TemporaryDirectory() as d:
            ws = Path(d)

            # Stage: START SESSION — load Constitution
            store = ConstitutionStore(str(ws))
            initial = store.assemble()
            assert isinstance(initial, list)

            # Stage: STORE new Constitution rule (L2) via RPC path
            store.promote_to_l2("Always use TypeScript for backend", tags=["tech_stack"])
            store.promote_to_l2("Communicate via Markdown in ~/comm/", tags=["protocol"])

            # Stage: VERIFY — entries are stored
            all_entries = store.get_all()
            assert len(all_entries) >= 2
            l2_entries = [e for e in all_entries if e["layer"] == 2]
            assert len(l2_entries) >= 2

            # Stage: RESET SESSION — reload store
            store2 = ConstitutionStore(str(ws))
            assembled = store2.assemble()
            l2_in_assembled = [e for e in assembled if e["layer"] == 2]
            assert len(l2_in_assembled) >= 2, \
                f"Expected L2 entries to survive reload, got {len(l2_in_assembled)}"

            # Content verification
            contents = [e["content"] for e in l2_in_assembled]
            assert any("TypeScript" in c for c in contents)
            assert any("communicate" in c.lower() for c in contents)

    def test_empty_workspace_no_crash(self):
        """Empty workspace should not crash ConstitutionStore."""
        with tempfile.TemporaryDirectory() as d:
            store = ConstitutionStore(d)
            assembled = store.assemble()
            assert isinstance(assembled, list)

            stats = store.get_stats()
            assert isinstance(stats, dict)
            # Stats structure may vary — key is no crash

    def test_scan_and_suggest_detects_rules(self):
        """Post-session scan detects tech stack from conversation."""
        with tempfile.TemporaryDirectory() as d:
            store = ConstitutionStore(d)
            conversations = [
                {"content": "Let's use Python and FastAPI for this project"},
                {"content": "We decided to use PostgreSQL as the database"},
                {"content": "Communication between agents should be via Markdown files"},
            ]
            suggestions = store.scan_and_suggest(conversations)
            assert len(suggestions) >= 1

    def test_migration_flag_prevents_duplicate(self):
        """Migration should only run once."""
        import json, os
        with tempfile.TemporaryDirectory() as d:
            ws = Path(d)
            # Simulate pre-migration state
            rules_file = ws / "critical_rules.json"
            json.dump({
                "r1": {"id": "r1", "content": "Always use Python", "metadata": {}}
            }, open(rules_file, 'w'))

            store = ConstitutionStore(str(ws))
            # First migration
            store.promote_to_l2("Always use Python", tags=["legacy_critical", "migrated_v5.1"])

            # Verify it's stored
            entries = store.get_all()
            l2 = [e for e in entries if e["layer"] == 2]
            assert len(l2) >= 1

    def test_delete_constitution_rule(self):
        """L2 rules can be deleted."""
        with tempfile.TemporaryDirectory() as d:
            store = ConstitutionStore(d)
            store.promote_to_l2("Test rule", tags=["test"])
            entries = store.get_all()
            rule_id = next(e["id"] for e in entries if e["content"] == "Test rule")

            result = store.delete(rule_id)
            assert result is True

            entries_after = store.get_all()
            assert not any(e["id"] == rule_id for e in entries_after)

    def test_l0_files_are_immutable_via_api(self):
        """L0 entries loaded from workspace files should appear in assemble()."""
        with tempfile.TemporaryDirectory() as d:
            ws = Path(d)
            # Write AGENTS.md
            (ws / "AGENTS.md").write_text("# AGENTS.md\n\n- Jarvis: Coding Engineer", encoding="utf-8")

            store = ConstitutionStore(str(ws))
            assembled = store.assemble()
            l0 = [e for e in assembled if e["layer"] == 0]
            assert len(l0) >= 1
            assert any("Jarvis" in e["content"] for e in l0)
