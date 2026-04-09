"""
Tests for Errors

Tests custom exception classes.
"""

import pytest
from claw_mem.errors import (
    ValidationError,
    ConfigurationError,
    MemoryRetrievalError,
    MemoryCorruptedError,
    WorkspaceNotFoundError,
    PermissionDeniedError
)


class TestErrors:
    """Test custom error classes"""
    
    def test_validation_error(self):
        """Test ValidationError"""
        with pytest.raises(ValidationError):
            raise ValidationError("Test validation error")
    
    def test_configuration_error(self):
        """Test ConfigurationError"""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test configuration error")
    
    def test_memory_retrieval_error(self):
        """Test MemoryRetrievalError"""
        with pytest.raises(MemoryRetrievalError):
            raise MemoryRetrievalError("Test retrieval error")
    
    def test_memory_corrupted_error(self):
        """Test MemoryCorruptedError"""
        with pytest.raises(MemoryCorruptedError):
            raise MemoryCorruptedError("Test corrupted error")
    
    def test_workspace_not_found_error(self):
        """Test WorkspaceNotFoundError"""
        with pytest.raises(WorkspaceNotFoundError):
            raise WorkspaceNotFoundError("Test workspace not found")
    
    def test_permission_denied_error(self):
        """Test PermissionDeniedError"""
        with pytest.raises(PermissionDeniedError):
            raise PermissionDeniedError("Test permission denied")
    
    def test_error_inheritance(self):
        """Test error inheritance"""
        assert issubclass(ValidationError, Exception)
        assert issubclass(ConfigurationError, Exception)
        assert issubclass(MemoryRetrievalError, Exception)
        assert issubclass(MemoryCorruptedError, Exception)
        assert issubclass(WorkspaceNotFoundError, Exception)
        assert issubclass(PermissionDeniedError, Exception)
