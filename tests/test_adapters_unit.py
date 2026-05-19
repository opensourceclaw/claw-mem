# Copyright 2026 Peter Cheng
"""Unit tests for claw_mem.adapters module."""

import pytest


class TestV2Adapter:
    def test_import(self):
        from claw_mem.adapters.v2 import V2Strategy
        assert V2Strategy is not None

    def test_version_import(self):
        from claw_mem.adapters.v2 import CLAW_MEM_VERSION
        assert isinstance(CLAW_MEM_VERSION, str)

    def test_base_adapter(self):
        from claw_mem.adapters.v2 import BaseAdapter
        assert BaseAdapter is not None


class TestV1Adapter:
    def test_import(self):
        from claw_mem.adapters.v1 import V1Strategy
        assert V1Strategy is not None

    def test_version_import(self):
        from claw_mem.adapters.v1 import CLAW_MEM_VERSION
        assert isinstance(CLAW_MEM_VERSION, str)


class TestOpenClawAdapter:
    def test_import(self):
        from claw_mem.adapters.openclaw_adapter import OpenClawAdapter
        assert OpenClawAdapter is not None
