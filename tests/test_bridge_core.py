# Copyright 2026 Peter Cheng
"""Unit tests for bridge module."""

import os
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from claw_mem.bridge import ClawMemBridge, main


class TestClawMemBridge:
    def test_import(self):
        from claw_mem.bridge import ClawMemBridge

        assert ClawMemBridge is not None

    def test_init(self):
        from claw_mem.bridge import ClawMemBridge

        bridge = ClawMemBridge()
        assert bridge is not None
        assert bridge.memory_manager is not None

    def test_memory_manager_access(self):
        from claw_mem.bridge import ClawMemBridge

        bridge = ClawMemBridge()
        mm = bridge.memory_manager
        assert mm is not None

    def test_request_count(self):
        from claw_mem.bridge import ClawMemBridge

        bridge = ClawMemBridge()
        assert isinstance(bridge.request_count, int)

    def test_total_latency(self):
        from claw_mem.bridge import ClawMemBridge

        bridge = ClawMemBridge()
        assert isinstance(bridge.total_latency, (int, float))


class TestBridgeHandlers:
    """Test individual RPC handler methods"""

    @pytest.fixture
    def bridge(self):
        from claw_mem.bridge import ClawMemBridge

        b = ClawMemBridge.__new__(ClawMemBridge)
        b.request_count = 0
        b.total_latency = 0.0
        b.memory_manager = MagicMock()
        b._adapter = MagicMock()
        return b

    def test_respond_success(self, bridge):
        result = bridge._respond(1, {"data": "test"})
        assert result is None

    def test_respond_error(self, bridge):
        result = bridge._respond(1, "error message", -32000)
        assert result is None

    def test_handle_request_unknown_method(self, bridge):
        resp = bridge._handle_request({"method": "unknown_method", "params": {}, "id": 1})
        assert resp is None

    def test_handle_search(self, bridge):
        bridge._adapter.search.return_value = []
        resp = bridge._handle_search({"query": "test"})
        assert "results" in resp

    def test_handle_store(self, bridge):
        bridge._adapter.store.return_value = {"id": "test"}
        resp = bridge._handle_store({"content": "test"})
        assert resp is not None

    def test_handle_get(self, bridge):
        bridge._adapter.get.return_value = {"id": "test"}
        resp = bridge._handle_get({"id": "test"})
        assert resp is not None

    def test_handle_delete(self, bridge):
        bridge._adapter.delete.return_value = True
        resp = bridge._handle_delete({"id": "test"})
        assert resp is not None

    def test_handle_ping(self, bridge):
        bridge._adapter.ping.return_value = {"pong": True}
        resp = bridge._handle_ping({})
        assert resp is not None

    def test_handle_status(self, bridge):
        bridge._adapter.status.return_value = {"ok": True}
        resp = bridge._handle_status({})
        assert resp is not None

    def test_handle_build_context(self, bridge):
        bridge._adapter.build_context.return_value = {"context": ""}
        resp = bridge._handle_build_context({})
        assert resp is not None

    def test_handle_start_session(self, bridge):
        bridge._adapter.start_session.return_value = {"session": "id"}
        resp = bridge._handle_start_session({})
        assert resp is not None

    def test_handle_end_session(self, bridge):
        bridge._adapter.end_session.return_value = {"ok": True}
        resp = bridge._handle_end_session({})
        assert resp is not None

    def test_handle_resolve_flush_plan(self, bridge):
        bridge._adapter.resolve_flush_plan.return_value = {"plan": {}}
        resp = bridge._handle_resolve_flush_plan({})
        assert resp is not None

    def test_handle_get_critical_rules(self, bridge):
        bridge.memory_manager.get_critical_rules.return_value = ["rule1"]
        resp = bridge._handle_get_critical_rules({})
        assert resp["count"] == 1

    def test_handle_get_critical_rules_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_get_critical_rules({})
        assert resp == {"rules": [], "count": 0}

    def test_handle_store_critical_rule(self, bridge):
        bridge.memory_manager.store_critical_rule.return_value = "rule_1"
        resp = bridge._handle_store_critical_rule({"text": "test rule", "metadata": {}})
        assert resp["success"] is True

    def test_handle_store_critical_rule_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_store_critical_rule({"text": "test"})
        assert resp["success"] is False

    def test_handle_delete_critical_rule(self, bridge):
        bridge.memory_manager.delete_critical_rule.return_value = True
        resp = bridge._handle_delete_critical_rule({"rule_id": "rule_1"})
        assert resp["success"] is True

    def test_handle_delete_critical_rule_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_delete_critical_rule({"rule_id": "test"})
        assert resp["success"] is False

    # Session continuity handlers
    def test_handle_extract_important_content(self, bridge):
        with patch("claw_mem.bridge.extract_important_content") as mock_fn:
            mock_fn.return_value = {"items": []}
            resp = bridge._handle_extract_important_content({"messages": ["msg1"]})
            assert resp is not None

    def test_handle_generate_session_summary(self, bridge):
        with patch("claw_mem.bridge.generate_session_summary") as mock_fn:
            mock_fn.return_value = {"summary": ""}
            resp = bridge._handle_generate_session_summary({"messages": ["msg1"]})
            assert resp is not None

    def test_handle_detect_content_type(self, bridge):
        resp = bridge._handle_detect_content_type({"content": "hello world"})
        assert "type" in resp
        assert "importance" in resp

    def test_handle_detect_content_type_empty(self, bridge):
        resp = bridge._handle_detect_content_type({"content": ""})
        assert resp == {"type": "chat", "importance": 0.0}

    # Compression spectrum handlers
    def test_handle_get_compression_stats(self, bridge):
        bridge.memory_manager.get_compression_stats.return_value = {"enabled": True}
        resp = bridge._handle_get_compression_stats({})
        assert resp.get("enabled") is True

    def test_handle_get_compression_stats_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_get_compression_stats({})
        assert resp == {"enabled": False}

    def test_handle_manual_compress(self, bridge):
        bridge.memory_manager.manual_compress.return_value = {"compressed": True}
        resp = bridge._handle_manual_compress({"memory_id": "m1"})
        assert resp["success"] is True

    def test_handle_manual_compress_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_manual_compress({"memory_id": "m1"})
        assert resp["success"] is False

    def test_handle_configure_compression(self, bridge):
        bridge.memory_manager.compression_spectrum = MagicMock()
        resp = bridge._handle_configure_compression({"access": 5})
        assert resp["success"] is True

    def test_handle_configure_compression_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_configure_compression({"access": 5})
        assert resp["success"] is False

    def test_handle_configure_compression_no_spectrum(self, bridge):
        bridge.memory_manager.compression_spectrum = None
        resp = bridge._handle_configure_compression({"access": 5})
        assert resp["success"] is False

    # CMS Perception Layer handlers
    def test_handle_get_capacity_stats(self, bridge):
        bridge.memory_manager.get_capacity_stats.return_value = {"total": 100}
        resp = bridge._handle_get_capacity_stats({})
        assert resp is not None

    def test_handle_get_capacity_stats_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_get_capacity_stats({})
        assert resp == {"enabled": False}

    def test_handle_get_importance_scores(self, bridge):
        bridge.memory_manager.get_importance_scores.return_value = {"id1": 0.9}
        resp = bridge._handle_get_importance_scores({"memory_ids": ["id1"]})
        assert "scores" in resp

    def test_handle_get_importance_scores_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_get_importance_scores({"memory_ids": []})
        assert "error" in resp

    def test_handle_get_important_memories(self, bridge):
        bridge.memory_manager.get_important_memories.return_value = [{"id": "m1", "score": 0.9}]
        resp = bridge._handle_get_important_memories({"threshold": 0.5, "limit": 10})
        assert "memories" in resp

    def test_handle_get_important_memories_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_get_important_memories({})
        assert "error" in resp

    # CMS State Machine handlers
    def test_handle_save_snapshot(self, bridge):
        bridge.memory_manager.save_snapshot.return_value = "snap_1"
        resp = bridge._handle_save_snapshot({"session_id": "s1"})
        assert resp["snapshot_id"] == "snap_1"

    def test_handle_save_snapshot_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_save_snapshot({})
        assert "error" in resp

    def test_handle_recover_session(self, bridge):
        bridge.memory_manager.recover_session.return_value = {"recovered": True}
        resp = bridge._handle_recover_session({"session_id": "s1"})
        assert resp is not None

    def test_handle_recover_session_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_recover_session({})
        assert "error" in resp

    def test_handle_switch_context(self, bridge):
        bridge.memory_manager.switch_context.return_value = {"switched": True}
        resp = bridge._handle_switch_context({"from_id": "a", "to_id": "b"})
        assert resp is not None

    def test_handle_switch_context_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_switch_context({})
        assert "error" in resp

    def test_handle_list_snapshots(self, bridge):
        bridge.memory_manager.list_snapshots.return_value = [{"id": "snap1"}]
        resp = bridge._handle_list_snapshots({"session_id": "s1"})
        assert "snapshots" in resp

    def test_handle_list_snapshots_no_manager(self, bridge):
        bridge.memory_manager = None
        resp = bridge._handle_list_snapshots({})
        assert resp == {"snapshots": []}


class TestBridgeRun:
    """Test bridge run loop"""

    def test_run_exits_on_eof(self):
        from claw_mem.bridge import ClawMemBridge

        with patch("claw_mem.bridge.sys.stdin", StringIO("")):
            with patch.object(ClawMemBridge, "_initialize"):
                with patch.object(ClawMemBridge, "_log"):
                    bridge = ClawMemBridge.__new__(ClawMemBridge)
                    bridge._adapter = MagicMock()
                    bridge._adapter.version = "test"
                    bridge.request_count = 0
                    bridge.run()
                    assert bridge.request_count == 0

    def test_main_sets_env(self):
        with patch.object(ClawMemBridge, "__init__", return_value=None):
            with patch.object(ClawMemBridge, "run"):
                from claw_mem.bridge import main

                main()
                assert os.environ.get("CLAW_MEM_SILENT") == "1"
