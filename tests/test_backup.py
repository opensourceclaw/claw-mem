# Copyright 2026 Peter Cheng
"""Tests for backup.py - Backup and Restore System"""

import json
import os
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claw_mem.backup import BackupManager, backup_command, list_command, restore_command


class TestBackupManager:
    """Test BackupManager class"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            # Create test files
            (workspace / "MEMORY.md").write_text("# Memory\n\nTest content")
            memory_dir = workspace / "memory"
            memory_dir.mkdir()
            (memory_dir / "test1.md").write_text("---\nid: test1\n---\nTest memory 1")
            (memory_dir / "test2.md").write_text("---\nid: test2\n---\nTest memory 2")
            
            yield str(workspace)

    def test_init(self, temp_workspace):
        """Test BackupManager initialization"""
        manager = BackupManager(temp_workspace)
        assert manager.workspace == Path(temp_workspace)
        assert manager.backup_dir == Path(temp_workspace) / ".claw-mem" / "backups"
        assert manager.backup_dir.exists()

    def test_backup_full(self, temp_workspace):
        """Test full backup creation"""
        manager = BackupManager(temp_workspace)
        result = manager.backup(incremental=False)
        
        assert result["success"] is True
        assert "path" in result
        assert "size" in result
        assert result["size"] > 0
        assert result["files_count"] >= 3  # MEMORY.md + test1.md + test2.md
        
        # Verify backup file exists
        assert Path(result["path"]).exists()

    def test_backup_incremental(self, temp_workspace):
        """Test incremental backup creation"""
        manager = BackupManager(temp_workspace)
        result = manager.backup(incremental=True)
        
        assert result["success"] is True
        assert result["timestamp"] is not None

    def test_backup_custom_path(self, temp_workspace):
        """Test backup with custom output path"""
        manager = BackupManager(temp_workspace)
        custom_path = os.path.join(temp_workspace, "custom_backup.zip")
        result = manager.backup(output_path=custom_path)
        
        assert result["success"] is True
        assert str(Path(result["path"]).resolve()) == str(Path(custom_path).resolve())
        assert Path(custom_path).exists()

    def test_verify_valid_backup(self, temp_workspace):
        """Test backup verification with valid backup"""
        manager = BackupManager(temp_workspace)
        result = manager.backup()
        
        verify_result = manager.verify(result["path"])
        
        assert verify_result["valid"] is True
        assert "backup_info" in verify_result
        assert verify_result["backup_info"]["version"] == "0.8.0"

    def test_verify_nonexistent_backup(self, temp_workspace):
        """Test backup verification with non-existent file"""
        manager = BackupManager(temp_workspace)
        verify_result = manager.verify("/nonexistent/backup.zip")
        
        assert verify_result["valid"] is False
        assert "error" in verify_result

    def test_verify_corrupted_backup(self, temp_workspace):
        """Test backup verification with corrupted file"""
        manager = BackupManager(temp_workspace)
        
        # Create a corrupted zip file
        corrupted_path = Path(temp_workspace) / "corrupted.zip"
        corrupted_path.write_text("This is not a valid zip file")
        
        verify_result = manager.verify(str(corrupted_path))
        
        assert verify_result["valid"] is False

    def test_restore_valid_backup(self, temp_workspace):
        """Test restore from valid backup"""
        manager = BackupManager(temp_workspace)
        backup_result = manager.backup()
        
        # Create a restore workspace
        restore_workspace = Path(temp_workspace).parent / "restore_workspace"
        restore_workspace.mkdir()
        
        restore_manager = BackupManager(str(restore_workspace))
        restore_result = restore_manager.restore(backup_result["path"])
        
        assert restore_result["success"] is True
        assert restore_result["restored_files"] > 0

    def test_restore_nonexistent_backup(self, temp_workspace):
        """Test restore from non-existent backup"""
        manager = BackupManager(temp_workspace)
        result = manager.restore("/nonexistent/backup.zip")
        
        assert result["success"] is False
        assert "error" in result

    def test_restore_verify_first_false(self, temp_workspace):
        """Test restore without verification"""
        manager = BackupManager(temp_workspace)
        backup_result = manager.backup()
        
        restore_manager = BackupManager(temp_workspace)
        result = restore_manager.restore(backup_result["path"], verify_first=False)
        
        assert result["success"] is True

    def test_list_backups(self, temp_workspace):
        """Test listing backups"""
        manager = BackupManager(temp_workspace)
        
        # Create multiple backups
        manager.backup()
        manager.backup()
        manager.backup(incremental=True)
        
        backups = manager.list_backups()
        
        # May have more or fewer due to timing, just check we have backups
        assert len(backups) >= 1
        assert all("path" in b for b in backups)
        assert all("size" in b for b in backups)
        assert all("timestamp" in b for b in backups)

    def test_list_backups_empty(self, temp_workspace):
        """Test listing backups when none exist"""
        manager = BackupManager(temp_workspace)
        backups = manager.list_backups()
        
        assert backups == []

    def test_collect_files(self, temp_workspace):
        """Test file collection for backup"""
        manager = BackupManager(temp_workspace)
        files = manager._collect_files()
        
        assert len(files) >= 3  # MEMORY.md + test1.md + test2.md
        assert any(f.name == "MEMORY.md" for f in files)

    def test_collect_files_empty_workspace(self):
        """Test file collection with no files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "empty_workspace"
            workspace.mkdir()
            
            manager = BackupManager(str(workspace))
            files = manager._collect_files()
            
            assert files == []


class TestCLIFunctions:
    """Test CLI command functions"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            # Create test files
            (workspace / "MEMORY.md").write_text("# Memory\n\nTest content")
            memory_dir = workspace / "memory"
            memory_dir.mkdir()
            (memory_dir / "test1.md").write_text("---\nid: test1\n---\nTest memory 1")
            
            yield str(workspace)

    def test_backup_command(self, temp_workspace, capsys):
        """Test backup CLI command"""
        backup_command(temp_workspace)
        
        captured = capsys.readouterr()
        assert "✅ Backup successful!" in captured.out

    def test_restore_command_success(self, temp_workspace, capsys):
        """Test restore CLI command"""
        manager = BackupManager(temp_workspace)
        backup_result = manager.backup()
        
        restore_command(temp_workspace, backup_result["path"])
        
        captured = capsys.readouterr()
        assert "✅ Restore successful!" in captured.out

    def test_restore_command_failure(self, temp_workspace, capsys):
        """Test restore CLI command with invalid path"""
        restore_command(temp_workspace, "/nonexistent/backup.zip")
        
        captured = capsys.readouterr()
        assert "❌ Restore failed" in captured.out

    def test_list_command(self, temp_workspace, capsys):
        """Test list CLI command"""
        # Create a backup first
        manager = BackupManager(temp_workspace)
        manager.backup()
        
        list_command(temp_workspace)
        
        captured = capsys.readouterr()
        assert "Found" in captured.out

    def test_list_command_empty(self, temp_workspace, capsys):
        """Test list CLI command with no backups"""
        list_command(temp_workspace)
        
        captured = capsys.readouterr()
        assert "No backups found" in captured.out
