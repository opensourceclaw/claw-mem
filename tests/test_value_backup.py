#!/usr/bin/env python3
"""
Tests for ValueBackup
"""

import pytest
import tempfile
from pathlib import Path
from claw_mem.values import ValueBackup


class TestBackupMetadata:
    """Test BackupMetadata"""

    def test_creation(self):
        """Test metadata creation"""
        from claw_mem.values import BackupMetadata
        from datetime import datetime

        meta = BackupMetadata(
            user_id="user1",
            backup_id="abc123",
            created_at=datetime.now(),
            file_path="/tmp/test.json",
            file_size=1024,
            values_count=5
        )

        assert meta.user_id == "user1"
        assert meta.backup_id == "abc123"


class TestValueBackup:
    """Test ValueBackup"""

    @pytest.fixture
    def backup(self):
        """Create backup manager with temp directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = Path(tmpdir)
            yield ValueBackup(backup_dir=backup_dir)

    @pytest.fixture
    def populated_backup(self, backup):
        """Create backup with data"""
        backup.value_store.save_principle("user1", "Be honest")
        backup.value_store.save_preference("user1", "lang", "en")
        backup.value_store.save_red_line("user1", "no violence")
        yield backup

    def test_creation(self, backup):
        """Test creation"""
        assert backup.backup_dir.exists()

    def test_export_values(self, backup):
        """Test export values"""
        backup.value_store.save_principle("user1", "Test principle")

        metadata = backup.export_values("user1")

        assert metadata.user_id == "user1"
        assert metadata.backup_id
        assert metadata.file_size > 0

    def test_import_values(self, backup):
        """Test import values"""
        # 先导出
        backup.value_store.save_principle("user1", "Principle 1")
        metadata = backup.export_values("user1")

        # 模拟不同用户导入
        backup.value_store.save_principle("user2", "Different")
        metadata2 = backup.import_values("user2", Path(metadata.file_path), overwrite=True)

        assert metadata2 is True

    def test_list_backups(self, populated_backup):
        """Test list backups"""
        # 创建多个备份
        populated_backup.export_values("user1")
        populated_backup.export_values("user1")

        backups = populated_backup.list_backups("user1")

        assert len(backups) >= 2

    def test_backup_metadata(self, populated_backup):
        """Test backup metadata"""
        populated_backup.export_values("user1")

        meta = populated_backup.backup_metadata("user1")

        assert meta["user_id"] == "user1"
        assert meta["backup_count"] >= 1

    def test_delete_backup(self, populated_backup):
        """Test delete backup"""
        metadata = populated_backup.export_values("user1")

        result = populated_backup.delete_backup(metadata.backup_id)

        assert result is True
