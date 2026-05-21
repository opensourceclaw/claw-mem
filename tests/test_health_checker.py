# Copyright 2026 Peter Cheng
"""Comprehensive tests for health_checker.py - Data Health Checker"""

import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claw_mem.health_checker import (
    HealthChecker,
    HealthReport,
    HealthStatus,
)


class TestHealthStatus:
    """Test HealthStatus dataclass"""

    def test_defaults(self):
        """Test default values"""
        status = HealthStatus(
            component="test",
            healthy=True,
            message="Test message",
        )
        
        assert status.component == "test"
        assert status.healthy is True
        assert status.message == "Test message"
        assert status.severity == "info"
        assert status.details == {}
        assert status.timestamp is not None

    def test_custom_values(self):
        """Test custom values"""
        status = HealthStatus(
            component="test",
            healthy=False,
            message="Error",
            severity="error",
            details={"key": "value"},
            timestamp="2026-01-01T00:00:00",
        )
        
        assert status.severity == "error"
        assert status.details == {"key": "value"}
        assert status.timestamp == "2026-01-01T00:00:00"


class TestHealthReport:
    """Test HealthReport dataclass"""

    def test_creation(self):
        """Test creating a health report"""
        statuses = [
            HealthStatus("index", True, "Healthy", "info"),
            HealthStatus("disk", True, "OK", "info"),
        ]
        
        report = HealthReport(
            overall_healthy=True,
            check_time="2026-01-01T00:00:00",
            total_issues=0,
            critical_issues=0,
            warning_issues=0,
            statuses=statuses,
            recommendations=["Recommendation 1"],
        )
        
        assert report.overall_healthy is True
        assert report.total_issues == 0
        assert len(report.statuses) == 2

    def test_to_dict(self):
        """Test converting to dictionary"""
        statuses = [HealthStatus("test", True, "OK")]
        
        report = HealthReport(
            overall_healthy=True,
            check_time="2026-01-01T00:00:00",
            total_issues=0,
            critical_issues=0,
            warning_issues=0,
            statuses=statuses,
            recommendations=[],
        )
        
        data = report.to_dict()
        
        assert isinstance(data, dict)
        assert "overall_healthy" in data
        assert "statuses" in data


class TestHealthChecker:
    """Test HealthChecker class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "health.check_interval_hours": 24,
            "health.auto_cleanup": True,
            "health.max_backup_count": 10,
            "health.alert_on_issues": True,
            "storage.workspace": "~/.openclaw/workspace",
        }.get(key, default)
        return config

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            yield str(workspace)

    def test_init(self, mock_config, temp_workspace):
        """Test HealthChecker initialization"""
        with patch("claw_mem.health_checker.Path.expanduser"):
            with patch("claw_mem.health_checker.Path.home", return_value=Path(temp_workspace).parent):
                checker = HealthChecker(mock_config)
                
                assert checker.config == mock_config
                assert checker.auto_cleanup_enabled is True
                assert checker.max_backups == 10

    def test_check_all_success(self, mock_config):
        """Test comprehensive health check"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            # Create .claw-mem directory
            claw_mem_dir = Path(tmpdir) / ".claw-mem"
            claw_mem_dir.mkdir()
            
            mock_config.get.side_effect = lambda key, default=None: {
                "health.check_interval_hours": 24,
                "health.auto_cleanup": True,
                "health.max_backup_count": 10,
                "health.alert_on_issues": False,  # Disable alerts for test
                "storage.workspace": str(workspace),
            }.get(key, default)
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                checker.claw_mem_dir = claw_mem_dir
                checker.auto_cleanup_enabled = True
                checker.max_backups = 10
                checker.alert_on_issues = False
                checker.last_check = None
                checker.last_report = None
                
                report = checker.check_all()
                
                assert isinstance(report, HealthReport)
                assert len(report.statuses) == 6  # 6 health checks

    def test_check_index_health_no_index(self, mock_config):
        """Test index health check with no index"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            claw_mem_dir = Path(tmpdir) / ".claw-mem"
            claw_mem_dir.mkdir()
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                checker.claw_mem_dir = claw_mem_dir
                
                status = checker._check_index_health()
                
                assert status.component == "index"
                assert status.healthy is True
                assert "not found" in status.message.lower()

    def test_check_index_health_with_files(self, mock_config):
        """Test index health check with index files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            claw_mem_dir = Path(tmpdir) / ".claw-mem"
            claw_mem_dir.mkdir()
            index_dir = claw_mem_dir / "index"
            index_dir.mkdir()
            
            # Create fake index files
            (index_dir / "index.pkl").write_bytes(b"fake index data")
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                checker.claw_mem_dir = claw_mem_dir
                
                status = checker._check_index_health()
                
                assert status.healthy is True
                assert status.severity == "info"

    def test_check_data_integrity_no_memory(self, mock_config):
        """Test data integrity check with no memory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_data_integrity()
                
                assert status.component == "data"
                assert status.healthy is True

    def test_check_data_integrity_with_memory(self, mock_config):
        """Test data integrity check with memory file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            memory_dir = workspace / "memory"
            memory_dir.mkdir()
            
            memory_file = memory_dir / "MEMORY.md"
            memory_file.write_text("# Memory\n\nTest content")
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_data_integrity()
                
                assert status.component == "data"
                assert status.healthy is True

    def test_check_data_integrity_corrupted(self, mock_config):
        """Test data integrity check with corrupted file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            memory_dir = workspace / "memory"
            memory_dir.mkdir()
            
            memory_file = memory_dir / "MEMORY.md"
            # Create a file that will cause read error
            memory_file.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                # May succeed or fail depending on encoding handling
                status = checker._check_data_integrity()
                
                assert status.component == "data"

    def test_check_disk_space(self, mock_config):
        """Test disk space check"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_disk_space()
                
                assert status.component == "disk"
                assert "free" in status.message.lower() or "space" in status.message.lower()

    def test_check_memory_usage(self, mock_config):
        """Test memory usage check"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_memory_usage()
                
                assert status.component == "memory"

    def test_check_expired_memories_no_memory(self, mock_config):
        """Test expired memories check with no memories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_expired_memories()
                
                assert status.component == "memories"
                assert status.healthy is True

    def test_check_expired_memories_with_files(self, mock_config):
        """Test expired memories check with memory files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            memory_dir = workspace / "memory"
            memory_dir.mkdir()
            
            # Create old memory files
            old_file = memory_dir / "old.md"
            old_file.write_text("# Old Memory")
            
            with patch("claw_mem.health_checker.datetime") as mock_datetime:
                # Simulate old file by mocking now
                mock_datetime.now.return_value = datetime.now() + timedelta(days=60)
                
                with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                    checker = HealthChecker.__new__(HealthChecker)
                    checker.config = mock_config
                    checker.workspace = workspace
                    
                    status = checker._check_expired_memories()
                    
                    assert status.component == "memories"

    def test_check_backup_status_no_backups(self, mock_config):
        """Test backup status check with no backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_backup_status()
                
                assert status.component == "backups"
                assert status.healthy is True

    def test_check_backup_status_with_backups(self, mock_config):
        """Test backup status check with backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            # Create backup directory with a backup
            backup_dir = Path(tmpdir) / "backups"
            backup_dir.mkdir()
            (backup_dir / "backup.zip").write_bytes(b"fake zip content")
            
            mock_config.get.side_effect = lambda key, default=None: {
                "storage.backup_dir": str(backup_dir),
            }.get(key, default)
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                status = checker._check_backup_status()
                
                assert status.component == "backups"

    def test_generate_recommendations(self, mock_config):
        """Test recommendation generation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            statuses = [
                HealthStatus("disk", False, "Low disk space", "critical"),
                HealthStatus("memory", True, "OK", "warning"),
            ]
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                
                recommendations = checker._generate_recommendations(statuses)
                
                assert len(recommendations) > 0
                assert any("disk" in rec.lower() for rec in recommendations)

    def test_auto_cleanup(self, mock_config):
        """Test auto cleanup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            claw_mem_dir = Path(tmpdir) / ".claw-mem"
            claw_mem_dir.mkdir()
            
            # Create old backups
            backup_dir = claw_mem_dir / "backups"
            backup_dir.mkdir()
            
            # Create more backups than max
            for i in range(15):
                (backup_dir / f"backup_{i}.zip").write_bytes(b"test")
            
            # Create temp directory
            temp_dir = claw_mem_dir / "tmp"
            temp_dir.mkdir()
            (temp_dir / "temp.txt").write_text("temp")
            
            mock_config.get.side_effect = lambda key, default=None: {
                "storage.backup_dir": str(backup_dir),
            }.get(key, default)
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.workspace = workspace
                checker.claw_mem_dir = claw_mem_dir
                checker.max_backups = 10
                
                stats = checker.auto_cleanup()
                
                assert "backups_removed" in stats
                assert "files_cleaned" in stats

    def test_cleanup_old_backups(self, mock_config):
        """Test cleaning up old backups"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            backup_dir = Path(tmpdir) / "backups"
            backup_dir.mkdir()
            
            # Create backups
            for i in range(12):
                (backup_dir / f"backup_{i}.zip").write_bytes(b"test")
            
            mock_config.get.side_effect = lambda key, default=None: {
                "storage.backup_dir": str(backup_dir),
            }.get(key, default)
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.config = mock_config
                checker.max_backups = 10
                
                removed = checker._cleanup_old_backups()
                
                assert removed == 2  # 12 - 10 = 2

    def test_cleanup_temp_files(self, mock_config):
        """Test cleaning up temp files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            claw_mem_dir = Path(tmpdir) / ".claw-mem"
            claw_mem_dir.mkdir()
            
            temp_dir = claw_mem_dir / "tmp"
            temp_dir.mkdir()
            
            # Create temp files
            for i in range(5):
                (temp_dir / f"temp_{i}.tmp").write_text("temp")
            
            with patch.object(HealthChecker, "__init__", lambda self, cfg: None):
                checker = HealthChecker.__new__(HealthChecker)
                checker.claw_mem_dir = claw_mem_dir
                
                removed = checker._cleanup_temp_files()
                
                assert removed == 5

    def test_start_periodic_checks(self, mock_config):
        """Test starting periodic checks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            mock_config.get.side_effect = lambda key, default=None: {
                "health.check_interval_hours": 1,
                "health.auto_cleanup": False,
                "health.max_backup_count": 10,
                "health.alert_on_issues": False,
                "storage.workspace": str(workspace),
            }.get(key, default)
            
            checker = HealthChecker(mock_config)
            checker.start_periodic_checks()
            
            # Give it a moment to start
            time.sleep(0.1)
            
            assert checker._check_thread is not None
            assert checker._check_thread.is_alive()
            
            checker.stop_periodic_checks()

    def test_stop_periodic_checks(self, mock_config):
        """Test stopping periodic checks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            mock_config.get.side_effect = lambda key, default=None: {
                "health.check_interval_hours": 24,
                "health.auto_cleanup": False,
                "health.max_backup_count": 10,
                "health.alert_on_issues": False,
                "storage.workspace": str(workspace),
            }.get(key, default)
            
            checker = HealthChecker(mock_config)
            checker.start_periodic_checks()
            checker.stop_periodic_checks()
            
            assert checker._check_thread is None

    def test_get_report(self, mock_config):
        """Test getting last report"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            claw_mem_dir = Path(tmpdir) / ".claw-mem"
            claw_mem_dir.mkdir()
            
            mock_config.get.side_effect = lambda key, default=None: {
                "health.check_interval_hours": 24,
                "health.auto_cleanup": False,
                "health.max_backup_count": 10,
                "health.alert_on_issues": False,
                "storage.workspace": str(workspace),
            }.get(key, default)
            
            checker = HealthChecker(mock_config)
            
            # No report yet
            assert checker.get_report() is None
            
            # Run a check
            checker.check_all()
            
            # Should have report now
            assert checker.get_report() is not None

    def test_get_stats(self, mock_config):
        """Test getting health checker stats"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            
            mock_config.get.side_effect = lambda key, default=None: {
                "health.check_interval_hours": 24,
                "health.auto_cleanup": True,
                "health.max_backup_count": 10,
                "health.alert_on_issues": False,
                "storage.workspace": str(workspace),
            }.get(key, default)
            
            checker = HealthChecker(mock_config)
            
            stats = checker.get_stats()
            
            assert "last_check" in stats
            assert "check_interval_hours" in stats
            assert stats["auto_cleanup_enabled"] is True
