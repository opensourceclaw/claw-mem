"""
Tests for ProceduralStorage

Tests procedural memory storage and retrieval.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from claw_mem.storage.procedural import ProceduralStorage


class TestProceduralStorage:
    """Test procedural memory storage"""
    
    def test_store_basic(self):
        """Test storing basic procedural memory"""
        workspace = Path(tempfile.mkdtemp())
        procedural = ProceduralStorage(workspace)
        
        memory_record = {
            "name": "How to make coffee",
            "steps": ["Boil water", "Add coffee", "Wait 3 minutes"]
        }
        
        procedural.store(memory_record)
        
        count = procedural.count()
        assert count >= 1
        
        shutil.rmtree(workspace)
    
    def test_get_all(self):
        """Test getting all procedures"""
        workspace = Path(tempfile.mkdtemp())
        procedural = ProceduralStorage(workspace)
        
        procedural.store({"name": "Procedure 1", "steps": ["step1"]})
        procedural.store({"name": "Procedure 2", "steps": ["step2"]})
        
        all_memories = procedural.get_all()
        
        assert len(all_memories) >= 2
        
        shutil.rmtree(workspace)
    
    def test_count(self):
        """Test procedure count"""
        workspace = Path(tempfile.mkdtemp())
        procedural = ProceduralStorage(workspace)
        
        procedural.store({"name": "Procedure 1", "steps": ["step1"]})
        procedural.store({"name": "Procedure 2", "steps": ["step2"]})
        
        count = procedural.count()
        
        assert count >= 2
        
        shutil.rmtree(workspace)
