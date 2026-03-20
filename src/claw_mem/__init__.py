"""
claw-mem - Make OpenClaw Truly Remember

OpenClaw memory system built on evolutionary principles, fully compatible with existing OpenClaw memory formats.

v0.8.0 Features:
- Friendly error messages (Chinese with suggestions)
- Index persistence for fast startup
- Lazy loading support
- Incremental index updates
"""

__version__ = "0.8.0"
__author__ = "Peter Cheng"

from .memory_manager import MemoryManager
from .storage.episodic import EpisodicStorage
from .storage.semantic import SemanticStorage
from .storage.procedural import ProceduralStorage
from .storage.index import InMemoryIndex, WorkingMemoryCache
from .retrieval.keyword import KeywordRetriever
from .config import ConfigDetector
from .importance import ImportanceScorer
from .memory_fix_plugin import MemoryFixPlugin
from .memory_decay import MemoryDecay
from .rule_extractor import RuleExtractor
from .errors import (
    FriendlyError,
    IndexNotFoundError,
    WorkspaceNotFoundError,
    MemoryCorruptedError,
    PermissionDeniedError,
    ConfigurationError,
    MemoryRetrievalError,
    ValidationError,
    NetworkError,
    DependencyError,
    get_error_documentation,
)

__all__ = [
    "MemoryManager",
    "EpisodicStorage",
    "SemanticStorage",
    "ProceduralStorage",
    "InMemoryIndex",
    "WorkingMemoryCache",
    "KeywordRetriever",
    "ConfigDetector",
    "ImportanceScorer",
    "MemoryFixPlugin",
    "MemoryDecay",
    "RuleExtractor",
    # Error classes
    "FriendlyError",
    "IndexNotFoundError",
    "WorkspaceNotFoundError",
    "MemoryCorruptedError",
    "PermissionDeniedError",
    "ConfigurationError",
    "MemoryRetrievalError",
    "ValidationError",
    "NetworkError",
    "DependencyError",
    "get_error_documentation",
]
