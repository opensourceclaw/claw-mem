"""
Tests for SemanticStorage

Tests semantic memory storage and retrieval.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from claw_mem.storage.semantic import SemanticStorage


class TestSemanticStorage:
    """Test semantic memory storage"""
    
    def test_store_basic(self):
        """Test storing basic semantic memory"""
        workspace = Path(tempfile.mkdtemp())
        semantic = SemanticStorage(workspace)
        
        memory_record = {
            "content": "The user likes pizza",
            "type": "preference"
        }
        
        semantic.store(memory_record)
        
        count = semantic.count()
        assert count >= 1
        
        shutil.rmtree(workspace)
    
    def test_store_with_metadata(self):
        """Test storing with metadata"""
        workspace = Path(tempfile.mkdtemp())
        semantic = SemanticStorage(workspace)
        
        memory_record = {
            "content": "The user's favorite color is blue",
            "type": "preference",
            "confidence": 0.9
        }
        
        semantic.store(memory_record)
        
        count = semantic.count()
        assert count >= 1
        
        shutil.rmtree(workspace)
    
    def test_get_all(self):
        """Test getting all memories"""
        workspace = Path(tempfile.mkdtemp())
        semantic = SemanticStorage(workspace)
        
        semantic.store({"content": "Memory 1"})
        semantic.store({"content": "Memory 2"})
        
        all_memories = semantic.get_all()
        
        assert len(all_memories) >= 2
        
        shutil.rmtree(workspace)
    
    def test_count(self):
        """Test memory count"""
        workspace = Path(tempfile.mkdtemp())
        semantic = SemanticStorage(workspace)
        
        semantic.store({"content": "Memory 1"})
        semantic.store({"content": "Memory 2"})
        semantic.store({"content": "Memory 3"})
        
        count = semantic.count()
        
        assert count >= 3
        
        shutil.rmtree(workspace)
