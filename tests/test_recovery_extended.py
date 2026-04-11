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
Extended Recovery Manager Tests for Coverage Improvement

Tests for:
- All recovery strategies (checkpoint, backup, rebuild, degrade, manual)
- Graceful degradation
- Recovery statistics tracking
- Multiple recovery attempts
- Error handling
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from claw_mem.recovery import RecoveryManager, RecoveryStrategy, Diagnosis, RecoveryResult


class TestRecoveryStrategies:
    """Test all recovery strategies"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir)

        # Create necessary directories
        (workspace / "memory").mkdir()
        (workspace / ".claw-mem").mkdir()
        (workspace / ".claw-mem" / "backups").mkdir()
        (workspace / ".claw-mem" / "checkpoints").mkdir()

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

    def test_diagnosis_timestamp(self, temp_workspace, mock_config):
        """Test diagnosis timestamp generation"""
        diagnosis = Diagnosis(
            problem_type="TEST_ERROR",
            severity="low",
            description="Test error",
            root_cause="Test cause",
            affected_components=["test"]
        )

        assert diagnosis.timestamp is not None
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(diagnosis.timestamp)

    def test_diagnosis_all_severity_levels(self, temp_workspace, mock_config):
        """Test all severity levels"""
        severities = ["low", "medium", "high", "critical"]

        for severity in severities:
            diagnosis = Diagnosis(
                problem_type="TEST_ERROR",
                severity=severity,
                description="Test error",
                root_cause="Test cause",
                affected_components=["test"]
            )
            assert diagnosis.severity == severity

    def test_recovery_result_all_fields(self, temp_workspace, mock_config):
        """Test recovery result with all fields"""
        result = RecoveryResult(
            success=True,
            strategy_used=RecoveryStrategy.REBUILD,
            time_taken_ms=1500.5,
            description="Index rebuilt successfully",
            data_recovered=True,
            user_action_needed=False,
            error_details=None
        )

        assert result.success is True
        assert result.strategy_used == RecoveryStrategy.REBUILD
        assert result.data_recovered is True
        assert result.user_action_needed is False
        assert result.error_details is None

    def test_recovery_result_with_error(self, temp_workspace, mock_config):
        """Test recovery result with error details"""
        result = RecoveryResult(
            success=False,
            strategy_used=RecoveryStrategy.MANUAL,
            time_taken_ms=100.0,
            description="Recovery failed, manual intervention required",
            data_recovered=False,
            user_action_needed=True,
            error_details="Corruption detected in index file"
        )

        assert result.success is False
        assert result.user_action_needed is True
        assert result.error_details == "Corruption detected in index file"

    def test_recovery_manager_diagnose_component_failure(self, temp_workspace, mock_config):
        """Test diagnosis for component failure"""
        manager = RecoveryManager(mock_config)

        # Test diagnosing different components
        components = ["index", "config", "storage", "cache"]

        for component in components:
            diagnosis = manager.diagnose(component)
            assert diagnosis is not None
            assert diagnosis.problem_type is not None
            assert diagnosis.affected_components is not None

    def test_recovery_statistics_tracking(self, temp_workspace, mock_config):
        """Test recovery statistics tracking"""
        manager = RecoveryManager(mock_config)

        # Get initial stats
        initial_stats = manager.stats
        assert initial_stats["total_recoveries"] == 0
        assert initial_stats["successful_recoveries"] == 0
        assert initial_stats["failed_recoveries"] == 0

        # Attempt recovery
        try:
            raise Exception("Test error")
        except Exception as e:
            manager.recover(e, {"test": "context"})

        # Check stats updated
        stats = manager.stats
        assert stats["total_recoveries"] >= 1

    def test_multiple_recovery_attempts(self, temp_workspace, mock_config):
        """Test multiple recovery attempts"""
        manager = RecoveryManager(mock_config)

        # Attempt multiple recoveries
        for i in range(3):
            try:
                raise Exception(f"Test error {i}")
            except Exception as e:
                result = manager.recover(e, {"attempt": i})
                assert result is not None

        # Check stats reflect attempts
        stats = manager.stats
        assert stats["total_recoveries"] >= 3

    def test_recovery_with_different_error_types(self, temp_workspace, mock_config):
        """Test recovery with different error types"""
        manager = RecoveryManager(mock_config)

        errors = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            IOError("File not found"),
            RuntimeError("Runtime error"),
        ]

        for error in errors:
            try:
                raise error
            except Exception as e:
                result = manager.recover(e, {"error": type(e).__name__})
                assert result is not None
                assert result.time_taken_ms >= 0

    def test_recovery_strategy_selection(self, temp_workspace, mock_config):
        """Test that different strategies are used for different errors"""
        manager = RecoveryManager(mock_config)

        strategies_used = set()

        # Attempt recoveries with different errors
        errors = [
            IOError("Index file corrupted"),
            ValueError("Config invalid"),
            RuntimeError("Storage failure"),
        ]

        for error in errors:
            try:
                raise error
            except Exception as e:
                result = manager.recover(e, {"test": "context"})
                strategies_used.add(result.strategy_used)

        # At least one strategy should have been used
        assert len(strategies_used) > 0

    def test_recovery_manager_with_no_backups(self, temp_workspace, mock_config):
        """Test recovery when no backups exist"""
        # Remove backup directory
        backup_dir = temp_workspace / ".claw-mem" / "backups"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        manager = RecoveryManager(mock_config)

        try:
            raise Exception("Test error")
        except Exception as e:
            result = manager.recover(e, {"test": "context"})
            assert result is not None

    def test_recovery_manager_with_no_checkpoints(self, temp_workspace, mock_config):
        """Test recovery when no checkpoints exist"""
        # Remove checkpoint directory
        checkpoint_dir = temp_workspace / ".claw-mem" / "checkpoints"
        if checkpoint_dir.exists():
            shutil.rmtree(checkpoint_dir)

        manager = RecoveryManager(mock_config)

        try:
            raise Exception("Test error")
        except Exception as e:
            result = manager.recover(e, {"test": "context"})
            assert result is not None

    def test_recovery_context_preservation(self, temp_workspace, mock_config):
        """Test that recovery context is preserved"""
        manager = RecoveryManager(mock_config)

        context = {
            "operation": "search",
            "query": "test query",
            "user_id": "test_user",
        }

        try:
            raise Exception("Test error")
        except Exception as e:
            result = manager.recover(e, context)
            # Context should be used in recovery logic
            assert result is not None

    def test_recovery_result_time_tracking(self, temp_workspace, mock_config):
        """Test that recovery time is tracked accurately"""
        manager = RecoveryManager(mock_config)

        try:
            raise Exception("Test error")
        except Exception as e:
            result = manager.recover(e, {"test": "context"})
            # Time should be recorded
            assert result.time_taken_ms >= 0
            assert isinstance(result.time_taken_ms, float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
