"""
claw-mem - Make OpenClaw Truly Remember

OpenClaw memory system built on evolutionary principles, fully compatible with existing OpenClaw memory formats.

v0.7.0 Features:
- Index persistence for fast startup
- Lazy loading support
- Incremental index updates
"""

__version__ = "0.7.0"
__author__ = "Peter Cheng"

from .memory_manager import MemoryManager
from .storage.episodic import EpisodicStorage
from .storage.semantic import SemanticStorage
from .storage.procedural import ProceduralStorage
from .storage.index import InMemoryIndex, WorkingMemoryCache

__all__ = [
    "MemoryManager",
    "EpisodicStorage",
    "SemanticStorage",
    "ProceduralStorage",
    "InMemoryIndex",
    "WorkingMemoryCache",
]
