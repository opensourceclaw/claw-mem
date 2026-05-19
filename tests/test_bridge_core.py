# Copyright 2026 Peter Cheng
"""Unit tests for bridge module."""

import pytest


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
