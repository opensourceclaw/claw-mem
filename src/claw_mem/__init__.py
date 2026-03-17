"""
claw-mem - Make OpenClaw Truly Remember

OpenClaw memory system built on evolutionary principles, fully compatible with existing OpenClaw memory formats.
"""

__version__ = "0.1.0-mvp"
__author__ = "claw-mem Team"

from .memory_manager import MemoryManager
from .storage.episodic import EpisodicStorage
from .storage.semantic import SemanticStorage
from .storage.procedural import ProceduralStorage

__all__ = [
    "MemoryManager",
    "EpisodicStorage",
    "SemanticStorage",
    "ProceduralStorage",
]
