"""
Tests for Errors

Tests custom exception classes and error formatting.
"""

import pytest
from claw_mem.errors import (
    ValidationError,
    ConfigurationError,
    MemoryRetrievalError,
    MemoryCorruptedError,
    WorkspaceNotFoundError,
    PermissionDeniedError,
    IndexNotFoundError,
    FriendlyError,
    NetworkError,
    DependencyError,
    get_error_documentation
)


class TestFriendlyError:
    """Test base FriendlyError class"""
    
    def test_simple_message(self):
        """Test simple message only"""
        error = FriendlyError("Simple error message")
        assert "Simple error message" in str(error)
        assert "[Error]" in str(error)
    
    def test_error_with_suggestion(self):
        """Test error with suggestion"""
        error = FriendlyError(
            message="Error message",
            suggestion="Try doing X"
        )
        assert "Error message" in str(error)
        assert "Try doing X" in str(error)
        assert "[Suggestion]" in str(error)
    
    def test_error_with_error_code(self):
        """Test error with error code"""
        error = FriendlyError(
            message="Error message",
            error_code="ERROR_001"
        )
        assert "ERROR_001" in str(error)
        assert "[Error Code]" in str(error)
    
    def test_error_with_details(self):
        """Test error with details"""
        error = FriendlyError(
            message="Error message",
            details="Additional details here"
        )
        assert "Additional details here" in str(error)
        assert "[Details]" in str(error)
    
    def test_error_format_method(self):
        """Test format() method"""
        error = FriendlyError(
            message="Test",
            suggestion="Fix it",
            error_code="E001",
            details="Details"
        )
        formatted = error.format()
        assert "[Error] Test" in formatted
        assert "[Suggestion] Fix it" in formatted
        assert "[Error Code] E001" in formatted
        assert "[Details] Details" in formatted
    
    def test_backward_compatibility(self):
        """Test backward compatibility for simple message"""
        error = FriendlyError("Simple message")
        assert error.message == "Simple message"
        assert error.suggestion is None
        assert error.error_code is None
        assert error.details is None


class TestErrors:
    """Test custom error classes"""
    
    def test_validation_error_simple(self):
        """Test ValidationError with simple message"""
        with pytest.raises(ValidationError):
            raise ValidationError("Test validation error")
    
    def test_validation_error_detailed(self):
        """Test ValidationError with detailed parameters"""
        error = ValidationError(
            field="email",
            value="invalid",
            reason="Not a valid email format",
            suggestion="Use format: user@example.com"
        )
        assert "email" in str(error)
        assert "invalid" in str(error)
        assert "Not a valid email format" in str(error)
        assert "user@example.com" in str(error)
    
    def test_validation_error_kwargs(self):
        """Test ValidationError with kwargs"""
        error = ValidationError(
            field="age",
            value="-5",
            reason="Must be positive",
            suggestion="Use positive numbers"
        )
        assert error.message == "Validation failed: age"
        assert "-5" in str(error)
    
    def test_configuration_error_simple(self):
        """Test ConfigurationError with simple message"""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test configuration error")
    
    def test_configuration_error_detailed(self):
        """Test ConfigurationError with detailed parameters"""
        error = ConfigurationError(
            config_key="max_results",
            current_value="-1",
            suggestion="Use positive number"
        )
        assert "max_results" in str(error)
        assert "-1" in str(error)
        assert "positive number" in str(error)
    
    def test_configuration_error_kwargs(self):
        """Test ConfigurationError with kwargs"""
        error = ConfigurationError(
            config_key="timeout",
            current_value="0",
            suggestion="Use timeout > 0"
        )
        assert error.message == "Configuration item 'timeout' is invalid"
    
    def test_memory_retrieval_error(self):
        """Test MemoryRetrievalError"""
        with pytest.raises(MemoryRetrievalError):
            raise MemoryRetrievalError("Test retrieval error")
        
        error = MemoryRetrievalError("test query")
        assert "test query" in str(error)
    
    def test_memory_corrupted_error(self):
        """Test MemoryCorruptedError"""
        with pytest.raises(MemoryCorruptedError):
            raise MemoryCorruptedError("Test corrupted error")
        
        error = MemoryCorruptedError("/path/to/file.md")
        assert "/path/to/file.md" in str(error)
        assert "MEMORY_CORRUPTED" in str(error)
    
    def test_workspace_not_found_error(self):
        """Test WorkspaceNotFoundError"""
        with pytest.raises(WorkspaceNotFoundError):
            raise WorkspaceNotFoundError("Test workspace not found")
        
        error = WorkspaceNotFoundError([
            "~/.openclaw/workspace",
            "~/.config/openclaw/workspace"
        ])
        assert "~/.openclaw/workspace" in str(error)
        assert "WORKSPACE_NOT_FOUND" in str(error)
    
    def test_permission_denied_error(self):
        """Test PermissionDeniedError"""
        with pytest.raises(PermissionDeniedError):
            raise PermissionDeniedError("Test permission denied")
        
        error = PermissionDeniedError("/restricted/path")
        assert "/restricted/path" in str(error)
        assert "PERMISSION_DENIED" in str(error)
    
    def test_index_not_found_error(self):
        """Test IndexNotFoundError"""
        error = IndexNotFoundError("~/.claw-mem/index.pkl.gz")
        assert "~/.claw-mem/index.pkl.gz" in str(error)
        assert "INDEX_NOT_FOUND" in str(error)
        assert "rebuilding" in str(error)
    
    def test_network_error(self):
        """Test NetworkError"""
        error = NetworkError("https://api.example.com")
        assert "https://api.example.com" in str(error)
        assert "NETWORK_ERROR" in str(error)
        assert "Network connection failed" in str(error)
    
    def test_dependency_error(self):
        """Test DependencyError"""
        error = DependencyError("jieba")
        assert "jieba" in str(error)
        assert "DEPENDENCY_ERROR" in str(error)
        assert "pip install jieba" in str(error)
    
    def test_error_inheritance(self):
        """Test error inheritance"""
        assert issubclass(ValidationError, Exception)
        assert issubclass(ConfigurationError, Exception)
        assert issubclass(MemoryRetrievalError, Exception)
        assert issubclass(MemoryCorruptedError, Exception)
        assert issubclass(WorkspaceNotFoundError, Exception)
        assert issubclass(PermissionDeniedError, Exception)
        assert issubclass(IndexNotFoundError, Exception)
        assert issubclass(NetworkError, Exception)
        assert issubclass(DependencyError, Exception)
        
        # All errors should inherit from FriendlyError
        assert issubclass(ValidationError, FriendlyError)
        assert issubclass(ConfigurationError, FriendlyError)
        assert issubclass(MemoryRetrievalError, FriendlyError)
        assert issubclass(MemoryCorruptedError, FriendlyError)
        assert issubclass(WorkspaceNotFoundError, FriendlyError)
        assert issubclass(PermissionDeniedError, FriendlyError)
        assert issubclass(IndexNotFoundError, FriendlyError)
        assert issubclass(NetworkError, FriendlyError)
        assert issubclass(DependencyError, FriendlyError)


class TestErrorDocumentation:
    """Test error documentation system"""
    
    def test_get_error_documentation_valid(self):
        """Test get_error_documentation with valid error code"""
        doc = get_error_documentation("INDEX_NOT_FOUND")
        assert "Error Code: INDEX_NOT_FOUND" in doc
        assert "Description:" in doc
        assert "Cause:" in doc
        assert "Solution:" in doc
    
    def test_get_error_documentation_invalid(self):
        """Test get_error_documentation with invalid error code"""
        doc = get_error_documentation("INVALID_CODE")
        assert "has no documentation yet" in doc
    
    def test_all_error_codes_have_documentation(self):
        """Test that all error codes have documentation"""
        error_codes = [
            "INDEX_NOT_FOUND",
            "WORKSPACE_NOT_FOUND",
            "MEMORY_CORRUPTED",
            "PERMISSION_DENIED",
            "CONFIGURATION_ERROR",
            "MEMORY_RETRIEVAL_ERROR",
            "VALIDATION_ERROR",
            "NETWORK_ERROR",
            "DEPENDENCY_ERROR"
        ]
        
        for code in error_codes:
            doc = get_error_documentation(code)
            assert "has no documentation yet" not in doc, f"Missing documentation for {code}"
            assert "Description:" in doc
            assert "Cause:" in doc
            assert "Solution:" in doc
