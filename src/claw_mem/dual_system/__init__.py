"""
claw-mem v3.3.0 — Dual System Memory Model

Hippocampus-Neocortex inspired dual memory system:
- HippocampalStore: Fast, short-term memory with LRU cache
- NeocorticalStore: Slow, long-term memory with concept abstraction
- ConsolidationLoop: Periodic memory consolidation

Usage::

    from claw_mem.dual_system import (
        HippocampalStore, NeocorticalStore, ConsolidationLoop,
        Memory, Concept, DualSystemConfig,
    )

    hippo = HippocampalStore()
    cortex = NeocorticalStore()
    loop = ConsolidationLoop(hippo, cortex)
    loop.start_background()
"""

from .config import DualSystemConfig
from .consolidation import ConsolidationLoop, ConsolidationResult
from .hippocampal import HippocampalStore, Memory
from .neocortical import Concept, NeocorticalStore

__all__ = [
    "DualSystemConfig",
    "HippocampalStore",
    "Memory",
    "NeocorticalStore",
    "Concept",
    "ConsolidationLoop",
    "ConsolidationResult",
]
