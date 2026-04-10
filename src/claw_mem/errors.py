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
claw-mem Friendly Error System

All errors are in English with fix suggestions.
Apache 2.0 License - Professional Open Source Style
"""

from typing import Optional


class FriendlyError(Exception):
    """Base class for friendly error messages"""
    
    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[str] = None
    ):
        # Handle simple message-only calls (backward compatibility)
        if isinstance(message, str) and all(arg is None or isinstance(arg, str) 
                                            for arg in [suggestion, error_code, details]):
            self.message = message
            self.suggestion = suggestion
            self.error_code = error_code
            self.details = details
        else:
            # Legacy support: if message looks like args tuple/list
            self.message = str(message)
            self.suggestion = suggestion
            self.error_code = error_code
            self.details = details
        super().__init__(self.format())
    
    def format(self) -> str:
        """Format error message with suggestions and details"""
        output = f"[Error] {self.message}\n"
        
        if self.suggestion:
            output += f"[Suggestion] {self.suggestion}\n"
        
        if self.error_code:
            output += f"[Error Code] {self.error_code}\n"
        
        if self.details:
            output += f"[Details] {self.details}\n"
        
        return output
    
    def __str__(self) -> str:
        return self.format()


# ============================================================================
# Pre-defined Error Types
# ============================================================================

class IndexNotFoundError(FriendlyError):
    """Error raised when memory index file is not found"""
    
    def __init__(self, index_path: str, suggestion: Optional[str] = None):
        super().__init__(
            message="Memory index not found, rebuilding...",
            suggestion=suggestion or "First startup requires index rebuild, please wait (~1 second)",
            error_code="INDEX_NOT_FOUND",
            details=f"Index path: {index_path}"
        )


class WorkspaceNotFoundError(FriendlyError):
    """Error raised when OpenClaw workspace is not found"""
    
    def __init__(self, searched_paths: list, suggestion: Optional[str] = None):
        paths_str = "\n  - ".join(searched_paths)
        super().__init__(
            message="OpenClaw workspace not found",
            suggestion=suggestion or "Please confirm OpenClaw is installed or manually specify workspace path",
            error_code="WORKSPACE_NOT_FOUND",
            details=f"Searched paths:\n  - {paths_str}"
        )


class MemoryCorruptedError(FriendlyError):
    """Error raised when memory file is corrupted"""
    
    def __init__(self, file_path: str, suggestion: Optional[str] = None):
        super().__init__(
            message="Memory file corrupted, attempting recovery from backup...",
            suggestion=suggestion or "System will auto-recover from recent backup. If issue persists, check disk health",
            error_code="MEMORY_CORRUPTED",
            details=f"Corrupted file: {file_path}"
        )


class PermissionDeniedError(FriendlyError):
    """Error raised when file permission is denied"""
    
    def __init__(self, path: str, suggestion: Optional[str] = None):
        super().__init__(
            message="Permission denied, cannot access file",
            suggestion=suggestion or "Please check file permissions or use chmod to modify permissions",
            error_code="PERMISSION_DENIED",
            details=f"Cannot access: {path}"
        )


class ConfigurationError(FriendlyError):
    """Error raised when configuration is invalid"""
    
    def __init__(self, *args, **kwargs):
        # Support both simple message and detailed configuration error
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            # Simple message: ConfigurationError("message")
            super().__init__(
                message=args[0],
                error_code="CONFIGURATION_ERROR"
            )
        else:
            # Detailed configuration error: ConfigurationError(config_key, current_value, suggestion)
            config_key = kwargs.get('config_key', args[0] if args else "unknown")
            current_value = kwargs.get('current_value', args[1] if len(args) > 1 else "")
            suggestion = kwargs.get('suggestion', args[2] if len(args) > 2 else None)
            
            super().__init__(
                message=f"Configuration item '{config_key}' is invalid",
                suggestion=suggestion or "Please check configuration file or run 'claw-mem --help' for available options",
                error_code="CONFIGURATION_ERROR",
                details=f"Current value: {current_value}"
            )


class MemoryRetrievalError(FriendlyError):
    """Error raised when memory retrieval fails"""
    
    def __init__(self, query: str, suggestion: Optional[str] = None):
        super().__init__(
            message="Memory retrieval failed",
            suggestion=suggestion or "Try simplifying search keywords or check if memory file exists",
            error_code="MEMORY_RETRIEVAL_ERROR",
            details=f"Search query: {query}"
        )


class ValidationError(FriendlyError):
    """Error raised when data validation fails"""
    
    def __init__(self, *args, **kwargs):
        # Support both simple message and detailed validation error
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            # Simple message: ValidationError("message")
            super().__init__(
                message=args[0],
                error_code="VALIDATION_ERROR"
            )
        else:
            # Detailed validation: ValidationError(field, value, reason, suggestion)
            field = kwargs.get('field', args[0] if args else "unknown")
            value = kwargs.get('value', args[1] if len(args) > 1 else "")
            reason = kwargs.get('reason', args[2] if len(args) > 2 else "")
            suggestion = kwargs.get('suggestion', args[3] if len(args) > 3 else None)
            
            super().__init__(
                message=f"Validation failed: {field}",
                suggestion=suggestion or "Please check if input format is correct",
                error_code="VALIDATION_ERROR",
                details=f"Value: {value}\nReason: {reason}"
            )


class NetworkError(FriendlyError):
    """Error raised when network connection fails"""
    
    def __init__(self, url: str, suggestion: Optional[str] = None):
        super().__init__(
            message="Network connection failed",
            suggestion=suggestion or "Please check network connection or try again later",
            error_code="NETWORK_ERROR",
            details=f"Target URL: {url}"
        )


class DependencyError(FriendlyError):
    """Error raised when Python dependency is missing"""
    
    def __init__(self, dependency: str, suggestion: Optional[str] = None):
        super().__init__(
            message=f"Missing dependency: {dependency}",
            suggestion=suggestion or f"Please run 'pip install {dependency}' to install",
            error_code="DEPENDENCY_ERROR",
            details=f"Missing dependency: {dependency}"
        )


# ============================================================================
# Error Code Documentation
# ============================================================================

ERROR_CODE_DOCUMENTATION = {
    "INDEX_NOT_FOUND": {
        "description": "Memory index file not found",
        "cause": "First startup or index file deleted",
        "solution": "System will automatically rebuild index, please wait"
    },
    "WORKSPACE_NOT_FOUND": {
        "description": "OpenClaw workspace not found",
        "cause": "OpenClaw not installed or workspace path configuration error",
        "solution": "Install OpenClaw or manually specify workspace path"
    },
    "MEMORY_CORRUPTED": {
        "description": "Memory file corrupted",
        "cause": "Disk errors, unexpected power loss, or file modification",
        "solution": "System will auto-recover from backup. Check disk if issue persists"
    },
    "PERMISSION_DENIED": {
        "description": "Permission denied",
        "cause": "File permissions prevent access",
        "solution": "Use chmod to modify file permissions or run as correct user"
    },
    "CONFIGURATION_ERROR": {
        "description": "Configuration item invalid",
        "cause": "Configuration file syntax error or invalid value",
        "solution": "Check configuration file or refer to documentation"
    },
    "MEMORY_RETRIEVAL_ERROR": {
        "description": "Memory retrieval failed",
        "cause": "Search query too complex or memory file does not exist",
        "solution": "Simplify search query or check memory file"
    },
    "VALIDATION_ERROR": {
        "description": "Data validation failed",
        "cause": "Input data format incorrect",
        "solution": "Check input format and correct"
    },
    "NETWORK_ERROR": {
        "description": "Network connection failed",
        "cause": "Network unavailable or target server unreachable",
        "solution": "Check network connection or try again later"
    },
    "DEPENDENCY_ERROR": {
        "description": "Missing Python dependency",
        "cause": "Dependency package not installed or version incompatible",
        "solution": "Use pip to install missing dependency"
    }
}


def get_error_documentation(error_code: str) -> str:
    """Get detailed documentation for an error code"""
    if error_code not in ERROR_CODE_DOCUMENTATION:
        return f"Error code '{error_code}' has no documentation yet"
    
    doc = ERROR_CODE_DOCUMENTATION[error_code]
    output = f"Error Code: {error_code}\n"
    output += f"Description: {doc['description']}\n"
    output += f"Cause: {doc['cause']}\n"
    output += f"Solution: {doc['solution']}\n"
    
    return output


# ============================================================================
# Usage Examples
# ============================================================================

if __name__ == "__main__":
    # Example 1: Index not found
    try:
        raise IndexNotFoundError("~/.claw-mem/index/index_v0.9.0.pkl.gz")
    except FriendlyError as e:
        print(e)
        print()
    
    # Example 2: Workspace not found
    try:
        raise WorkspaceNotFoundError([
            "~/.openclaw/workspace",
            "~/.config/openclaw/workspace",
            "/current/dir"
        ])
    except FriendlyError as e:
        print(e)
        print()
    
    # Example 3: Get error documentation
    print(get_error_documentation("INDEX_NOT_FOUND"))
