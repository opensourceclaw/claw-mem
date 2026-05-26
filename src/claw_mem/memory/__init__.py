"""Cross-Agent Memory Sharing for claw-mem v4.0.

Provides standardized memory records, shared memory pool,
and cross-agent synchronization.
"""

from .agnostic import AgentAgnosticMemory, MemoryRecord
from .pool import MemoryPool
from .sync import CrossAgentSync

__all__ = [
    "AgentAgnosticMemory",
    "CrossAgentSync",
    "MemoryPool",
    "MemoryRecord",
]
