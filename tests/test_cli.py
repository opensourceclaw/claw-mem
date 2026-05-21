# Copyright 2026 Peter Cheng
"""Tests for cli.py - Command Line Interface"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claw_mem import cli


class TestCLI:
    """Test CLI functionality"""

    def test_main_no_args(self):
        """Test main CLI with no arguments"""
        with patch.object(sys, "argv", ["claw-mem"]):
            with patch("claw_mem.cli.main") as mock_main:
                cli.main()

    def test_main_help(self):
        """Test main CLI with --help"""
        with patch.object(sys, "argv", ["claw-mem", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0

    def test_main_version(self):
        """Test main CLI with --version"""
        with patch.object(sys, "argv", ["claw-mem", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0

    def test_cmd_stats_json(self):
        """Test stats command with JSON output"""
        args = MagicMock()
        args.command = "stats"
        args.json = True
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            with patch("claw_mem.memory_manager.MemoryManager") as mock_mm:
                mock_detector.detect_workspace.return_value = "/test/workspace"
                mock_mm_instance = MagicMock()
                mock_mm_instance.get_stats.return_value = {
                    "workspace": "/test/workspace",
                    "session_id": "test-session",
                    "working_memory_count": 10,
                    "working_cache_size": 100,
                    "index_built": True,
                    "episodic_count": 50,
                    "semantic_count": 30,
                    "procedural_count": 20,
                }
                mock_mm.return_value = mock_mm_instance
                
                cli.cmd_stats(args)
                
                mock_mm_instance.get_stats.assert_called_once()

    def test_cmd_stats_text(self):
        """Test stats command with text output"""
        args = MagicMock()
        args.command = "stats"
        args.json = False
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            with patch("claw_mem.memory_manager.MemoryManager") as mock_mm:
                mock_detector.detect_workspace.return_value = "/test/workspace"
                mock_mm_instance = MagicMock()
                mock_mm_instance.get_stats.return_value = {
                    "workspace": "/test/workspace",
                    "session_id": None,
                    "working_memory_count": 0,
                    "working_cache_size": 0,
                    "index_built": False,
                    "episodic_count": 0,
                    "semantic_count": 0,
                    "procedural_count": 0,
                }
                mock_mm.return_value = mock_mm_instance
                
                # Should not raise
                cli.cmd_stats(args)

    def test_cmd_search_json(self):
        """Test search command with JSON output"""
        args = MagicMock()
        args.command = "search"
        args.query = "test query"
        args.limit = 10
        args.layers = "l1,l2,l3"
        args.json = True
        
        # Create mock result
        mock_result = MagicMock()
        mock_result.to_dict.return_value = {
            "content": "test content",
            "layer": "l1",
            "score": 0.9,
        }
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            with patch("claw_mem.cli.ThreeTierRetriever") as mock_retriever:
                mock_detector.detect_workspace.return_value = "/test/workspace"
                mock_retriever_instance = MagicMock()
                mock_retriever_instance.search.return_value = [mock_result]
                mock_retriever.return_value = mock_retriever_instance
                
                cli.cmd_search(args)
                
                mock_retriever_instance.search.assert_called_once()

    def test_cmd_search_text(self):
        """Test search command with text output"""
        args = MagicMock()
        args.command = "search"
        args.query = "test query"
        args.limit = 5
        args.layers = "l1,l2"
        args.json = False
        
        # Create mock result
        mock_result = MagicMock()
        mock_result.content = "test content"
        mock_result.layer.value = "l1"
        mock_result.score = 0.9
        mock_result.source = "memory/test.md"
        mock_result.tags = ["tag1", "tag2"]
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            with patch("claw_mem.cli.ThreeTierRetriever") as mock_retriever:
                mock_detector.detect_workspace.return_value = "/test/workspace"
                mock_retriever_instance = MagicMock()
                mock_retriever_instance.search.return_value = [mock_result]
                mock_retriever.return_value = mock_retriever_instance
                
                # Should not raise
                cli.cmd_search(args)

    def test_cmd_search_empty_results(self):
        """Test search command with no results"""
        args = MagicMock()
        args.command = "search"
        args.query = "nonexistent"
        args.limit = 10
        args.layers = "l1,l2,l3"
        args.json = False
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            with patch("claw_mem.cli.ThreeTierRetriever") as mock_retriever:
                mock_detector.detect_workspace.return_value = "/test/workspace"
                mock_retriever_instance = MagicMock()
                mock_retriever_instance.search.return_value = []
                mock_retriever.return_value = mock_retriever_instance
                
                # Should not raise
                cli.cmd_search(args)

    def test_cmd_backup(self):
        """Test backup command"""
        args = MagicMock()
        args.command = "backup"
        args.output = None
        
        # Should not raise
        cli.cmd_backup(args)

    def test_cmd_backup_custom_output(self):
        """Test backup command with custom output"""
        args = MagicMock()
        args.command = "backup"
        args.output = "/custom/path/backup.zip"
        
        # Should not raise
        cli.cmd_backup(args)

    def test_cmd_restore(self):
        """Test restore command"""
        args = MagicMock()
        args.command = "restore"
        args.file = "/path/to/backup.zip"
        
        # Should not raise
        cli.cmd_restore(args)

    def test_subparser_commands(self):
        """Test that all subparsers are set up correctly"""
        # This tests the argparse setup by parsing --help
        with patch.object(sys, "argv", ["claw-mem", "stats", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0

    def test_search_subparser(self):
        """Test search subparser setup"""
        with patch.object(sys, "argv", ["claw-mem", "search", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                cli.main()
            assert exc_info.value.code == 0


class TestCLIErrorHandling:
    """Test CLI error handling"""

    def test_stats_workspace_error(self, capsys):
        """Test stats command with workspace detection error"""
        args = MagicMock()
        args.command = "stats"
        args.json = False
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            mock_detector.detect_workspace.side_effect = Exception("Workspace not found")
            
            with pytest.raises(SystemExit) as exc_info:
                cli.cmd_stats(args)
            assert exc_info.value.code == 1

    def test_search_workspace_error(self, capsys):
        """Test search command with workspace detection error"""
        args = MagicMock()
        args.command = "search"
        args.query = "test"
        args.limit = 10
        args.layers = "l1,l2,l3"
        args.json = False
        
        with patch("claw_mem.cli.ConfigDetector") as mock_detector:
            mock_detector.detect_workspace.side_effect = Exception("Workspace not found")
            
            with pytest.raises(SystemExit) as exc_info:
                cli.cmd_search(args)
            assert exc_info.value.code == 1
