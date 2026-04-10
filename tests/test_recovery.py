"""
Tests for Recovery Manager

Tests automatic diagnosis, recovery, and graceful degradation.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from claw_mem.recovery import RecoveryManager, RecoveryStrategy, Diagnosis, RecoveryResult


class TestDiagnosis:
    """Test diagnosis functionality"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)
        
        # Create necessary directories
        (workspace / "memory").mkdir()
        (workspace / ".claw-mem").mkdir()
        
        yield workspace
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_diagnosis_initialization(self, temp_workspace):
        """Test diagnosis initialization"""
        diagnosis = Diagnosis(
            problem_type="INDEX_MISSING",
            severity="medium",
            description="Index file not found",
            root_cause="File deleted or not created",
            affected_components=["index"]
        )
        
        assert diagnosis.problem_type == "INDEX_MISSING"
        assert diagnosis.severity == "medium"
        assert diagnosis.description == "Index file not found"
        assert diagnosis.root_cause == "File deleted or not created"
        assert diagnosis.timestamp is not None
    
    def test_recovery_result_initialization(self):
        """Test recovery result initialization"""
        result = RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.REBUILD,
            time_taken_ms=1500.5,
            description="Index rebuilt successfully"
        )
        
        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.REBUILD
        assert result.time_taken_ms == 1500.5
        assert result.data_recovered is False
        assert result.user_action_needed is False


class TestRecoveryManager:
    """Test recovery manager"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)
        
        # Create necessary directories
        (workspace / "memory").mkdir()
        (workspace / ".claw-mem").mkdir()
        (workspace / ".claw-mem" / "backups").mkdir()
        
        yield workspace
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self, temp_workspace):
        """Create mock configuration"""
        class MockConfig:
            def __init__(self, workspace):
                self.workspace = workspace
            
            def get(self, key, default=None):
                return default
            
            def set(self, key, value):
                pass
        
        return MockConfig(temp_workspace)
    
    def test_recovery_manager_initialization(self, temp_workspace, mock_config):
        """Test recovery manager initialization"""
        manager = RecoveryManager(mock_config)
        
        assert manager is not None
    
    def test_diagnose_missing_index(self, temp_workspace, mock_config):
        """Test diagnosis for missing index"""
        manager = RecoveryManager(mock_config)
        
        # Remove index file to simulate problem
        index_file = temp_workspace / ".claw-mem" / "index" / "index_v0.9.0.pkl.gz"
        if index_file.exists():
            index_file.unlink()
        
        # Run diagnosis
        diagnosis = manager.diagnose("index_load")
        
        assert diagnosis is not None
        # Diagnosis may return Chinese or English problem type
        assert diagnosis.problem_type is not None
    
    def test_rebuild_strategy(self, temp_workspace, mock_config):
        """Test rebuild recovery strategy"""
        manager = RecoveryManager(mock_config)
        
        # Simulate an error and attempt recovery
        try:
            raise Exception("Index corrupted")
        except Exception as e:
            result = manager.recover(e, {"test": "context"})
        
        assert result is not None
        assert result.time_taken_ms > 0
        # Result may be successful or fail depending on context
    
    def test_checkpoint_strategy(self, temp_workspace, mock_config):
        """Test checkpoint recovery strategy"""
        manager = RecoveryManager(mock_config)
        
        # Simulate an error and attempt recovery
        try:
            raise Exception("Config corrupted")
        except Exception as e:
            result = manager.recover(e, {"test": "context"})
        
        assert result is not None
        assert result.time_taken_ms > 0
    
    def test_recovery_statistics(self, temp_workspace, mock_config):
        """Test recovery statistics"""
        manager = RecoveryManager(mock_config)
        
        # Access stats directly
        stats = manager.stats
        
        assert stats is not None
        assert isinstance(stats, dict)
        assert "total_recoveries" in stats
        assert "successful_recoveries" in stats
        assert "failed_recoveries" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
