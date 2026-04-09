"""
Tests for EpisodicStorage

Tests episodic memory storage and retrieval.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from claw_mem.storage.episodic import EpisodicStorage


class TestEpisodicStorage:
    """Test episodic memory storage"""
    
    def test_store_basic(self):
        """Test storing basic episodic memory"""
        workspace = Path(tempfile.mkdtemp())
        episodic = EpisodicStorage(workspace)
        
        memory_record = {
            "content": "User went to the store",
            "session_id": "test-session",
            "timestamp": datetime.now().isoformat()
        }
        
        episodic.store(memory_record)
        
        count = episodic.count()
        assert count >= 1
        
        shutil.rmtree(workspace)
    
    def test_get_all(self):
        """Test getting all episodic memories"""
        workspace = Path(tempfile.mkdtemp())
        episodic = EpisodicStorage(workspace)
        
        episodic.store({"content": "Memory 1", "session_id": "test", "timestamp": datetime.now().isoformat()})
        episodic.store({"content": "Memory 2", "session_id": "test", "timestamp": datetime.now().isoformat()})
        
        all_memories = episodic.get_all()
        
        assert len(all_memories) >= 2
        
        shutil.rmtree(workspace)
    
    def test_count(self):
        """Test memory count"""
        workspace = Path(tempfile.mkdtemp())
        episodic = EpisodicStorage(workspace)
        
        episodic.store({"content": "Memory 1", "session_id": "test", "timestamp": datetime.now().isoformat()})
        episodic.store({"content": "Memory 2", "session_id": "test", "timestamp": datetime.now().isoformat()})
        
        count = episodic.count()
        
        assert count >= 2
        
        shutil.rmtree(workspace)
