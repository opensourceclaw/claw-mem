# Copyright 2026 Peter Cheng
"""Unit tests for atomic_writer, backup, CLI, and config_manager modules."""

import pytest
import tempfile
from pathlib import Path


class TestAtomicWriter:
    def test_import(self):
        from claw_mem.atomic_writer import AtomicWriter
        assert AtomicWriter is not None

    def test_init(self, tmp_path):
        from claw_mem.atomic_writer import AtomicWriter
        w = AtomicWriter()
        assert w is not None

    def test_save_node(self):
        from claw_mem.atomic_writer import AtomicWriter
        from unittest.mock import MagicMock
        w = AtomicWriter()
        node = MagicMock()
        node.content_path = "/tmp/test.md"
        node.content = "test"
        node.metadata = {}
        w.save_node(node)  # no exception = pass
        assert w is not None


class TestBackup:
    def test_import(self):
        from claw_mem.backup import BackupManager
        assert BackupManager is not None

    def test_cli_commands(self):
        from claw_mem.backup import backup_command, restore_command, list_command
        assert callable(backup_command)
        assert callable(restore_command)
        assert callable(list_command)

    def test_manager_init(self):
        from claw_mem.backup import BackupManager
        bm = BackupManager('/tmp')
        assert bm is not None


class TestCLI:
    def test_cli_import(self):
        from claw_mem import cli
        assert cli is not None


class TestConfigManager:
    def test_import(self):
        from claw_mem.config_manager import ConfigManager
        assert ConfigManager is not None
