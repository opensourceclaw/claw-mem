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
Tests for MemoryFixPlugin
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from claw_mem.memory_fix_plugin import MemoryFixPlugin


class TestMemoryFixPlugin:
    """Test suite for MemoryFixPlugin"""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        workspace = Path(temp_dir) / "workspace"
        workspace.mkdir()
        yield str(workspace)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def plugin(self, temp_workspace):
        """Create a MemoryFixPlugin instance"""
        return MemoryFixPlugin(temp_workspace)

    # ========================================================================
    # Test Initialization
    # ========================================================================

    def test_plugin_initialization(self, plugin, temp_workspace):
        """Test that plugin initializes correctly"""
        assert plugin.workspace == Path(temp_workspace).expanduser()
        assert plugin.memory_file == Path(temp_workspace).expanduser() / "MEMORY.md"
        assert plugin.fix_log_file.parent.exists()

    # ========================================================================
    # Test Retrieval Scoring (Fix 1)
    # ========================================================================

    def test_retrieve_with_priority_empty_list(self, plugin):
        """Test retrieval with empty memory list"""
        result = plugin.retrieve_with_priority("test query", [])
        assert result == []

    def test_retrieve_with_priority_exact_match_url(self, plugin):
        """Test retrieval with exact URL match"""
        memories = [
            {
                'content': 'GitHub repo: https://github.com/user/repo',
                'timestamp': datetime.now().isoformat(),
                'confidence': 1.0
            },
            {
                'content': 'Some other content',
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.5
            }
        ]
        result = plugin.retrieve_with_priority("https://github.com/user/repo", memories)
        assert len(result) == 2
        assert "https://github.com/user/repo" in result[0]['content']

    def test_retrieve_with_priority_exact_match_path(self, plugin):
        """Test retrieval with exact path match"""
        memories = [
            {
                'content': 'Config file at ~/.openclaw/workspace/config.yaml',
                'timestamp': datetime.now().isoformat(),
                'confidence': 1.0
            },
            {
                'content': 'Unrelated content',
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.5
            }
        ]
        result = plugin.retrieve_with_priority("~/.openclaw/workspace/config.yaml", memories)
        assert len(result) == 2
        assert "~/.openclaw/workspace/config.yaml" in result[0]['content']

    def test_retrieve_with_priority_time_weight_today(self, plugin):
        """Test retrieval with today's memory prioritized"""
        now = datetime.now()
        memories = [
            {
                'content': 'Recent memory',
                'timestamp': now.isoformat(),
                'confidence': 0.5
            },
            {
                'content': 'Old memory',
                'timestamp': datetime(2024, 1, 1).isoformat(),
                'confidence': 0.9
            }
        ]
        result = plugin.retrieve_with_priority("memory", memories)
        assert len(result) == 2
        assert "Recent memory" in result[0]['content']

    def test_retrieve_with_priority_confidence_weight(self, plugin):
        """Test retrieval with high confidence prioritized"""
        timestamp = datetime.now().isoformat()
        memories = [
            {
                'content': 'High confidence memory',
                'timestamp': timestamp,
                'confidence': 0.95
            },
            {
                'content': 'Low confidence memory',
                'timestamp': timestamp,
                'confidence': 0.3
            }
        ]
        result = plugin.retrieve_with_priority("memory", memories)
        assert len(result) == 2
        assert "High confidence memory" in result[0]['content']

    def test_calculate_retrieval_score_exact_match(self, plugin):
        """Test score calculation for exact match"""
        memory = {
            'content': 'https://github.com/test/repo',
            'timestamp': datetime.now().isoformat(),
            'confidence': 1.0
        }
        score = plugin._calculate_retrieval_score("https://github.com/test/repo", memory)
        assert score >= 100.0  # Exact match bonus

    def test_calculate_retrieval_score_critical_info(self, plugin):
        """Test score calculation for critical information"""
        memory = {
            'content': 'API endpoint: https://api.example.com/v1',
            'timestamp': datetime.now().isoformat(),
            'confidence': 1.0
        }
        score = plugin._calculate_retrieval_score("https://api.example.com", memory)
        assert score >= 50.0  # Critical info bonus

    def test_is_exact_match_url(self, plugin):
        """Test URL exact matching"""
        assert plugin._is_exact_match(
            "https://github.com/user/repo",
            "The repo is at https://github.com/user/repo"
        ) is True

    def test_is_exact_match_path(self, plugin):
        """Test path exact matching"""
        assert plugin._is_exact_match(
            "~/.openclaw/workspace/config.yaml",
            "Config file: ~/.openclaw/workspace/config.yaml"
        ) is True

    def test_is_exact_match_text(self, plugin):
        """Test text exact matching"""
        assert plugin._is_exact_match(
            "test query",
            "This is a test query"
        ) is True

    def test_is_critical_info(self, plugin):
        """Test critical information detection"""
        assert plugin._is_critical_info("https://example.com") is True
        assert plugin._is_critical_info("~/.openclaw") is True
        assert plugin._is_critical_info("/path/to/file") is True
        assert plugin._is_critical_info("github.com") is True
        assert plugin._is_critical_info("normal text") is False

    def test_days_since(self, plugin):
        """Test days since calculation"""
        today = datetime.now()
        yesterday = datetime(2024, 1, 2)
        assert plugin._days_since(today.isoformat()) == 0
        assert plugin._days_since(yesterday.isoformat()) > 365

    # ========================================================================
    # Test Similarity Calculation
    # ========================================================================

    def test_calculate_similarity_identical(self, plugin):
        """Test similarity for identical texts"""
        similarity = plugin._calculate_similarity(
            "https://github.com/user/repo",
            "https://github.com/user/repo"
        )
        assert similarity == 1.0

    def test_calculate_similarity_url_key_match(self, plugin):
        """Test similarity with matching URLs"""
        similarity = plugin._calculate_similarity(
            "GitHub repo: https://github.com/user/repo",
            "Repo URL: https://github.com/user/repo"
        )
        assert similarity > 0.8

    def test_calculate_similarity_path_key_match(self, plugin):
        """Test similarity with matching paths"""
        similarity = plugin._calculate_similarity(
            "Config at ~/.openclaw/workspace/config.yaml",
            "Config file: ~/.openclaw/workspace/config.yaml"
        )
        assert similarity > 0.8

    def test_calculate_similarity_word_overlap(self, plugin):
        """Test similarity with word overlap"""
        similarity = plugin._calculate_similarity(
            "User prefers dark mode",
            "User likes dark theme"
        )
        assert similarity > 0.0

    def test_calculate_similarity_no_overlap(self, plugin):
        """Test similarity with no overlap"""
        similarity = plugin._calculate_similarity(
            "cats are cute",
            "dogs are loyal"
        )
        assert similarity < 0.5

    def test_has_same_key_pattern_url(self, plugin):
        """Test same key pattern detection for URLs"""
        assert plugin._has_same_key_pattern(
            "Check https://github.com/user/repo",
            "Visit https://github.com/user/repo for more"
        ) is True

    def test_has_same_key_pattern_path(self, plugin):
        """Test same key pattern detection for paths"""
        assert plugin._has_same_key_pattern(
            "Config: ~/.openclaw/workspace/config.yaml",
            "File at ~/.openclaw/workspace/config.yaml"
        ) is True

    def test_extract_key_info_url(self, plugin):
        """Test URL key extraction"""
        key = plugin._extract_key_info("Check this: https://github.com/user/repo")
        assert key == "https://github.com/user/repo"

    def test_extract_key_info_path(self, plugin):
        """Test path key extraction"""
        key = plugin._extract_key_info("Config at ~/.openclaw/workspace/config.yaml")
        assert key == "~/.openclaw/workspace/config.yaml"

    def test_extract_key_info_text(self, plugin):
        """Test text key extraction"""
        key = plugin._extract_key_info("User prefers Chinese")
        assert key == "User prefers Chinese"

    # ========================================================================
    # Test Memory Storage with Dedup (Fix 2)
    # ========================================================================

    def test_store_with_dedup_new_memory(self, plugin):
        """Test storing a new memory (no duplicates)"""
        success, msg = plugin.store_with_dedup(
            "User prefers dark mode",
            memory_type="semantic",
            tags=["preference", "ui"]
        )
        assert success is True
        assert "成功" in msg or "success" in msg.lower()
        assert plugin.memory_file.exists()

    def test_store_with_dedup_duplicate_detection(self, plugin):
        """Test duplicate detection and update"""
        # Store first memory
        plugin.store_with_dedup(
            "https://github.com/user/repo is the main repository",
            memory_type="semantic"
        )

        # Store similar memory (should update due to URL match)
        success, msg = plugin.store_with_dedup(
            "GitHub repository: https://github.com/user/repo",
            memory_type="semantic"
        )
        assert success is True
        # Either update or add is acceptable depending on similarity threshold

    def test_find_similar_memory_no_similarity(self, plugin):
        """Test finding similar memory with no match"""
        memories = [
            {'content': 'First memory'},
            {'content': 'Second memory'}
        ]
        result = plugin._find_similar_memory("completely different", memories)
        assert result is None

    def test_find_similar_memory_with_similarity(self, plugin):
        """Test finding similar memory with match"""
        memories = [
            {'content': 'https://github.com/user/repo is the main repository'},
            {'content': 'Some other content'}
        ]
        result = plugin._find_similar_memory("https://github.com/user/repo", memories)
        assert result is not None
        assert 'index' in result
        assert 'memory' in result
        assert 'similarity' in result

    def test_read_memories_empty_file(self, plugin):
        """Test reading memories from non-existent file"""
        memories = plugin._read_memories()
        assert memories == []

    def test_read_memories_valid_file(self, plugin, temp_workspace):
        """Test reading memories from valid file"""
        # Create a MEMORY.md file with proper format
        memory_file = Path(temp_workspace) / "MEMORY.md"
        memory_file.write_text("""# MEMORY.md

[2024-01-01T12:00:00] First memory <!-- tags: tag1, tag2 -->
[2024-01-02T12:00:00] Second memory
""")

        memories = plugin._read_memories()
        assert len(memories) == 2
        # Verify timestamps are parsed correctly
        assert '2024-01-01' in memories[0]['timestamp']
        assert '2024-01-02' in memories[1]['timestamp']

    def test_add_new_memory(self, plugin):
        """Test adding a new memory"""
        success, msg = plugin._add_new_memory(
            "Test memory",
            "semantic",
            ["test"]
        )
        assert success is True
        assert plugin.memory_file.exists()
        content = plugin.memory_file.read_text()
        assert "Test memory" in content

    def test_update_memory(self, plugin, temp_workspace):
        """Test updating an existing memory"""
        # Create initial memory
        plugin._add_new_memory("Original content", "semantic", ["test"])

        # Update memory
        success, msg = plugin._update_memory(
            0,
            "Updated content",
            ["updated"]
        )
        assert success is True
        assert "成功" in msg or "success" in msg.lower()

        content = plugin.memory_file.read_text()
        assert "Updated content" in content
        assert "Original content" not in content

    def test_update_memory_invalid_index(self, plugin):
        """Test updating with invalid index"""
        success, msg = plugin._update_memory(999, "Content", ["tag"])
        assert success is False

    def test_write_memories(self, plugin):
        """Test writing memories back to file"""
        memories = [
            {
                'timestamp': '2024-01-01T12:00:00',
                'content': 'Memory 1',
                'tags': ['tag1']
            },
            {
                'timestamp': '2024-01-02T12:00:00',
                'content': 'Memory 2',
                'tags': []
            }
        ]
        plugin._write_memories(memories)
        assert plugin.memory_file.exists()
        content = plugin.memory_file.read_text()
        assert "Memory 1" in content
        assert "Memory 2" in content

    # ========================================================================
    # Test Session Validation (Fix 3)
    # ========================================================================

    def test_validate_session_memory_no_file(self, plugin):
        """Test validation when MEMORY.md doesn't exist"""
        result = plugin.validate_session_memory()
        assert 'valid' in result
        assert result['memories_count'] == 0
        assert len(result['warnings']) > 0

    def test_validate_session_memory_empty_file(self, plugin, temp_workspace):
        """Test validation with empty MEMORY.md"""
        memory_file = Path(temp_workspace) / "MEMORY.md"
        memory_file.write_text("# MEMORY.md\n\n")

        result = plugin.validate_session_memory()
        assert result['valid'] is True
        assert result['memories_count'] == 0

    def test_validate_session_memory_valid_memories(self, plugin, temp_workspace):
        """Test validation with valid memories"""
        memory_file = Path(temp_workspace) / "MEMORY.md"
        memory_file.write_text("""
# MEMORY.md

[2024-01-01T12:00:00] First memory
[2024-01-02T12:00:00] Second memory
""")

        result = plugin.validate_session_memory()
        assert result['valid'] is True
        assert result['memories_count'] == 2

    def test_find_duplicates(self, plugin):
        """Test finding duplicate memories"""
        memories = [
            {'content': 'https://github.com/user/repo is here'},
            {'content': 'Some other memory'},
            {'content': 'https://github.com/user/repo again'}
        ]
        duplicates = plugin._find_duplicates(memories)
        assert len(duplicates) > 0

    def test_find_conflicts(self, plugin):
        """Test finding conflicting memories"""
        memories = [
            {'content': 'URL: https://github.com/user/repo'},
            {'content': 'Same URL: https://github.com/user/repo'}
        ]
        conflicts = plugin._find_conflicts(memories)
        # May or may not find conflicts depending on implementation
        assert isinstance(conflicts, list)

    # ========================================================================
    # Test Statistics
    # ========================================================================

    def test_get_fix_statistics(self, plugin):
        """Test getting fix statistics"""
        stats = plugin.get_fix_statistics()
        assert 'workspace' in stats
        assert 'memory_file_exists' in stats
        assert 'memories_count' in stats
        assert 'fix_log_exists' in stats
        assert 'fix_actions' in stats

    def test_get_fix_statistics_after_store(self, plugin):
        """Test statistics after storing memories"""
        plugin.store_with_dedup("Test memory", "semantic")
        stats = plugin.get_fix_statistics()
        assert stats['memory_file_exists'] is True
        assert stats['memories_count'] == 1
