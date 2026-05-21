#!/usr/bin/env python3
# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Coverage tests for memory_manager.py -- targets:
1. Compression (compress, manual_compress, get_compression_stats, compression_spectrum)
2. CMS/Perception Layer (get_capacity_stats, get_importance_scores, get_important_memories)
3. Session recovery (save_snapshot, recover_session, switch_context, list_snapshots, save_snapshots)
4. Critical rules (get_critical_rules, store_critical_rule, delete_critical_rule)
5. Gating (configure_gating, check_write_gate)
6. Edge cases for store / search / get methods
"""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch, call

from claw_mem.memory_manager import MemoryManager


# =========================================================================
# Helper: build an MM whose expensive lazy properties are all replaced with
# MagicMock instances. We patch the constructors of all heavy dependencies
# so __init__ runs fast, then override lazy properties on the instance.
# =========================================================================

def mock_mm():
    """Create a MemoryManager with all I/O dependencies mocked."""
    patches = [
        patch("claw_mem.memory_manager.WorkingMemoryCache"),
        patch("claw_mem.memory_manager.InMemoryIndex"),
        patch.object(MemoryManager, "_load_critical_rules", return_value=None),
    ]
    for p in patches:
        p.start()
    mm = MemoryManager("/tmp/test_mock_mm")
    for p in patches:
        p.stop()

    # Now replace all lazy properties with MagicMock
    _mock_props(mm)
    return mm


def _mock_props(mm):
    """Replace every lazy-load property on *mm* with a MagicMock."""
    # Storage
    mm._episodic = MagicMock()
    mm._semantic = MagicMock()
    mm._procedural = MagicMock()
    # Validator / Audit / Checkpoint
    mm._validator = MagicMock()
    mm._validator.validate.return_value = True
    mm._audit = MagicMock()
    mm._checkpoint = MagicMock()
    # Gating
    mm._gating = MagicMock()
    # Compressor
    mm._compressor = MagicMock()
    # Graph
    mm._multi_graph = None
    # Three-tier
    mm._three_tier_retriever = MagicMock()
    # Retriever (keyword)
    mm._retriever = MagicMock()
    # CMS
    mm._cms_capacity = None
    mm._cms_importance = None
    mm._cms_summarizer = None
    mm._cms_deduplicator = None
    mm._cms_strategy = None
    # Snapshots
    mm._cms_snap = MagicMock()
    # Performance monitor
    mm._performance_monitor = None
    # Ground truth
    mm._ground_truth = None
    # Query cache
    mm._query_cache = None
    # Search stats
    mm._search_stats = None
    # Synonym expander
    mm._synonym_expander = None
    # Decay
    mm._decay_controller = None
    # Index
    mm.index = MagicMock()
    mm.index.built = True
    # Working cache
    mm.working_cache = MagicMock()
    mm.working_cache.size.return_value = 0
    # Working memory
    mm.working_memory = []
    # Session
    mm.session_id = "test_session"


# =========================================================================
# 1. Compression-related methods
# =========================================================================

class TestCompression:
    def test_compress_disabled_returns_none(self):
        mm = mock_mm()
        mm.enable_compression = False
        assert mm.compress(force=True) is None

    def test_compress_not_enough_memories_returns_none(self):
        mm = mock_mm()
        mm.enable_compression = True
        mm.episodic.get_recent.return_value = []
        mm.semantic.get_all.return_value = []
        mm.procedural.get_all.return_value = []
        mm._compression_config.max_memories = 1000
        assert mm.compress(force=False) is None

    def test_compress_force_success(self):
        mm = mock_mm()
        mm.enable_compression = True
        mm.episodic.get_recent.return_value = [{"id": "1", "content": "mem1"}]
        mm.semantic.get_all.return_value = []
        mm.procedural.get_all.return_value = []
        fake_result = MagicMock()
        mm.compressor.compress.return_value = fake_result
        result = mm.compress(force=True)
        mm.compressor.compress.assert_called_once()
        assert result is fake_result

    def test_compress_natural_trigger(self):
        mm = mock_mm()
        mm.enable_compression = True
        # Return many memories, exceeding threshold
        mm.episodic.get_recent.return_value = [{"id": str(i)} for i in range(10)]
        mm.semantic.get_all.return_value = [{"id": str(i)} for i in range(10)]
        mm.procedural.get_all.return_value = [{"id": str(i)} for i in range(10)]
        mm._compression_config.max_memories = 5
        fake_result = MagicMock()
        mm.compressor.compress.return_value = fake_result
        result = mm.compress(force=False)
        assert result is fake_result

    def test_get_compression_config_returns_dict(self):
        mm = mock_mm()
        cfg = mm.get_compression_config()
        assert isinstance(cfg, dict)

    def test_get_compression_history(self):
        mm = mock_mm()
        mm.compressor.compression_count = 3
        mm.compressor.operation_count = 10
        mm.compressor.last_compression_idx = 2
        hist = mm.get_compression_history()
        assert hist == {"compression_count": 3, "operation_count": 10, "last_compression_idx": 2}

    def test_get_compression_stats_enabled(self):
        mm = mock_mm()
        mm.enable_compression_spectrum = True
        mm._compression_spectrum = MagicMock()
        mm._compression_spectrum.get_stats.return_value = {"compressed": 5}
        stats = mm.get_compression_stats()
        assert stats == {"compressed": 5}

    def test_get_compression_stats_disabled(self):
        mm = mock_mm()
        mm.enable_compression_spectrum = False
        mm._compression_spectrum = None
        stats = mm.get_compression_stats()
        assert stats == {"enabled": False}

    def test_manual_compress_disabled(self):
        mm = mock_mm()
        mm.enable_compression_spectrum = False
        mm._compression_spectrum = None
        assert mm.manual_compress("mem_1") is None

    def test_manual_compress_success(self):
        mm = mock_mm()
        mm.enable_compression_spectrum = True
        mm._compression_spectrum = MagicMock()
        fake_result = MagicMock()
        fake_result.compressed = True
        mm._compression_spectrum.record_access.return_value = fake_result
        result = mm.manual_compress("mem_1")
        mm._compression_spectrum.record_access.assert_called_once_with("mem_1")
        assert result is not None

    def test_manual_compress_result_none(self):
        mm = mock_mm()
        mm.enable_compression_spectrum = True
        mm._compression_spectrum = MagicMock()
        mm._compression_spectrum.record_access.return_value = None
        assert mm.manual_compress("mem_1") is None


# =========================================================================
# 2. CMS / Perception Layer methods
# =========================================================================

class TestCMS:
    def test_get_capacity_stats_disabled(self):
        mm = mock_mm()
        mm._cms_capacity = None
        assert mm.get_capacity_stats() is None

    def test_get_capacity_stats_enabled(self):
        mm = mock_mm()
        fake_cap = MagicMock()
        fake_stats = MagicMock()
        fake_stats.to_dict.return_value = {"utilization": 0.6, "memory_count": 500}
        fake_cap.get_stats.return_value = fake_stats
        mm._cms_capacity = fake_cap
        assert mm.get_capacity_stats() == {"utilization": 0.6, "memory_count": 500}

    def test_get_importance_scores_disabled(self):
        mm = mock_mm()
        mm._cms_importance = None
        assert mm.get_importance_scores(["m1"]) is None

    def test_get_importance_scores_enabled(self):
        mm = mock_mm()
        fake_imp = MagicMock()
        s1, s2 = MagicMock(), MagicMock()
        s1.to_dict.return_value = {"memory_id": "m1", "score": 0.9}
        s2.to_dict.return_value = {"memory_id": "m2", "score": 0.3}
        fake_imp.evaluate_batch.return_value = {"m1": s1, "m2": s2}
        mm._cms_importance = fake_imp
        result = mm.get_importance_scores(["m1", "m2"])
        assert result == {"m1": {"memory_id": "m1", "score": 0.9}, "m2": {"memory_id": "m2", "score": 0.3}}

    def test_get_importance_scores_empty(self):
        mm = mock_mm()
        fake_imp = MagicMock()
        fake_imp.evaluate_batch.return_value = {}
        mm._cms_importance = fake_imp
        assert mm.get_importance_scores([]) == {}

    def test_get_important_memories_disabled(self):
        mm = mock_mm()
        mm._cms_importance = None
        assert mm.get_important_memories(threshold=0.5) is None

    def test_get_important_memories_enabled(self):
        mm = mock_mm()
        fake_imp = MagicMock()
        r1, r2 = MagicMock(), MagicMock()
        r1.to_dict.return_value = {"memory_id": "m1", "score": 0.9}
        r2.to_dict.return_value = {"memory_id": "m2", "score": 0.7}
        fake_imp.get_important_memories.return_value = [r1, r2]
        mm._cms_importance = fake_imp
        result = mm.get_important_memories(threshold=0.5, limit=50)
        assert len(result) == 2
        assert result[0] == {"memory_id": "m1", "score": 0.9}
        fake_imp.get_important_memories.assert_called_once_with(0.5, 50)

    def test_generate_summary_disabled(self):
        mm = mock_mm()
        mm._cms_summarizer = None
        assert mm.generate_summary("s1") is None

    def test_generate_summary_with_memories(self):
        mm = mock_mm()
        fake_sum = MagicMock()
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"summary": "test"}
        fake_sum.generate.return_value = fake_result
        mm._cms_summarizer = fake_sum
        result = mm.generate_summary("s1", memories=[{"id": "m1"}], strategy="key_points")
        assert result == {"summary": "test"}
        fake_sum.generate.assert_called_once_with("s1", [{"id": "m1"}], "key_points")

    def test_generate_summary_no_memories(self):
        mm = mock_mm()
        fake_sum = MagicMock()
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"summary": "empty"}
        fake_sum.generate.return_value = fake_result
        mm._cms_summarizer = fake_sum
        result = mm.generate_summary("s1")
        assert result == {"summary": "empty"}
        fake_sum.generate.assert_called_once_with("s1", [], "key_points")

    def test_deduplicate_memories_disabled(self):
        mm = mock_mm()
        mm._cms_deduplicator = None
        assert mm.deduplicate_memories(["m1"]) is None

    def test_deduplicate_memories_success(self):
        mm = mock_mm()
        fake_dedup = MagicMock()
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"dedup_count": 2, "reduction_ratio": 0.3}
        fake_dedup.deduplicate.return_value = fake_result
        mm._cms_deduplicator = fake_dedup
        result = mm.deduplicate_memories(["m1", "m2"], threshold=0.9)
        assert result == {"dedup_count": 2, "reduction_ratio": 0.3}
        assert fake_dedup._similarity_threshold == 0.9
        fake_dedup.deduplicate.assert_called_once_with(["m1", "m2"])

    def test_compress_session_disabled(self):
        mm = mock_mm()
        mm.enable_cms = False
        assert mm.compress_session("s1") is None

    def test_compress_session_no_plan(self):
        mm = mock_mm()
        mm.enable_cms = True
        # Provide a capacity monitor
        fake_cap = MagicMock()
        fake_stats = MagicMock()
        fake_stats.to_dict.return_value = {"utilization": 0.5}
        fake_cap.get_stats.return_value = fake_stats
        mm._cms_capacity = fake_cap
        fake_sel = MagicMock()
        fake_sel.select.return_value = None
        mm._cms_strategy = fake_sel
        assert mm.compress_session("s1") is None

    def test_compress_session_auto_strategy(self):
        mm = mock_mm()
        mm.enable_cms = True
        # Capacity monitor returning stats
        fake_cap = MagicMock()
        fake_stats = MagicMock()
        fake_stats.to_dict.return_value = {"utilization": 0.9}
        fake_cap.get_stats.return_value = fake_stats
        mm._cms_capacity = fake_cap
        # Strategy selector returning a plan
        fake_sel = MagicMock()
        fake_plan = MagicMock()
        fake_plan.suggested_actions = ["summarize", "deduplicate"]
        fake_sel.select.return_value = fake_plan
        mm._cms_strategy = fake_sel
        # Summarizer
        fake_sum = MagicMock()
        fake_sum_result = MagicMock()
        fake_sum_result.to_dict.return_value = {"text": "summary"}
        fake_sum.generate.return_value = fake_sum_result
        mm._cms_summarizer = fake_sum
        # Deduplicator
        fake_dedup = MagicMock()
        fake_dedup_result = MagicMock()
        fake_dedup_result.to_dict.return_value = {"dedup_count": 1}
        fake_dedup_result.reduction_ratio = 0.2
        fake_dedup.deduplicate.return_value = fake_dedup_result
        mm._cms_deduplicator = fake_dedup
        # Gather session memories
        mm._episodic = MagicMock()
        mm._episodic.get_all.return_value = [{"id": "m1", "content": "hello world"}]

        with patch("claw_mem.memory_manager.CompressionResult") as MockCR:
            fake_cr = MagicMock()
            fake_cr.to_dict.return_value = {
                "session_id": "s1", "reduction_ratio": 0.5,
            }
            MockCR.return_value = fake_cr
            result = mm.compress_session("s1", strategy="auto")
        assert result is not None
        assert "reduction_ratio" in result
        fake_sel.select.assert_called_once_with(0.9)

    def test_compress_session_aggressive(self):
        mm = mock_mm()
        mm.enable_cms = True
        fake_cap = MagicMock()
        fake_stats = MagicMock()
        fake_stats.to_dict.return_value = {"utilization": 0.5}
        fake_cap.get_stats.return_value = fake_stats
        mm._cms_capacity = fake_cap
        fake_sel = MagicMock()
        fake_plan = MagicMock()
        fake_plan.suggested_actions = ["summarize"]
        fake_sel.select.return_value = fake_plan
        mm._cms_strategy = fake_sel
        fake_sum = MagicMock()
        fake_sum_result = MagicMock()
        fake_sum_result.to_dict.return_value = {"text": "aggro"}
        fake_sum.generate.return_value = fake_sum_result
        mm._cms_summarizer = fake_sum
        mm._cms_deduplicator = None  # skip dedup
        mm._episodic = MagicMock()
        mm._episodic.get_all.return_value = [{"id": "m1", "content": "hello"}]

        with patch("claw_mem.memory_manager.CompressionResult") as MockCR:
            fake_cr = MagicMock()
            fake_cr.to_dict.return_value = {
                "session_id": "s1", "reduction_ratio": 0.8,
            }
            MockCR.return_value = fake_cr
            result = mm.compress_session("s1", strategy="aggressive")
        assert result is not None
        # aggressive should pass 0.99 to select
        fake_sel.select.assert_called_once()
        args, _ = fake_sel.select.call_args
        assert args[0] == 0.99

    def test_compress_session_balanced(self):
        mm = mock_mm()
        mm.enable_cms = True
        fake_cap = MagicMock()
        fake_stats = MagicMock()
        fake_stats.to_dict.return_value = {"utilization": 0.5}
        fake_cap.get_stats.return_value = fake_stats
        mm._cms_capacity = fake_cap
        fake_sel = MagicMock()
        fake_plan = MagicMock()
        fake_plan.suggested_actions = []
        fake_sel.select.return_value = fake_plan
        mm._cms_strategy = fake_sel
        mm._episodic = MagicMock()
        mm._episodic.get_all.return_value = []

        with patch("claw_mem.memory_manager.CompressionResult") as MockCR:
            fake_cr = MagicMock()
            fake_cr.to_dict.return_value = {
                "session_id": "s1", "reduction_ratio": 0.3,
            }
            MockCR.return_value = fake_cr
            result = mm.compress_session("s1", strategy="balanced")
        assert result is not None


# =========================================================================
# 3. Session Recovery Methods
# =========================================================================

class TestSessionRecovery:
    def test_save_snapshot_empty(self):
        mm = mock_mm()
        mm._cms_snap.save.return_value = "snap_abc"
        mm._episodic = MagicMock()
        mm._episodic.get_all.return_value = []
        assert mm.save_snapshot("s1") == "snap_abc"
        mm._cms_snap.save.assert_called_once_with("s1", state="active", memory_ids=[])

    def test_save_snapshot_with_memories(self):
        mm = mock_mm()
        mm._cms_snap.save.return_value = "snap_xyz"
        mm._episodic = MagicMock()
        mm._episodic.get_all.return_value = [{"id": "m1"}, {"id": "m2"}]
        result = mm.save_snapshot("s1")
        assert result == "snap_xyz"
        mm._cms_snap.save.assert_called_once_with("s1", state="active", memory_ids=["m1", "m2"])

    def test_load_snapshot_exists(self):
        mm = mock_mm()
        fake_snap = MagicMock()
        fake_snap.to_dict.return_value = {"snapshot_id": "s1", "state": "active"}
        mm._cms_snap.load.return_value = fake_snap
        assert mm.load_snapshot("s1") == {"snapshot_id": "s1", "state": "active"}
        mm._cms_snap.load.assert_called_once_with("s1")

    def test_load_snapshot_not_found(self):
        mm = mock_mm()
        mm._cms_snap.load.return_value = None
        assert mm.load_snapshot("nonexistent") is None

    def test_list_snapshots(self):
        mm = mock_mm()
        item1, item2 = MagicMock(), MagicMock()
        item1.snapshot_id = "s1"
        item1.timestamp.isoformat.return_value = "2026-01-01T00:00:00"
        item1.state = "active"
        item1.size_bytes = 1024
        item2.snapshot_id = "s2"
        item2.timestamp.isoformat.return_value = "2026-01-02T00:00:00"
        item2.state = "archived"
        item2.size_bytes = 2048
        mm._cms_snap.list.return_value = [item1, item2]
        result = mm.list_snapshots("s1")
        assert len(result) == 2
        assert result[0]["snapshot_id"] == "s1"
        assert result[1]["state"] == "archived"
        mm._cms_snap.list.assert_called_once_with("s1")

    def test_list_snapshots_empty(self):
        mm = mock_mm()
        mm._cms_snap.list.return_value = []
        assert mm.list_snapshots("s1") == []

    def test_delete_snapshot_true(self):
        mm = mock_mm()
        mm._cms_snap.delete.return_value = True
        assert mm.delete_snapshot("s1") is True
        mm._cms_snap.delete.assert_called_once_with("s1")

    def test_delete_snapshot_false(self):
        mm = mock_mm()
        mm._cms_snap.delete.return_value = False
        assert mm.delete_snapshot("nonexistent") is False

    @patch("claw_mem.memory_manager.SessionStateMachine")
    def test_get_session_state(self, MockSSM):
        mm = mock_mm()
        instance = MockSSM.return_value
        instance.get_current_state.return_value = "active"
        assert mm.get_session_state("s1") == "active"
        instance.get_current_state.assert_called_once_with("s1")

    @patch("claw_mem.memory_manager.SessionStateMachine")
    def test_set_session_state(self, MockSSM):
        mm = mock_mm()
        instance = MockSSM.return_value
        mm.set_session_state("s1", "archived")
        instance.set_state.assert_called_once_with("s1", "archived")

    @patch("claw_mem.memory_manager.ContextSwitcher")
    def test_switch_context(self, MockCS):
        mm = mock_mm()
        fake_switcher = MockCS.return_value
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"switched": True}
        fake_switcher.switch.return_value = fake_result
        result = mm.switch_context("from_s", "to_s")
        assert result == {"switched": True}
        MockCS.assert_called_once_with(importance_evaluator=mm.cms_importance, memory_manager=mm)
        fake_switcher.switch.assert_called_once_with("from_s", "to_s", "preserve_important")

    @patch("claw_mem.memory_manager.RecoveryMechanism")
    def test_recover_session(self, MockRM):
        mm = mock_mm()
        fake_rec = MockRM.return_value
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"recovered": True}
        fake_rec.recover.return_value = fake_result
        result = mm.recover_session("s1", snapshot_id="snap1")
        assert result == {"recovered": True}
        MockRM.assert_called_once_with(snapshot_storage=mm.cms_snap_storage, memory_manager=mm)
        fake_rec.recover.assert_called_once_with("s1", "snap1", "latest")

    @patch("claw_mem.memory_manager.RecoveryMechanism")
    def test_recover_session_default(self, MockRM):
        mm = mock_mm()
        fake_rec = MockRM.return_value
        fake_result = MagicMock()
        fake_result.to_dict.return_value = {"recovered": True}
        fake_rec.recover.return_value = fake_result
        result = mm.recover_session("s1")
        assert result == {"recovered": True}
        fake_rec.recover.assert_called_once_with("s1", None, "latest")


# =========================================================================
# 4. Critical Rules
# =========================================================================

class TestCriticalRules:
    def test_store_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            rule_id = mm.store_critical_rule("Always back up data", metadata={"priority": "high"})
            assert isinstance(rule_id, str) and len(rule_id) == 8
            rules = mm.get_critical_rules()
            assert len(rules) == 1
            assert rules[0]["content"] == "Always back up data"
            assert rules[0]["metadata"]["priority"] == "high"
            assert rules[0]["memory_type"] == "critical"

    def test_store_multiple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            id1 = mm.store_critical_rule("Rule one")
            id2 = mm.store_critical_rule("Rule two")
            rules = mm.get_critical_rules()
            assert len(rules) == 2
            contents = {r["id"]: r["content"] for r in rules}
            assert contents[id1] == "Rule one"
            assert contents[id2] == "Rule two"

    def test_delete_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            rule_id = mm.store_critical_rule("Delete me")
            assert len(mm.get_critical_rules()) == 1
            assert mm.delete_critical_rule(rule_id) is True
            assert len(mm.get_critical_rules()) == 0

    def test_delete_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            assert mm.delete_critical_rule("nonexistent") is False

    def test_persist_across_instances(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm1 = MemoryManager(tmpdir)
            rule_id = mm1.store_critical_rule("Persistent rule")
            mm2 = MemoryManager(tmpdir)
            rules = mm2.get_critical_rules()
            assert len(rules) == 1
            assert rules[0]["id"] == rule_id

    def test_empty_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            assert mm.get_critical_rules() == []

    def test_store_no_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            mm.store_critical_rule("No metadata")
            rules = mm.get_critical_rules()
            assert rules[0]["metadata"] == {}

    def test_delete_nonexistent_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            # Should not raise
            assert mm.delete_critical_rule("") is False

    def test_repr(self):
        """__repr__ returns expected format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mm = MemoryManager(tmpdir)
            mm.session_id = "sess1"
            r = repr(mm)
            assert "MemoryManager" in r
            assert "workspace" in r
            assert "sess1" in r


# =========================================================================
# 5. Gating-related tests
# =========================================================================

class TestGating:
    def test_store_with_gating_cold_skips_index(self):
        mm = mock_mm()
        mm.enable_gating = True
        mm.session_id = "s1"
        mm._gating = MagicMock()
        fake_result = MagicMock()
        fake_result.tier = "cold"
        fake_result.salience_score = 0.3
        fake_result.stored = True
        mm._gating.write.return_value = fake_result
        mm.validator.validate.return_value = True

        assert mm.store("Low importance", memory_type="episodic") is True
        mm.index.add_memory.assert_not_called()

    def test_store_with_gating_hot_updates_index(self):
        mm = mock_mm()
        mm.enable_gating = True
        mm.session_id = "s1"
        mm._gating = MagicMock()
        fake_result = MagicMock()
        fake_result.tier = "hot"
        fake_result.salience_score = 0.9
        fake_result.stored = True
        mm._gating.write.return_value = fake_result
        mm.validator.validate.return_value = True

        assert mm.store("High importance", memory_type="episodic") is True
        mm.index.add_memory.assert_called_once()

    def test_store_gating_logs_audit(self):
        mm = mock_mm()
        mm.enable_gating = True
        mm.session_id = "s1"
        mm._gating = MagicMock()
        fake_result = MagicMock()
        fake_result.tier = "warm"
        fake_result.salience_score = 0.6
        fake_result.stored = True
        mm._gating.write.return_value = fake_result
        mm.validator.validate.return_value = True

        mm.store("Gated memory", memory_type="episodic")
        # Should log gating_decision
        gating_calls = [c for c in mm._audit.log.call_args_list if c[0][0] == "gating_decision"]
        assert len(gating_calls) >= 1

    def test_get_gating_stats_enabled(self):
        mm = mock_mm()
        mm.enable_gating = True
        mm._gating = MagicMock()
        mm._gating.get_stats.return_value = {"total_writes": 10}
        assert mm.get_gating_stats() == {"total_writes": 10}

    def test_get_gating_stats_disabled(self):
        mm = mock_mm()
        mm.enable_gating = False
        mm._gating = None
        assert mm.get_gating_stats() is None


# =========================================================================
# 6. Edge cases for store / search / get
# =========================================================================

class TestStoreEdgeCases:
    def test_store_empty_content_raises(self):
        mm = mock_mm()
        mm.session_id = "s1"
        with pytest.raises(ValueError, match="Content cannot be empty"):
            mm.store("")
        with pytest.raises(ValueError, match="Content cannot be empty"):
            mm.store("   ")

    def test_store_invalid_type_raises(self):
        mm = mock_mm()
        mm.session_id = "s1"
        with pytest.raises(ValueError, match="Invalid memory_type"):
            mm.store("test", memory_type="unknown")

    def test_store_validation_fails(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm.validator.validate.return_value = False
        assert mm.store("bad content") is False

    def test_store_with_tags_and_metadata(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm.validator.validate.return_value = True
        result = mm.store("data", memory_type="semantic", tags=["tag1"], metadata={"k": "v"})
        assert result is True
        mm._semantic.store.assert_called_once()

    def test_store_update_index_false(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm.validator.validate.return_value = True
        mm.store("no index", memory_type="episodic", update_index=False)
        mm.index.add_memory.assert_not_called()


class TestSearchEdgeCases:
    def test_search_empty_query_raises(self):
        mm = mock_mm()
        mm.session_id = "s1"
        with pytest.raises(ValueError, match="Query cannot be empty"):
            mm.search("")
        with pytest.raises(ValueError, match="Query cannot be empty"):
            mm.search("   ")

    def test_search_query_too_long_raises(self):
        mm = mock_mm()
        mm.session_id = "s1"
        with pytest.raises(Exception, match="exceeds 2000"):
            mm.search("x" * 2001)

    def test_search_limit_clamped(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm._search_stats = None
        mm._query_cache = None
        mm.episodic.get_recent.return_value = []
        mm.semantic.get_all.return_value = []
        mm.procedural.get_all.return_value = []
        mm.retriever.search.return_value = []
        results = mm.search("test", limit=0, mode="keyword")
        assert isinstance(results, list)

    def test_search_with_metadata_filter(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm._search_stats = None
        mm._query_cache = None
        mm.retriever.search.return_value = [
            {"id": "1", "content": "data", "metadata": {"agent": "X"}},
        ]
        results = mm.search("data", metadata={"agent": "X"}, mode="keyword")
        assert len(results) > 0

    def test_search_metadata_no_match(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm._search_stats = None
        mm._query_cache = None
        mm.retriever.search.return_value = [
            {"id": "1", "content": "data", "metadata": {"agent": "X"}},
        ]
        results = mm.search("data", metadata={"agent": "Y"}, mode="keyword")
        # Results filtered out by metadata filter; only critical rules prepended
        assert isinstance(results, list)

    def test_search_critical_rules_prepended(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm._search_stats = None
        mm._query_cache = None
        # Inject a critical rule
        mm._critical_rules["test"] = {
            "id": "test", "content": "critical!", "tags": [], "metadata": {},
        }
        mm.retriever.search.return_value = [{"id": "1", "content": "mem"}]
        results = mm.search("test", mode="keyword")
        assert results[0]["content"] == "critical!"

    def test_search_include_critical_false(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm._search_stats = None
        mm._query_cache = None
        mm._critical_rules["test"] = {
            "id": "test", "content": "critical!", "tags": [], "metadata": {},
        }
        mm.retriever.search.return_value = [{"id": "1", "content": "mem"}]
        results = mm.search("test", mode="keyword", include_critical=False)
        assert results[0]["content"] == "mem"

    def test_search_deprecated_mode_falls_through(self):
        """Deprecated modes like 'bm25' now fall through to keyword."""
        mm = mock_mm()
        mm.session_id = "s1"
        mm._search_stats = None
        mm._query_cache = None
        mm.episodic.get_recent.return_value = []
        mm.semantic.get_all.return_value = []
        mm.procedural.get_all.return_value = []
        mm.retriever.search.return_value = []
        # Should not raise error; deprecated mode falls through to keyword
        results = mm.search("test", mode="bm25")
        assert isinstance(results, list)


class TestGetStatsEdgeCases:
    def test_get_stats_basic(self):
        mm = mock_mm()
        mm.session_id = "sess1"
        mm.episodic.count.return_value = 5
        mm.semantic.count.return_value = 3
        mm.procedural.count.return_value = 2
        mm.working_memory = [{"id": "1"}, {"id": "2"}]
        mm.working_cache.size.return_value = 10
        mm.index.built = True
        stats = mm.get_stats()
        assert stats["session_id"] == "sess1"
        assert stats["working_memory_count"] == 2
        assert stats["working_cache_size"] == 10
        assert stats["episodic_count"] == 5
        assert stats["semantic_count"] == 3
        assert stats["procedural_count"] == 2

    def test_get_stats_with_graph(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm.episodic.count.return_value = 0
        mm.semantic.count.return_value = 0
        mm.procedural.count.return_value = 0
        mm.working_cache.size.return_value = 0
        mm.index.built = True
        fake_mg = MagicMock()
        fake_mg.get_stats.return_value = {"nodes": 10}
        mm._multi_graph = fake_mg
        stats = mm.get_stats()
        assert stats["graph"] == {"nodes": 10}

    def test_get_stats_with_ground_truth(self):
        mm = mock_mm()
        mm.session_id = "s1"
        mm.episodic.count.return_value = 0
        mm.semantic.count.return_value = 0
        mm.procedural.count.return_value = 0
        mm.working_cache.size.return_value = 0
        mm.index.built = True
        fake_gt = MagicMock()
        fake_gt.list_sessions.return_value = ["s1"]
        fake_gt.count_records.return_value = 10
        mm._ground_truth = fake_gt
        stats = mm.get_stats()
        assert stats["ground_truth"]["sessions"] == 1
        assert stats["ground_truth"]["records"] == 10


class TestSessionEdgeCases:
    def test_end_session_noop_when_no_session(self):
        mm = mock_mm()
        mm.session_id = None
        mm.end_session()  # should not raise
        assert mm.session_id is None

    def test_cross_session_search(self):
        mm = mock_mm()
        mm.session_id = "s1"
        r1, r2 = MagicMock(), MagicMock()
        r1.to_dict.return_value = {"memory_id": "m1"}
        r2.to_dict.return_value = {"memory_id": "m2"}
        mm._three_tier_retriever.search.return_value = [r1, r2]
        results = mm.cross_session_search("query", layers=["l2"], limit=5)
        assert len(results) == 2
        assert results[0]["memory_id"] == "m1"
        mm._three_tier_retriever.search.assert_called_once()


class TestReflectionPerformance:
    def test_get_reflection_stats(self):
        mm = mock_mm()
        mm._reflection = MagicMock()
        mm._reflection.get_reflection_stats.return_value = {"count": 3}
        assert mm.get_reflection_stats() == {"count": 3}

    def test_get_performance_stats(self):
        mm = mock_mm()
        mm._performance_monitor = MagicMock()
        mm._performance_monitor.get_stats.return_value = {"latency_ms": 5.0}
        stats = mm.get_performance_stats()
        assert stats["latency_ms"] == 5.0

    def test_get_performance_stats_no_monitor(self):
        mm = mock_mm()
        mm._performance_monitor = None
        mm._query_cache = None
        with patch.object(type(mm), "performance_monitor",
                          new_callable=PropertyMock, return_value=None):
            stats = mm.get_performance_stats()
            assert stats.get("enabled") is False

    def test_get_search_statistics_enabled(self):
        mm = mock_mm()
        mm._search_stats = MagicMock()
        mm._search_stats.get_stats.return_value = {"total": 5}
        assert mm.get_search_statistics() == {"total": 5}

    def test_get_search_statistics_disabled(self):
        mm = mock_mm()
        mm._search_stats = None
        mm.enable_stats = False
        with patch.object(type(mm), "search_stats",
                          new_callable=PropertyMock, return_value=None):
            assert mm.get_search_statistics() is None


class TestGroundTruth:
    def test_search_ground_truth_disabled(self):
        mm = mock_mm()
        mm._ground_truth = None
        assert mm.search_ground_truth(session_id="s1") == []

    def test_search_ground_truth_enabled(self):
        mm = mock_mm()
        mm._ground_truth = MagicMock()
        mm._ground_truth.search.return_value = [{"id": "1"}]
        result = mm.search_ground_truth(session_id="s1", keyword="test")
        assert result == [{"id": "1"}]
        mm._ground_truth.search.assert_called_once_with(session_id="s1", keyword="test", limit=50)

    def test_list_sessions_disabled(self):
        mm = mock_mm()
        mm._ground_truth = None
        assert mm.list_sessions() == []

    def test_list_sessions_enabled(self):
        mm = mock_mm()
        mm._ground_truth = MagicMock()
        mm._ground_truth.list_sessions.return_value = [{"session_id": "s1"}]
        assert mm.list_sessions() == [{"session_id": "s1"}]


class TestGraphDecay:
    def test_get_graph_stats_enabled(self):
        mm = mock_mm()
        fake_mg = MagicMock()
        fake_mg.get_stats.return_value = {"nodes": 5}
        mm._multi_graph = fake_mg
        stats = mm.get_graph_stats()
        assert stats["enabled"] is True
        assert stats["nodes"] == 5

    def test_get_graph_stats_disabled(self):
        mm = mock_mm()
        mm._multi_graph = None
        assert mm.get_graph_stats() == {"enabled": False}

    def test_get_node_graph_not_found(self):
        mm = mock_mm()
        fake_mg = MagicMock()
        fake_mg.get_node.return_value = None
        mm._multi_graph = fake_mg
        result = mm.get_node_graph("x")
        assert "error" in result

    def test_get_node_graph_success(self):
        mm = mock_mm()
        fake_node = MagicMock()
        fake_node.to_dict.return_value = {"id": "m1"}
        fake_mg = MagicMock()
        fake_mg.get_node.return_value = fake_node
        fake_mg._graphs = {}
        mm._multi_graph = fake_mg
        result = mm.get_node_graph("m1")
        assert result["node"]["id"] == "m1"

    def test_persist_graph_disabled(self):
        mm = mock_mm()
        mm._multi_graph = None
        assert mm.persist_graph() is False

    def test_persist_graph_enabled(self):
        mm = mock_mm()
        fake_mg = MagicMock()
        fake_mg.to_dict.return_value = {"data": "test"}
        mm._multi_graph = fake_mg
        with patch("builtins.open", MagicMock()):
            assert mm.persist_graph() is True

    def test_persist_graph_exception(self):
        mm = mock_mm()
        fake_mg = MagicMock()
        fake_mg.to_dict.side_effect = Exception("fail")
        mm._multi_graph = fake_mg
        assert mm.persist_graph() is False

    def test_get_decay_stats_disabled(self):
        mm = mock_mm()
        mm._decay_controller = None
        assert mm.get_decay_stats() == {"enabled": False}

    def test_get_decay_stats_enabled(self):
        mm = mock_mm()
        mm._decay_controller = MagicMock()
        mm._decay_controller.get_stats.return_value = {"decayed": 3}
        stats = mm.get_decay_stats()
        assert stats["enabled"] is True
        assert stats["decayed"] == 3

    def test_force_decay_cycle_disabled(self):
        mm = mock_mm()
        mm._decay_controller = None
        assert mm.force_decay_cycle() == 0

    def test_force_decay_cycle_enabled(self):
        mm = mock_mm()
        mm._decay_controller = MagicMock()
        mm._decay_controller.compute_all_decays.return_value = {"m1": -0.5}
        mm._decay_controller.cleanup_expired.return_value = ["m1"]
        from claw_mem.memory_manager import DecayController
        with patch.object(DecayController, "_graph", create=True):
            assert mm.force_decay_cycle() == 1


class TestGatherMemories:
    def test_gather_session_memories_ok(self):
        mm = mock_mm()
        mm._episodic.get_all.return_value = [{"id": "m1"}]
        assert mm._gather_session_memories("s1") == [{"id": "m1"}]

    def test_gather_session_memories_exception(self):
        mm = mock_mm()
        mm._episodic.get_all.side_effect = Exception("fail")
        assert mm._gather_session_memories("s1") == []


class TestHandleError:
    def test_with_fallback(self):
        mm = mock_mm()
        result = mm._handle_error(ValueError("x"), "op", fallback="fb")
        assert result == "fb"

    def test_without_fallback(self):
        mm = mock_mm()
        # _handle_error uses bare `raise` so it must be called inside an except block
        try:
            raise ValueError("x")
        except ValueError:
            with pytest.raises(ValueError, match="x"):
                mm._handle_error(ValueError("x"), "op")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
