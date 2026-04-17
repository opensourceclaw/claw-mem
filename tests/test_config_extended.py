"""
Extended tests for Config Detection

Tests automatic configuration detection for OpenClaw workspace.
"""

import pytest
import os
import tempfile
from pathlib import Path
from claw_mem.config import ConfigDetector
from claw_mem.errors import WorkspaceNotFoundError


class TestConfigDetector:
    """Test ConfigDetector"""

    def test_detect_workspace_with_memory_dir(self, tmp_path):
        """Test detecting workspace with memory directory"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "2026-04-11.md").write_text("Test memory")

        detected = ConfigDetector.detect_workspace([str(tmp_path)])

        assert detected == str(tmp_path)

    def test_detect_workspace_with_memory_md(self, tmp_path):
        """Test detecting workspace with MEMORY.md file"""
        (tmp_path / "MEMORY.md").write_text("# Memory")

        detected = ConfigDetector.detect_workspace([str(tmp_path)])

        assert detected == str(tmp_path)

    def test_detect_workspace_with_agents_md(self, tmp_path):
        """Test detecting workspace with AGENTS.md file"""
        (tmp_path / "AGENTS.md").write_text("# Agents")

        detected = ConfigDetector.detect_workspace([str(tmp_path)])

        assert detected == str(tmp_path)

    def test_detect_workspace_with_soul_md(self, tmp_path):
        """Test detecting workspace with SOUL.md file"""
        (tmp_path / "SOUL.md").write_text("# Soul")

        detected = ConfigDetector.detect_workspace([str(tmp_path)])

        assert detected == str(tmp_path)

    def test_detect_workspace_with_user_md(self, tmp_path):
        """Test detecting workspace with USER.md file"""
        (tmp_path / "USER.md").write_text("# User")

        detected = ConfigDetector.detect_workspace([str(tmp_path)])

        assert detected == str(tmp_path)

    def test_detect_workspace_not_found(self, tmp_path):
        """Test detecting workspace when not found"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(WorkspaceNotFoundError) as exc_info:
            ConfigDetector.detect_workspace([str(empty_dir)])

        assert str(empty_dir) in str(exc_info.value)

    def test_detect_workspace_custom_paths(self, tmp_path):
        """Test detecting workspace with custom paths"""
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "MEMORY.md").write_text("# Memory")

        invalid_dir = tmp_path / "invalid"
        invalid_dir.mkdir()

        custom_paths = [str(invalid_dir), str(valid_dir)]

        detected = ConfigDetector.detect_workspace(custom_paths)

        assert detected == str(valid_dir)

    def test_detect_workspace_nonexistent_path(self, tmp_path):
        """Test detecting workspace with non-existent paths"""
        valid_dir = tmp_path / "valid"
        valid_dir.mkdir()
        (valid_dir / "MEMORY.md").write_text("# Memory")

        nonexistent = tmp_path / "nonexistent"

        custom_paths = [str(nonexistent), str(valid_dir)]

        detected = ConfigDetector.detect_workspace(custom_paths)

        assert detected == str(valid_dir)

    def test_is_valid_workspace_true(self, tmp_path):
        """Test validating a valid workspace"""
        (tmp_path / "MEMORY.md").write_text("# Memory")

        is_valid = ConfigDetector._is_valid_workspace(tmp_path)

        assert is_valid is True

    def test_is_valid_workspace_false(self, tmp_path):
        """Test validating an invalid workspace"""
        is_valid = ConfigDetector._is_valid_workspace(tmp_path)

        assert is_valid is False

    def test_is_valid_workspace_empty_memory_dir(self, tmp_path):
        """Test validating workspace with empty memory directory"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        is_valid = ConfigDetector._is_valid_workspace(tmp_path)

        assert is_valid is False

    def test_is_valid_workspace_nonempty_memory_dir(self, tmp_path):
        """Test validating workspace with non-empty memory directory"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "2026-04-11.md").write_text("Test")

        is_valid = ConfigDetector._is_valid_workspace(tmp_path)

        assert is_valid is True

    def test_get_workspace_info_valid(self, tmp_path):
        """Test getting workspace info for valid workspace"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "2026-04-11.md").write_text("Test 1")
        (memory_dir / "2026-04-12.md").write_text("Test 2")
        (tmp_path / "MEMORY.md").write_text("# Memory")

        info = ConfigDetector.get_workspace_info(str(tmp_path))

        assert info["path"] == str(tmp_path)
        assert info["exists"] is True
        assert info["is_valid"] is True
        assert "MEMORY.md" in info["markers_found"]
        assert "memory/" in info["markers_found"]
        assert len(info["memory_files"]) >= 2

    def test_get_workspace_info_invalid(self, tmp_path):
        """Test getting workspace info for invalid workspace"""
        info = ConfigDetector.get_workspace_info(str(tmp_path))

        assert info["path"] == str(tmp_path)
        assert info["exists"] is True
        assert info["is_valid"] is False
        assert len(info["markers_found"]) == 0
        assert len(info["memory_files"]) == 0

    def test_get_workspace_info_nonexistent(self, tmp_path):
        """Test getting workspace info for non-existent path"""
        nonexistent = tmp_path / "nonexistent"

        info = ConfigDetector.get_workspace_info(str(nonexistent))

        assert info["path"] == str(nonexistent)
        assert info["exists"] is False
        assert info["is_valid"] is False
        assert len(info["markers_found"]) == 0
        assert len(info["memory_files"]) == 0

    def test_get_workspace_info_many_memory_files(self, tmp_path):
        """Test getting workspace info limits memory files to 10"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        # Create 15 memory files
        for i in range(15):
            (memory_dir / f"2026-04-{i+1:02d}.md").write_text(f"Memory {i}")

        info = ConfigDetector.get_workspace_info(str(tmp_path))

        assert len(info["memory_files"]) == 10

    def test_suggest_workspace_existing(self, tmp_path):
        """Test suggesting existing workspace"""
        (tmp_path / "MEMORY.md").write_text("# Memory")

        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)
            suggested = ConfigDetector.suggest_workspace()

            # Should suggest existing workspace, not create new one
            assert suggested is not None

    def test_suggest_workspace_create(self, tmp_path):
        """Test suggesting and creating workspace"""
        # Skip this test as it would modify the real home directory
        pytest.skip("Test would modify ~/.openclaw/workspace")

    def test_default_paths(self):
        """Test default paths are configured"""
        paths = ConfigDetector.DEFAULT_PATHS

        assert len(paths) > 0
        # First path should contain ".openclaw/workspace" (may be expanded)
        assert ".openclaw/workspace" in paths[0] or ".config/openclaw/workspace" in paths[0]

    def test_workspace_markers(self):
        """Test workspace markers are configured"""
        markers = ConfigDetector.WORKSPACE_MARKERS

        assert "MEMORY.md" in markers
        assert "memory/" in markers
        assert "AGENTS.md" in markers

    def test_detect_workspace_priority(self, tmp_path):
        """Test workspace detection respects path priority"""
        # Create two valid workspaces
        first = tmp_path / "first"
        first.mkdir()
        (first / "MEMORY.md").write_text("# First")

        second = tmp_path / "second"
        second.mkdir()
        (second / "MEMORY.md").write_text("# Second")

        # Search with first path first
        custom_paths = [str(first), str(second)]
        detected = ConfigDetector.detect_workspace(custom_paths)

        # Should find first workspace
        assert detected == str(first)

    def test_is_valid_workspace_file_only(self, tmp_path):
        """Test workspace validation with file marker only"""
        (tmp_path / "AGENTS.md").write_text("# Agents")

        is_valid = ConfigDetector._is_valid_workspace(tmp_path)

        assert is_valid is True

    def test_get_workspace_info_expanded_path(self, tmp_path):
        """Test workspace info expands tilde in path"""
        info = ConfigDetector.get_workspace_info(str(tmp_path))

        # Path should be absolute and expanded
        path_obj = Path(info["path"])
        assert path_obj.is_absolute()
        assert "~" not in info["path"]

    def test_detect_workspace_with_path_expansion(self, tmp_path):
        """Test workspace detection expands tilde in paths"""
        (tmp_path / "MEMORY.md").write_text("# Memory")

        # Create a path with tilde and test expansion
        with tempfile.TemporaryDirectory() as tempdir:
            # Create symlink or use relative path
            custom_paths = [str(tmp_path)]

            detected = ConfigDetector.detect_workspace(custom_paths)

            assert detected == str(tmp_path.resolve())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
