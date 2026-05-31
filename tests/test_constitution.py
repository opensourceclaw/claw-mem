"""Tests for ConstitutionStore — three-layer identity persistence (v5.1.0)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from claw_mem import ConstitutionStore, ConstitutionEntry


class TestConstitutionStore:
    """Unit tests for ConstitutionStore."""

    @pytest.fixture
    def workspace(self):
        with tempfile.TemporaryDirectory() as td:
            yield td

    @pytest.fixture
    def store(self, workspace):
        return ConstitutionStore(workspace)

    # ── L0 file sources ──────────────────────────────────────────

    def test_l0_from_agents_md(self, workspace):
        """L0 entries should be loaded from AGENTS.md."""
        (Path(workspace) / "AGENTS.md").write_text(
            "# AGENTS\n\nThis project uses TypeScript.\nFriday is the strategist.\n",
            encoding="utf-8",
        )
        store = ConstitutionStore(workspace)
        entries = store.assemble()
        l0 = [e for e in entries if e["layer"] == 0]
        assert len(l0) >= 2
        contents = {e["content"] for e in l0}
        assert any("TypeScript" in c for c in contents)
        assert any("strategist" in c for c in contents)

    def test_l0_from_identity_md(self, workspace):
        """L0 entries should be loaded from IDENTITY.md."""
        (Path(workspace) / "IDENTITY.md").write_text(
            "# Identity\n\nName: Friday\nRole: AI Assistant\n",
            encoding="utf-8",
        )
        store = ConstitutionStore(workspace)
        entries = store.assemble()
        l0 = [e for e in entries if e["layer"] == 0]
        assert any("Friday" in e["content"] for e in l0)

    def test_l0_empty_workspace_no_crash(self, workspace):
        """Empty workspace should produce no L0 entries (no crash)."""
        store = ConstitutionStore(workspace)
        entries = store.assemble()
        l0 = [e for e in entries if e["layer"] == 0]
        assert len(l0) == 0

    def test_l0_file_not_found_no_crash(self, workspace):
        """Missing files should not crash the loader."""
        store = ConstitutionStore(workspace)
        # No files exist — should be fine
        store._load_l0()
        assert True

    # ── L1 promotions ────────────────────────────────────────────

    def test_promote_to_l1(self, store):
        """Promote content to L1 should create entry and persist to disk."""
        entry_id = store.promote_to_l1("Use TypeScript for all projects")
        assert entry_id is not None
        assert entry_id.startswith("l1_")

        entries = store.assemble()
        l1 = [e for e in entries if e["layer"] == 1]
        assert any(e["content"] == "Use TypeScript for all projects" for e in l1)

    def test_promote_to_l2(self, store):
        """Promote content to L2 should create entry layer=2."""
        entry_id = store.promote_to_l2("Protocol: file-based communication", tags=["protocol"])
        assert entry_id is not None

        entries = store.assemble()
        l2 = [e for e in entries if e["layer"] == 2]
        assert any("file-based" in e["content"] for e in l2)

    def test_promote_duplicate(self, store):
        """Promoting the same content twice should return None."""
        store.promote_to_l1("Rule X")
        result = store.promote_to_l1("Rule X")
        assert result is None

    # ── Delete ───────────────────────────────────────────────────

    def test_delete_l1(self, store):
        """Delete should remove L1 entries."""
        eid = store.promote_to_l1("Temporary rule")
        assert store.delete(eid) is True
        entries = store.assemble()
        assert all(e["id"] != eid for e in entries)

    def test_cannot_delete_l0(self, workspace):
        """L0 (file-system) entries cannot be deleted via API."""
        (Path(workspace) / "AGENTS.md").write_text("Rule from file\n", encoding="utf-8")
        store = ConstitutionStore(workspace)
        entries = store.assemble()
        l0 = [e for e in entries if e["layer"] == 0]
        if l0:
            assert store.delete(l0[0]["id"]) is False

    # ── Scan and suggest ─────────────────────────────────────────

    def test_scan_detects_tech_decision(self, store):
        """Scan should detect technical stack decisions."""
        msgs = [{"content": "Let's use TypeScript for this project", "role": "user"}]
        suggestions = store.scan_and_suggest(msgs)
        assert len(suggestions) >= 1
        assert any("TypeScript" in s["content"] for s in suggestions)
        assert all(s["confidence"] > 0.5 for s in suggestions)

    def test_scan_detects_protocol(self, store):
        """Scan should detect protocol agreements."""
        msgs = [{"content": "Communication protocol is file-based inbox", "role": "assistant"}]
        suggestions = store.scan_and_suggest(msgs)
        assert len(suggestions) >= 1
        assert any("communication" in s["content"].lower() for s in suggestions)

    def test_scan_detects_role(self, store):
        """Scan should detect role definitions."""
        msgs = [{"content": "Friday is responsible for strategy and architecture", "role": "user"}]
        suggestions = store.scan_and_suggest(msgs)
        assert len(suggestions) >= 1
        assert any("Friday" in s["content"] for s in suggestions)

    def test_scan_dedup(self, store):
        """Scan should deduplicate identical suggestions."""
        msgs = [
            {"content": "Let's use TypeScript", "role": "user"},
            {"content": "Let's use TypeScript", "role": "assistant"},
        ]
        suggestions = store.scan_and_suggest(msgs)
        # "Let's use TypeScript" should appear at most once
        ts_count = sum(1 for s in suggestions if "TypeScript" in s["content"])
        assert ts_count <= 1

    def test_scan_skips_existing(self, store):
        """Scan should skip content already in constitution."""
        store.promote_to_l1("Always use TypeScript")
        msgs = [{"content": "Always use TypeScript", "role": "user"}]
        suggestions = store.scan_and_suggest(msgs)
        # "use TypeScript" is already in constitution as part of "Always use TypeScript"
        # The scan extracts "use TypeScript" via regex, not the full sentence
        # So we verify it's caught by the seen check (substring matching)
        ts_suggestions = [s for s in suggestions if "TypeScript" in s["content"]]
        assert len(ts_suggestions) == 0

    # ── Assemble ─────────────────────────────────────────────────

    def test_assemble_sorted_by_layer(self, store):
        """Assemble should return entries sorted L0 → L1 → L2."""
        store.promote_to_l2("L2 rule")
        store.promote_to_l1("L1 rule")
        entries = store.assemble()
        layers = [e["layer"] for e in entries]
        assert layers == sorted(layers)

    def test_assemble_text_format(self, store):
        """assemble_text should return formatted string."""
        store.promote_to_l1("Rule A")
        text = store.assemble_text()
        assert isinstance(text, str)
        assert "Rule A" in text
        assert "[L1]" in text

    # ── Stats ────────────────────────────────────────────────────

    def test_get_stats(self, store):
        """get_stats should return layer counts."""
        store.promote_to_l1("Rule A")
        stats = store.get_stats()
        assert stats["total_entries"] >= 1
        assert stats["by_layer"][1] >= 1

    # ── Persistence ──────────────────────────────────────────────

    def test_persistence_across_instances(self, workspace):
        """L1 entries should survive ConstitutionStore re-creation."""
        store1 = ConstitutionStore(workspace)
        eid = store1.promote_to_l1("Persistent rule")

        store2 = ConstitutionStore(workspace)
        entries = store2.assemble()
        assert any(e["id"] == eid for e in entries)

    def test_invalid_json_file_does_not_crash(self, workspace):
        """Corrupted storage file should not crash loading."""
        l1_dir = Path(workspace) / ".claw-mem" / "constitution"
        l1_dir.mkdir(parents=True, exist_ok=True)
        (l1_dir / "bad_entry.json").write_text("{invalid json!!}", encoding="utf-8")

        store = ConstitutionStore(workspace)
        entries = store.assemble()  # should not crash
        assert isinstance(entries, list)
